"""
URL configuration for OpenWallets project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path
from ow import views

urlpatterns = [
    path('', views.main_page, name="main_page"),
    path('members/', views.member_list, name="member_list") ,
    path('members/<str:member_id>/', views.member_info, name='member_info'),
    path('api/', views.api_page, name="api_page") ,
    path('guide/', views.guide_page, name="guide_page") ,
]