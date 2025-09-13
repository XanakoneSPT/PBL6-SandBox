from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import UploadedFile, AnalysisResult
from .vm_manager import get_vm, is_vm_ready
import threading
import time
import logging
from django.db import transaction
from django.conf import settings


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

            # Start background task to analyze file using VM
            threading.Thread(target=_analyze_file, args=(uf.id,), daemon=True).start()
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


def vm_status_api(request: HttpRequest) -> JsonResponse:
    """API endpoint to check VM status for debugging."""
    try:
        vm = get_vm()
        if vm:
            vm_info = vm.get_vm_info()
            return JsonResponse({
                'vm_available': True,
                'vm_ready': is_vm_ready(),
                'vm_status': vm_info.get('status', 'unknown'),
                'vm_path': vm_info.get('vm_path', ''),
                'base_snapshot': vm_info.get('base_snapshot', ''),
            })
        else:
            return JsonResponse({
                'vm_available': False,
                'vm_ready': False,
                'error': 'VM instance not available'
            })
    except Exception as e:
        return JsonResponse({
            'vm_available': False,
            'vm_ready': False,
            'error': str(e)
        })


def _analyze_file(uploaded_file_id: int) -> None:
    """
    Analyze uploaded file using the pre-started VMware VM.
    This runs in a background thread to avoid blocking the web request.
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Get the uploaded file
        uf = UploadedFile.objects.get(id=uploaded_file_id)
        
        # Check if VM is ready
        if not is_vm_ready():
            raise Exception("VM is not ready for analysis")
        
        # Get the VM instance
        vm = get_vm()
        if not vm:
            raise Exception("VM instance not available")
        
        # Update progress: Starting analysis
        _update_progress(uploaded_file_id, 10, "Starting file analysis...")
        
        # Copy file to VM
        _update_progress(uploaded_file_id, 20, "Copying file to VM...")
        vm_file_path = vm.copy_to_vm(str(uf.file.path))
        
        # Detect file type and prepare for analysis
        _update_progress(uploaded_file_id, 40, "Analyzing file type...")
        interpreter, ext, needs_compilation = vm.detect_language(vm_file_path)
        
        if not interpreter:
            raise Exception(f"Unsupported file type: {ext}")
        
        # Run strace analysis for system call monitoring
        _update_progress(uploaded_file_id, 60, "Running system call analysis...")
        log_file = f"analysis_log_{uploaded_file_id}.txt"
        strace_log = vm.analyze_with_strace(vm_file_path, log_file)
        
        # Execute the file if it's executable
        if ext in ['.py', '.js', '.sh', '.rb', '.pl', '.php']:
            _update_progress(uploaded_file_id, 80, "Executing file in sandbox...")
            try:
                vm.execute_code(vm_file_path)
                execution_result = "File executed successfully in sandbox."
            except Exception as e:
                execution_result = f"File execution failed: {str(e)}"
        else:
            execution_result = "File type does not support direct execution."
        
        # Copy analysis results back
        _update_progress(uploaded_file_id, 90, "Retrieving analysis results...")
        
        # Get the strace log if it was created
        analysis_output = f"File Analysis Results:\n"
        analysis_output += f"File Type: {ext}\n"
        analysis_output += f"Interpreter: {interpreter}\n"
        analysis_output += f"Needs Compilation: {needs_compilation}\n"
        analysis_output += f"Execution Result: {execution_result}\n"
        
        if strace_log:
            # Copy the log file to shared folder
            log_dest = settings.SHARED_FOLDERS['FROM_VM'] / f"strace_log_{uploaded_file_id}.txt"
            vm.get_log_file(strace_log, str(log_dest))
            analysis_output += f"\nSystem call log saved to: {log_dest}\n"
        
        # Mark as completed
        _update_progress(uploaded_file_id, 100, "Analysis completed successfully", analysis_output, 'done')
        
        logger.info(f"File analysis completed for file ID: {uploaded_file_id}")
        
    except Exception as e:
        logger.error(f"File analysis failed for file ID {uploaded_file_id}: {e}")
        _update_progress(uploaded_file_id, 0, f"Analysis failed: {str(e)}", status='error')


def _update_progress(uploaded_file_id: int, progress: int, message: str, output_text: str = None, status: str = None) -> None:
    """
    Update the analysis progress in the database.
    """
    try:
        with transaction.atomic():
            res = AnalysisResult.objects.select_for_update().get(uploaded_file_id=uploaded_file_id)
            res.progress = progress
            if output_text:
                res.output_text = output_text
            if status:
                res.status = status
            else:
                res.status = 'processing'
            res.save(update_fields=['progress', 'status', 'output_text', 'updated_at'])
    except AnalysisResult.DoesNotExist:
        logging.warning(f"AnalysisResult not found for file ID: {uploaded_file_id}")
    except Exception as e:
        logging.error(f"Failed to update progress for file ID {uploaded_file_id}: {e}")
