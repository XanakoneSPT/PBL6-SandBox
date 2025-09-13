from django.db import models


class UploadedFile(models.Model):
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.original_name


class AnalysisResult(models.Model):
    uploaded_file = models.OneToOneField(UploadedFile, on_delete=models.CASCADE, related_name='result')
    status = models.CharField(max_length=32, default='pending')  # pending, processing, done, error
    progress = models.PositiveSmallIntegerField(default=0)  # 0-100
    output_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Result for {self.uploaded_file.original_name} ({self.status})"