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
from rest_framework import permissions
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

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
    path('login/',  views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/auth/', views.UserViewSet.as_view({'post': 'create'}), name='user-register'),
    path('users/profile/', views.UserViewSet.as_view({'put': 'profile'}), name='user-profile'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
]