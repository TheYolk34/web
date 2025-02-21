from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
from django.http import Http404, HttpResponse, JsonResponse
from .models import Illness, Drug, DrugIllness
from .serializers import *
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views import View
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from app.permissions import *
import redis
import uuid
from django.http import JsonResponse
from django.middleware.csrf import get_token
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
from django.http import Http404, HttpResponse, JsonResponse
from .models import Illness, Drug, DrugIllness
from .serializers import *
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views import View
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from app.permissions import *
import redis
import uuid
from django.http import JsonResponse
from django.middleware.csrf import get_token
from .services.qr_generate import generate_drug_qr



def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})

session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes        
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator

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
        user = request.user
        draft_drug_id = None
        count = 0
        if user.is_authenticated:
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
    
    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
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
    
    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
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

    @swagger_auto_schema(request_body=serializer_class)
    def add_to_draft(self, request, pk):
        user = request.user
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


    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
    def put(self, request, pk, format=None):
        illness = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(illness, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_permission_classes([IsManager])
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
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user

        # Получаем фильтры из запросов
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')
        if user.is_authenticated:
            if user.is_staff:
                drugs = self.model_class.objects.all()
            else:
                drugs = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])
        else:
            return Response({"error": "Вы не авторизованы"}, status=401)

        if date_from:
            drugs = drugs.filter(created_at__gte=date_from)
        if date_to:
            drugs = drugs.filter(created_at__lte=date_to)
        if status:
            drugs = drugs.filter(status=status)

        # Сериализуем данные
        serialized_drugs = [
        {
            **self.serializer_class(drug, exclude_illnesses=True).data,
            'creator': drug.creator.email,
            'moderator': drug.moderator.email if drug.moderator else None
        }
        for drug in drugs
        ]

        return Response(serialized_drugs)

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsAdmin, IsManager])
    def put(self, request, format=None):
        user = request.user
        required_fields = ['name']
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
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        drug = get_object_or_404(self.model_class, pk=pk)
        ssid = request.COOKIES.get("session_id")
        
        # Проверка на наличие сессии и получение пользователя
        if ssid and session_storage.exists(ssid):
            email = session_storage.get(ssid).decode("utf-8")
            print(f"Email found in session: {email}")
            request.user = CustomUser.objects.get(email=email)
        else:
            print("No valid session found.")
            request.user = None
        
        # Если пользователь является сотрудником (isStaff = true), разрешаем доступ к любому сражению
        if request.user and request.user.is_staff and drug.status != 'dr':
            # Сотрудники могут видеть все сражения
            serializer = self.serializer_class(drug, context={'is_drug': True})
            data = serializer.data
            data['creator'] = drug.creator.email
            if drug.moderator:
                data['moderator'] = drug.moderator.email
            return Response(data)

    
    def put(self, request, pk, format=None):
        drug = get_object_or_404(self.model_class, pk=pk)
        user = request.user
        print(1)

        if 'status' in request.data:
            status_value = request.data['status']
            
            if status_value == 'c':
                drug_illnesses = DrugIllness.objects.filter(drug=drug)
                drug.qr = generate_drug_qr(drug, drug_illnesses)
                drug.save()

                print(drug.qr)

            if status_value in ['del', 'f']:
                print(3)
                if drug.creator == user:
                    updated_data = request.data.copy()
                    print(4)

                    if status_value == 'f':
                        print(5)
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

    @swagger_auto_schema(request_body=serializer_class)
    def put_creator(self, request, pk):
        drug = get_object_or_404(self.model_class, pk=pk)
        ssid = request.COOKIES.get("session_id")
        if ssid and session_storage.exists(ssid):
            email = session_storage.get(ssid).decode("utf-8")
            print(f"Email found in session: {email}")
            request.user = CustomUser.objects.get(email=email)
        else:
            print("No valid session found.")
            request.user = None
        user = request.user
        if user == drug.creator:

            if 'status' in request.data and request.data['status'] == 'f':
                drug.formed_at = timezone.now()
                updated_data = request.data.copy()

                serializer = self.serializer_class(drug, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"error": "Создатель может только формировать заявку."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Отказано в доступе"}, status=status.HTTP_403_FORBIDDEN)        

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
    def put_moderator(self, request, pk):
        drug = get_object_or_404(self.model_class, pk=pk)
        user = request.user
        
        if 'status' in request.data:
            status_value = request.data['status']

            # Модератор может завершить ('c') или отклонить ('r') заявку
            if status_value in ['c', 'r']:
                if drug.status != 'f':
                    return Response({"error": "Заявка должна быть сначала сформирована."}, status=status.HTTP_403_FORBIDDEN)

                if status_value == 'c':
                    drug.completed_at = timezone.now()
                    updated_data = request.data.copy()

                elif status_value == 'r':
                    drug.completed_at = timezone.now()
                    updated_data = request.data.copy()

                serializer = self.serializer_class(drug, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save(moderator=user)
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Модератор может только завершить или отклонить заявку."}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=serializer_class)
    def put_edit(self, request, pk):
        drug = get_object_or_404(self.model_class, pk=pk)

        serializer = self.serializer_class(drug, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
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

    @swagger_auto_schema(request_body=serializer_class)
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

# View для User (пользователей)
class UserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    # def get_permissions(self):
    #     # Удаляем ненужные проверки, чтобы любой пользователь мог обновить свой профиль
    #     if self.action == 'create':
    #         return [AllowAny()]
    #     return [IsAuthenticated()]

    def get_permissions(self):
        if self.action in ['create', 'profile']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def create(self, request):
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            self.model_class.objects.create_user(
                email=serializer.data['email'],
                password=serializer.data['password'],
                is_superuser=serializer.data['is_superuser'],
                is_staff=serializer.data['is_staff']
            )
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # Обновление данных профиля пользователя
    @action(detail=False, methods=['put'], permission_classes=[AllowAny])
    def profile(self, request, format=None):
        user = request.user
        print(user)
        if not user.is_authenticated:
            return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)

        old_email = user.email
        data = request.data

        if 'password' in data and data['password']:
            user.set_password(data['password'])
            user.save()
            del data['password']

        serializer = self.serializer_class(user, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()

            new_email = serializer.data.get('email')
            if new_email and old_email != new_email:
                ssid = request.COOKIES.get("session_id")
                if ssid:
                    session_storage.delete(ssid)
                    session_storage.set(ssid, new_email, ex=settings.SESSION_COOKIE_AGE)

            return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@authentication_classes([])
@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['Post'])
@csrf_exempt
@permission_classes([AllowAny])
def login_view(request):
    username = request.data["email"] 
    password = request.data["password"]

    user = authenticate(request, email=username, password=password)
    if user is not None:
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)
        response = JsonResponse({"status": "ok", "username": username, "is_staff": user.is_staff})
        response.set_cookie("session_id", random_key)
        return response
    else:
        return JsonResponse({"status": "error", "error": "login failed"})

def logout_view(request):
    session_id = request.COOKIES.get("session_id")

    if session_id:
        session_storage.delete(session_id)
        response = HttpResponse("{'status': 'ok'}")
        response.delete_cookie("session_id")
        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'no session found'}")

@swagger_auto_schema(method='get')
@api_view(["GET"])
@csrf_exempt
def check_session(request):
    session_id = request.COOKIES.get("session_id")
    
    if session_id:
        username = session_storage.get(session_id)
        if username:
            if isinstance(username, bytes):
                username = username.decode('utf-8')
            user = CustomUser.objects.get(email=username)
            return JsonResponse({"status": "ok", "username": username, "is_staff": user.is_staff})
    
    return JsonResponse({"status": "error", "message": "Invalid session"})