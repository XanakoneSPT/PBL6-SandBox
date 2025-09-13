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


def analysis_files_api(request: HttpRequest, file_id: int) -> JsonResponse:
    """API endpoint to list analysis files for a specific upload."""
    try:
        from django.conf import settings
        import os
        
        from_vm_folder = settings.SHARED_FOLDERS['FROM_VM']
        analysis_files = []
        
        # Look for files related to this analysis
        if os.path.exists(from_vm_folder):
            for filename in os.listdir(from_vm_folder):
                if str(file_id) in filename:
                    file_path = os.path.join(from_vm_folder, filename)
                    file_size = os.path.getsize(file_path)
                    analysis_files.append({
                        'filename': filename,
                        'path': str(file_path),
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2)
                    })
        
        return JsonResponse({
            'file_id': file_id,
            'analysis_files': analysis_files,
            'count': len(analysis_files)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'analysis_files': [],
            'count': 0
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
        
        # Check if it's a document file (non-executable)
        is_document = ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']
        
        # Run appropriate analysis based on file type
        strace_log = None
        strace_result = "Strace analysis skipped"
        execution_result = "File type does not support direct execution."
        document_log = None
        document_result = "Document analysis skipped"
        
        if is_document:
            # Document analysis for PDFs and other documents
            try:
                _update_progress(uploaded_file_id, 60, "Running document analysis...")
                log_file = f"document_analysis_{uploaded_file_id}.txt"
                document_log = vm.analyze_document(vm_file_path, log_file)
                document_result = "Document analysis completed successfully"
            except Exception as e:
                logger.warning(f"Document analysis failed for file {uploaded_file_id}: {e}")
                document_result = f"Document analysis failed: {str(e)}"
        else:
            # Code analysis for executable files
            # Run strace analysis for system call monitoring (optional)
            try:
                _update_progress(uploaded_file_id, 60, "Running system call analysis...")
                log_file = f"analysis_log_{uploaded_file_id}.txt"
                strace_log = vm.analyze_with_strace(vm_file_path, log_file)
                strace_result = "Strace analysis completed successfully"
            except Exception as e:
                logger.warning(f"Strace analysis failed for file {uploaded_file_id}: {e}")
                strace_result = f"Strace analysis failed: {str(e)}"
            
            # Execute the file if it's executable
            if ext in ['.py', '.js', '.sh', '.rb', '.pl', '.php']:
                _update_progress(uploaded_file_id, 80, "Executing file in sandbox...")
                try:
                    vm.execute_code(vm_file_path)
                    execution_result = "File executed successfully in sandbox."
                except Exception as e:
                    execution_result = f"File execution failed: {str(e)}"
                    logger.warning(f"File execution failed for {uploaded_file_id}: {e}")
        
        # Copy analysis results back
        _update_progress(uploaded_file_id, 90, "Retrieving analysis results...")
        
        # Get the analysis logs if they were created
        analysis_output = f"File Analysis Results:\n"
        analysis_output += f"File Type: {ext}\n"
        analysis_output += f"Interpreter: {interpreter}\n"
        analysis_output += f"Needs Compilation: {needs_compilation}\n"
        analysis_output += f"Execution Result: {execution_result}\n"
        analysis_output += f"Strace Analysis: {strace_result}\n"
        analysis_output += f"Document Analysis: {document_result}\n"
        
        # Copy analysis files from VM to shared folder
        analysis_files = []
        
        if strace_log:
            # Copy the strace log file to shared folder
            log_dest = settings.SHARED_FOLDERS['FROM_VM'] / f"strace_log_{uploaded_file_id}.txt"
            try:
                vm.get_log_file(strace_log, str(log_dest))
                analysis_files.append(str(log_dest))
                analysis_output += f"\nSystem call log saved to: {log_dest}\n"
            except Exception as e:
                logger.warning(f"Failed to copy strace log: {e}")
                analysis_output += f"\nSystem call log generation failed: {str(e)}\n"
        
        if document_log:
            # Copy the document analysis log file to shared folder
            log_dest = settings.SHARED_FOLDERS['FROM_VM'] / f"document_analysis_{uploaded_file_id}.txt"
            try:
                vm.get_log_file(document_log, str(log_dest))
                analysis_files.append(str(log_dest))
                analysis_output += f"\nDocument analysis log saved to: {log_dest}\n"
            except Exception as e:
                logger.warning(f"Failed to copy document analysis log: {e}")
                analysis_output += f"\nDocument analysis log generation failed: {str(e)}\n"
        
        # Copy any other analysis files that might have been generated
        try:
            # Look for any additional log files in the VM's base directory
            vm_base_dir = str(vm.base_dir)
            additional_logs = [
                f"analysis_log_{uploaded_file_id}.txt",
                f"execution_log_{uploaded_file_id}.txt",
                f"error_log_{uploaded_file_id}.txt"
            ]
            
            for log_name in additional_logs:
                try:
                    vm_log_path = f"{vm_base_dir}/{log_name}"
                    local_dest = settings.SHARED_FOLDERS['FROM_VM'] / log_name
                    vm.get_log_file(vm_log_path, str(local_dest))
                    analysis_files.append(str(local_dest))
                    analysis_output += f"\nAdditional log saved to: {local_dest}\n"
                except:
                    # File doesn't exist, continue
                    pass
                    
        except Exception as e:
            logger.warning(f"Failed to copy additional analysis files: {e}")
        
        # Add summary of all analysis files
        if analysis_files:
            analysis_output += f"\nAnalysis files saved to FROM_VM folder:\n"
            for file_path in analysis_files:
                analysis_output += f"- {file_path}\n"
        
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
