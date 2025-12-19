from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    original_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='uploads/', max_length=500) # User requested 'file_path'
    file_size = models.BigIntegerField(null=True, blank=True)
    md5_hash = models.CharField(max_length=32, blank=True)
    sha1_hash = models.CharField(max_length=40, blank=True)
    sha256_hash = models.CharField(max_length=64, blank=True)
    file_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'uploaded_files'

    def __str__(self) -> str:
        return self.original_name

class ResultAnalysis(models.Model):
    # One result per file, logic separated
    uploaded_file = models.OneToOneField(UploadedFile, on_delete=models.CASCADE, related_name='analysis_result')
    
    status = models.CharField(max_length=50, default='pending') # pending / completed / failed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # VM Analysis metadata (kept from original model for compatibility)
    interpreter = models.CharField(max_length=100, blank=True, null=True)
    vm_log_file_path = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'result_analysis'

    def __str__(self) -> str:
        return f"Analysis for {self.uploaded_file.original_name}"

class YaraAnalysis(models.Model):
    result_analysis = models.OneToOneField(ResultAnalysis, on_delete=models.CASCADE, related_name='yara_analysis')
    
    # Keeping rich data from original model, mapped to new structure
    matches = models.JSONField(default=list, blank=True) # Was yara_filtered_matches
    raw_matches = models.JSONField(default=list, blank=True) # Was yara_raw_matches
    error = models.TextField(blank=True, null=True) # Was yara_error

    class Meta:
        db_table = 'yara_analysis'

class BazaarAnalysis(models.Model):
    result_analysis = models.OneToOneField(ResultAnalysis, on_delete=models.CASCADE, related_name='bazaar_analysis')
    
    is_malicious = models.BooleanField(default=False)
    malware_info = models.JSONField(default=dict, blank=True, null=True)
    error = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'bazaar_analysis'

class LstmAnalysis(models.Model):
    result_analysis = models.OneToOneField(ResultAnalysis, on_delete=models.CASCADE, related_name='lstm_analysis')
    
    is_anomalous = models.BooleanField(default=False, null=True) # The specific field requested
    
    # Detailed stats from original model
    final_decision = models.CharField(max_length=50, blank=True, null=True)
    max_prob_anomaly = models.FloatField(null=True, blank=True)
    mean_prob_anomaly = models.FloatField(null=True, blank=True)
    num_windows = models.IntegerField(null=True, blank=True)
    
    error = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'lstm_analysis'