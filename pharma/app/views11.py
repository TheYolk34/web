from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
from django.http import Http404
from .models import Illness, Drug, DrugIllness
from .serializers import IllnessSerializer, DrugSerializer, DrugIllnessSerializer, UserSerializer
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.http import JsonResponse

class UserView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"message": "Hello from UserView"})


class UserSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                cls._instance = User.objects.get(id=2)
            except User.DoesNotExist:
                cls._instance = None
        return cls._instance

    @classmethod
    def clear_instance(cls, user):
        pass


def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        client.put_object('health-services', image_name, file_object, file_object.size)
        return f"http://localhost:9000/health-services/{image_name}"
    except Exception as e:
        return {"error": str(e)}


def add_pic(new_illness, pic):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )
    img_obj_name = f"{new_illness.id}.jpg"

    if not pic:
        return {"error": "Нет файла для изображения."}

    result = process_file_upload(pic, client, img_obj_name)

    if 'error' in result:
        return {"error": result['error']}

    return result


# View для Illness (услуг)
class IllnessList(APIView):
    model_class = Illness
    serializer_class = IllnessSerializer

    def get(self, request, format=None):
        illness_name = request.query_params.get('name')
        illnesses = self.model_class.objects.filter(status='a')
        if illness_name:
            illnesses = illnesses.filter(name__icontains=illness_name)
        user = UserSingleton.get_instance()
        draft_drug_id = None
        count = 0
        if user:
            draft_drug = Drug.objects.filter(creator=user, status='dr').first()
            if draft_drug:
                draft_drug_id = draft_drug.id
                count = DrugIllness.objects.filter(drug=draft_drug).count()

        serializer = self.serializer_class(illnesses, many=True, context={'is_list': True})
        response_data = {
            'illnesses': serializer.data,
            'draft_drug_id': draft_drug_id, 
            'count': count
        }
        return Response(response_data)

    def post(self, request, format=None):
        pic = request.FILES.get("photo")
        data = request.data.copy()
        data.pop('photo', None)
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            illness = serializer.save()
            if pic:
                pic_url = add_pic(illness, pic)
                if 'error' in pic_url:
                    return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)
                illness.photo = pic_url
                illness.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IllnessDetail(APIView):
    model_class = Illness
    serializer_class = IllnessSerializer

    def get(self, request, pk, format=None):
        illness = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(illness)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        illness = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(illness, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        illness = get_object_or_404(self.model_class, pk=pk)
        illness.status = 'd'  # Мягкое удаление
        illness.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для Drug (заявок)
class DrugList(APIView):
    model_class = Drug
    serializer_class = DrugSerializer

    def get(self, request, format=None):
        user = UserSingleton.get_instance()

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')

        drugs = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])

        if date_from:
            drugs = drugs.filter(created_at__gte=date_from)
        if date_to:
            drugs = drugs.filter(created_at__lte=date_to)

        if status:
            drugs = drugs.filter(status=status)

        serialized_drugs = [
            {
                **self.serializer_class(drug, exclude_illnesses=True).data,
                'creator': drug.creator.username
            }
            for drug in drugs
        ]

        return Response(serialized_drugs)

    def post(self, request, format=None):
        user = UserSingleton.get_instance()
        if not user:
            return Response({'error': 'Необходима авторизация.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            drug = serializer.save(creator=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DrugDetail(APIView):
    model_class = Drug
    serializer_class = DrugSerializer

    def get(self, request, pk, format=None):
        drug = get_object_or_404(self.model_class, pk=pk)
        if drug.status == 'del':
            return Response({"detail": "Эта заявка удалена и недоступна для просмотра."}, status=403)
        serializer = self.serializer_class(drug, context={'is_drug': True})
        data = serializer.data
        data['creator'] = drug.creator.username
        return Response(data)

    def delete(self, request, pk, format=None):
        drug = get_object_or_404(self.model_class, pk=pk)
        drug.status = 'del'  # Мягкое удаление
        drug.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для DrugIllness (связь много ко многим)
class DrugIllnessDetail(APIView):
    model_class = DrugIllness
    serializer_class = DrugIllnessSerializer

    def put(self, request, drug_id, illness_id, format=None):
        drug = get_object_or_404(Drug, pk=drug_id)
        drug_illness = get_object_or_404(self.model_class, drug=drug, illness__id=illness_id)
        
        serializer = self.serializer_class(drug_illness, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, drug_id, illness_id, format=None):
        drug = get_object_or_404(Drug, pk=drug_id)
        drug_illness = get_object_or_404(self.model_class, drug=drug, illness__id=illness_id)
        drug_illness.delete()
        return Response({"message": "Услуга успешно удалена из заявки"}, status=status.HTTP_204_NO_CONTENT)
