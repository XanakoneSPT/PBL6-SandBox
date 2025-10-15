from django.urls import path
from . import views

urlpatterns = [
    path("stream/", views.stream_sandbox, name="stream_sandbox"),
    path('upload_file/', views.upload_file, name='upload_file'),
]
