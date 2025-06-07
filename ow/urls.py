from django.urls import path
from . import views

# url 페이지
urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('members/', views.member_list, name="member_list") ,
    path('members/<str:member_id>/', views.member_info, name='member_info'),
    path('api/', views.api_page, name="api_page") ,
    path('guide/', views.guide_page, name="guide_page") ,
]