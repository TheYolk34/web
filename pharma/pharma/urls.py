"""
URL configuration for navy_sea project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from app import views
from django.urls import path, include
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('illnesses/', views.IllnessList.as_view(), name='illness-list'),
    path('illnesses/<int:pk>/', views.IllnessDetail.as_view(), name='illness-detail'),
    path('illnesses/<int:pk>/image/', views.IllnessDetail.as_view(), name='illness-update-image'),
    path('illnesses/<int:pk>/draft/', views.IllnessDetail.as_view(), name='illness-add-to-draft'),
    path('drugs/', views.DrugList.as_view(), name='drug-list'),
    path('drugs/<int:pk>/edit/', views.DrugDetail.as_view(), name='drug-detail-edit'),
    path('drugs/<int:pk>/form/', views.DrugDetail.as_view(), name='drug-detail-form'),
    path('drugs/<int:pk>/complete/', views.DrugDetail.as_view(), name='drug-detail-complete'),
    path('drugs/<int:pk>/', views.DrugDetail.as_view(), name='drug-detail'),
    path('drugs/<int:drug_id>/illnesses/<int:illness_id>/', views.DrugIllnessDetail.as_view(), name='drug-illness-detail'),
    path('users/<str:action>/', views.UserView.as_view(), name='user-action'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
]