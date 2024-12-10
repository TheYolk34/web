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

class UserSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                cls._instance = User.objects.get(id=11)
            except User.DoesNotExist:
                cls._instance = None
        return cls._instance

    @classmethod
    def clear_instance(cls, user):
        pass


def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        client.put_object('pharma', image_name, file_object, file_object.size)
        return f"http://localhost:9000/pharma/{image_name}"
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

# View для Illness (болезни)
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
        data = request.data.copy()
        data['photo'] = None

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            illness = serializer.save() 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IllnessDetail(APIView):
    model_class = Illness
    serializer_class = IllnessSerializer

    def get(self, request, pk, format=None):
        illness = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(illness)
        return Response(serializer.data)
    
    def post(self, request, pk, format=None):
        if request.path.endswith('/image/'):
            return self.update_image(request, pk)
        elif request.path.endswith('/draft/'):
            return self.add_to_draft(request, pk)
        raise Http404

    def update_image(self, request, pk):
        illness = get_object_or_404(self.model_class, pk=pk)
        pic = request.FILES.get("photo")

        if not pic:
            return Response({"error": "Файл изображения не предоставлен."}, status=status.HTTP_400_BAD_REQUEST)

        if illness.photo:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            old_img_name = illness.photo.split('/')[-1]
            try:
                client.remove_object('pharma', old_img_name)
            except Exception as e:
                return Response({"error": f"Ошибка при удалении старого изображения: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pic_url = add_pic(illness, pic)
        if 'error' in pic_url:
            return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)

        illness.photo = pic_url
        illness.save()

        return Response({"message": "Изображение успешно обновлено.", "photo_url": pic_url}, status=status.HTTP_200_OK)

    def add_to_draft(self, request, pk):
        user = UserSingleton.get_instance()
        if not user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        illness = get_object_or_404(self.model_class, pk=pk)
        draft_drug = Drug.objects.filter(creator=user, status='dr').first()

        if not draft_drug:
            draft_drug = Drug.objects.create(
                creator=user,
                status='dr',
                created_at=timezone.now()
            )
            draft_drug.save()

        if DrugIllness.objects.filter(drug=draft_drug, illness=illness).exists():
            return Response(data={"error": "Лекарство уже добавлено в черновик."}, status=status.HTTP_400_BAD_REQUEST)

        DrugIllness.objects.create(drug=draft_drug, illness=illness)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk, format=None):
        illness = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(illness, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        illness = get_object_or_404(self.model_class, pk=pk)
        if illness.photo:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            image_name = illness.photo.split('/')[-1]
            try:
                client.remove_object('pharma', image_name)
            except Exception as e:
                return Response({"error": f"Ошибка при удалении изображения: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        illness.status = 'd'
        illness.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для Drug (заявки)
class DrugList(APIView):
    model_class = Drug
    serializer_class = DrugSerializer

    def get(self, request, format=None):
        user = UserSingleton.get_instance()

        # Получаем фильтры из запросов
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')

        # Фильтруем ужины по пользователю и статусам
        drugs = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])

        if date_from:
            drugs = drugs.filter(created_at__gte=date_from)
        if date_to:
            drugs = drugs.filter(created_at__lte=date_to)
        if status:
            drugs = drugs.filter(status=status)

        # Сериализуем данные
        serialized_drugs = [
            {**self.serializer_class(drug).data, 'creator': drug.creator.username, 'moderator': drug.moderator.username if drug.moderator else None}
            for drug in drugs
        ]

        return Response(serialized_drugs)

    def put(self, request, format=None):
        user = UserSingleton.get_instance()
        required_fields = ['table_number']
        for field in required_fields:
            if field not in request.data or request.data[field] is None:
                return Response({field: 'Это поле обязательно для заполнения.'}, status=status.HTTP_400_BAD_REQUEST)
            
        drug_id = request.data.get('id')
        if drug_id:
            drug = get_object_or_404(self.model_class, pk=drug_id)
            serializer = self.serializer_class(drug, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=user)
                return Response(serializer.data)
            
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
        serializer = self.serializer_class(drug)
        data = serializer.data
        data['creator'] = drug.creator.username
        if drug.moderator:
            data['moderator'] = drug.moderator.username 

        return Response(data)

    def put(self, request, pk, format=None):
        drug = get_object_or_404(self.model_class, pk=pk)
        user = UserSingleton.get_instance()

        if 'status' in request.data:
            status_value = request.data['status']

            if status_value in ['del', 'f']:
                if drug.creator == user:
                    updated_data = request.data.copy()

                    if status_value == 'f':
                        drug.formed_at = timezone.now()

                    serializer = self.serializer_class(drug, data=updated_data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response(serializer.data)
                else:
                    return Response({"error": "Отказано в доступе"}, status=status.HTTP_403_FORBIDDEN)
                
            if status_value not in ['c', 'r']:
                return Response({"error": "Неверный статус."}, status=status.HTTP_400_BAD_REQUEST)
            
            if drug.status != 'f':
                return Response({"error": "Заявка ещё не сформирована."}, status=status.HTTP_403_FORBIDDEN)

            updated_data = request.data.copy()
            drug.completed_at = timezone.now()
            
            serializer = self.serializer_class(drug, data=updated_data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=user)
                return Response(serializer.data)

        # Если статус не был передан, пробуем обновить остальные данные
        serializer = self.serializer_class(drug, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(moderator=user)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удаление заявки
    def delete(self, request, pk, format=None):
        drug = get_object_or_404(self.model_class, pk=pk)
        drug.status = 'del'  # Мягкое удаление
        drug.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    
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
        return Response({"message": "Болезнь успешно удалена из Лекарства"}, status=status.HTTP_204_NO_CONTENT)

class UserView(APIView):
    def post(self, request, action, format=None):
        if action == 'register':
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                user = User(
                    username=validated_data['username'],
                    email=validated_data['email']
                )
                user.set_password(request.data.get('password'))
                user.save()
                return Response({
                    'message': 'Регистрация прошла успешно'
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'login':
            username = request.data.get('username')
            password = request.data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                user_data = UserSerializer(user).data
                return Response({
                    'message': 'Аутентификация успешна',
                    'user': user_data
                }, status=200)
            
            return Response({'error': 'Неправильное имя пользователя или пароль'}, status=400)

        elif action == 'logout':
            return Response({'message': 'Вы вышли из системы'}, status=200)

        return Response({'error': 'Некорректное действие'}, status=400)

    # Обновление данных профиля пользователя
    def put(self, request, action, format=None):
        if action == 'profile':
            user = UserSingleton.get_instance()
            if user is None:
                return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
            
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Некорректное действие'}, status=status.HTTP_400_BAD_REQUEST)
