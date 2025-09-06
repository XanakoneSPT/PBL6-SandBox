from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload, name='upload'),
    path('result/<int:file_id>/', views.result_page, name='result'),
    path('api/progress/<int:file_id>/', views.progress_api, name='progress_api'),
]


