from rest_framework import serializers
from django.contrib.auth.models import User
from app.models import Illness, Drug, DrugIllness, CustomUser


class IllnessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Illness
        fields = ['id', 'name', 'description', 'spread', 'photo', 'status']

    def __init__(self, *args, **kwargs):
        # Получаем контекст из запроса
        super(IllnessSerializer, self).__init__(*args, **kwargs)
        context = self.context

        # Если это запрос списка, исключаем поле 'spread' и 'photo'
        if context.get('is_list', False):
            self.fields.pop('description')
            self.fields.pop('status')

    def get_fields(self):
        fields = super().get_fields()

        # Если это запрос с указанием активного состояния
        if self.context.get('is_active', False):
            return {
                'name': fields['name'],
                'status': fields['status']
            }

        return fields


class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = [
            'id', 'name', 'description', 'price', 'status', 'created_at', 
            'formed_at', 'completed_at', 'creator', 'moderator'
        ]

    def __init__(self, *args, **kwargs):
        # Получаем контекст из запроса
        exclude_dates = kwargs.pop('exclude_dates', False)
        super(DrugSerializer, self).__init__(*args, **kwargs)

        # Исключаем временные поля, если указан exclude_dates=True
        if exclude_dates:
            self.fields.pop('created_at', None)
            self.fields.pop('formed_at', None)
            self.fields.pop('completed_at', None)


class DrugIllnessSerializer(serializers.ModelSerializer):
    drug = DrugSerializer(read_only=True)
    illness = IllnessSerializer(read_only=True)

    class Meta:
        model = DrugIllness
        fields = ['drug', 'illness', 'trial']


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'is_staff', 'is_superuser']
 