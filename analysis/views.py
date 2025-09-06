from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import UploadedFile, AnalysisResult
import threading
import time
from django.db import transaction


def home(request: HttpRequest) -> HttpResponse:
    return redirect('upload')


@require_http_methods(["GET", "POST"])
def upload(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        if not request.FILES.get('file'):
            return render(request, 'upload.html', {'error': 'No file selected'})
        
        try:
            uploaded = request.FILES['file']
            
            # Check file size (100MB limit)
            if uploaded.size > 100 * 1024 * 1024:
                return render(request, 'upload.html', {'error': 'File too large. Maximum size is 100MB.'})
            
            uf = UploadedFile.objects.create(original_name=uploaded.name, file=uploaded)
            AnalysisResult.objects.create(uploaded_file=uf, status='processing', progress=5)

            # Start a simple background task to simulate processing and progress updates
            threading.Thread(target=_simulate_processing, args=(uf.id,), daemon=True).start()
            return redirect(reverse('result', kwargs={'file_id': uf.id}))
            
        except Exception as e:
            return render(request, 'upload.html', {'error': f'Upload failed: {str(e)}'})
    
    return render(request, 'upload.html')


def result_page(request: HttpRequest, file_id: int) -> HttpResponse:
    uf = get_object_or_404(UploadedFile, id=file_id)
    return render(request, 'result.html', {'file': uf})


def progress_api(request: HttpRequest, file_id: int) -> JsonResponse:
    res = get_object_or_404(AnalysisResult, uploaded_file_id=file_id)
    return JsonResponse({
        'status': res.status,
        'progress': res.progress,
        'output_text': res.output_text,
        'updated_at': res.updated_at.isoformat() if res.updated_at else None,
    })


def _simulate_processing(uploaded_file_id: int) -> None:
    # This is a demo-only background worker to show progress moving.
    # Replace with real processing (Celery/RQ) in production.
    try:
        for p in (10, 20, 35, 55, 75, 90, 100):
            time.sleep(1)
            with transaction.atomic():
                try:
                    res = AnalysisResult.objects.select_for_update().get(uploaded_file_id=uploaded_file_id)
                except AnalysisResult.DoesNotExist:
                    return
                if res.status in ('done', 'error'):
                    return
                res.progress = p
                if p >= 100:
                    res.status = 'done'
                    res.output_text = (res.output_text or '') + 'Processing completed successfully.'
                res.save(update_fields=['progress', 'status', 'output_text', 'updated_at'])
    except Exception as e:
        with transaction.atomic():
            try:
                res = AnalysisResult.objects.select_for_update().get(uploaded_file_id=uploaded_file_id)
            except AnalysisResult.DoesNotExist:
                return
            res.status = 'error'
            res.output_text = f'Error: {e}'
            res.save(update_fields=['status', 'output_text', 'updated_at'])
