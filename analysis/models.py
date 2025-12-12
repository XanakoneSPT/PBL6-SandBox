from django.db import models
from django.contrib.auth.models import User  #Django's built-in User model

# Create your models here.
class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='')
    file_size = models.BigIntegerField(null=True, blank=True)
    md5_hash = models.CharField(max_length=32, blank=True)
    sha1_hash = models.CharField(max_length=40, blank=True)
    sha256_hash = models.CharField(max_length=64, blank=True)
    file_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.original_name

class AnalysisResult(models.Model):
    uploaded_file = models.OneToOneField(UploadedFile, on_delete=models.CASCADE, related_name='analysis_result')
    
    # Status and timestamps
    status = models.CharField(max_length=32, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # YARA Results
    yara_filtered_matches = models.JSONField(default=list, blank=True)
    yara_raw_matches = models.JSONField(default=list, blank=True)
    yara_error = models.TextField(blank=True, null=True)
    
    # Bazaar Results
    bazaar_success = models.BooleanField(default=False)
    bazaar_is_malicious = models.BooleanField(default=False)
    bazaar_malware_info = models.JSONField(default=dict, blank=True, null=True)
    bazaar_error = models.TextField(blank=True, null=True)
    
    # LSTM Results
    lstm_final_decision = models.CharField(max_length=50, blank=True, null=True)
    lstm_max_prob_anomaly = models.FloatField(null=True, blank=True)
    lstm_mean_prob_anomaly = models.FloatField(null=True, blank=True)
    lstm_num_windows = models.IntegerField(null=True, blank=True)
    lstm_error = models.TextField(blank=True, null=True)
    
    # VM Analysis
    interpreter = models.CharField(max_length=100, blank=True, null=True)
    vm_log_file_path = models.CharField(max_length=500, blank=True, null=True)
    
    def __str__(self) -> str:
        return f"AnalysisResult for {self.uploaded_file.original_name}"