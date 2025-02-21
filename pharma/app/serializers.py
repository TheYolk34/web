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

class DrugIllnessSerializer(serializers.ModelSerializer):
    illness = IllnessSerializer(read_only=True)

    class Meta:
        model = DrugIllness
        fields = ['illness', 'trial']

class DrugSerializer(serializers.ModelSerializer):
    illnesses = DrugIllnessSerializer(many=True, read_only=True, source='drugillness_set')

    class Meta:
        model = Drug
        fields = [
            'id', 'name', 'description', 'price', 'status', 'created_at', 
            'formed_at', 'completed_at', 'creator', 'moderator', 'illnesses', 'qr'
        ]

    def __init__(self, *args, **kwargs):
        # Получаем контекст из запроса
        exclude_illnesses = kwargs.pop('exclude_illnesses', False)
        super(DrugSerializer, self).__init__(*args, **kwargs)

                # Убираем поле 'illnesses' если exclude_illnesses=True
        if exclude_illnesses:
            self.fields.pop('illnesses', None)



class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'is_staff', 'is_superuser']
 