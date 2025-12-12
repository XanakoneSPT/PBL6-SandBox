from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload, name='home'),
    path('result/<int:file_id>/', views.result_page, name='result'),
    path('history/', views.history, name='history'),

    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # api endpoint
    path('api/progress/<int:file_id>/', views.api_progress, name='api_progress'),
    path('api/vm-logs/<int:file_id>/', views.api_vm_logs, name='api_vm_logs'),
    path('api/vm-logs/<int:file_id>/<str:filename>/', views.api_vm_logs, name='api_vm_logs_detail'),
    path('api/download-log/<int:file_id>/<str:filename>/', views.api_download_log, name='api_download_log'),
    path('api/download-report/<int:file_id>/', views.api_download_report, name='api_download_report'),
]