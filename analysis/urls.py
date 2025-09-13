from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload, name='upload'),
    path('result/<int:file_id>/', views.result_page, name='result'),
    path('api/progress/<int:file_id>/', views.progress_api, name='progress_api'),
    path('api/vm-status/', views.vm_status_api, name='vm_status_api'),
    path('api/analysis-files/<int:file_id>/', views.analysis_files_api, name='analysis_files_api'),
]


