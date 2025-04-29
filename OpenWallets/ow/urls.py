from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('members/', views.member_list, name="member_list") ,
    path('members/<int:member_id>/', views.member_info, name='member_info'),
]