from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import FileResponse, HttpRequest, HttpResponse, JsonResponse, Http404, response
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from unittest import result
from datetime import datetime

import threading

from .models import UploadedFile, ResultAnalysis, YaraAnalysis, BazaarAnalysis, LstmAnalysis

from utils.hashes_cal import calculate_file_hashes
from utils.getFileType import get_file_type
from utils.analysisFunc import _analyze_file
from utils.progress import get_progress
from utils.report_gen import generate_pdf
from utils.clean_folder import cleanup_uploaded_file


# Create your views here.
@require_http_methods(['GET', 'POST'])
def upload(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':

        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            return render(request, 'upload.html',{'error': 'Please select a file to upload.'})

        try:
            max_size = 100*1024*1024 #100MB
            if uploaded_file.size > max_size:
                return render(request, 'upload.html', {'error': 'File too large. Maximum 100MB.'})

            uf = UploadedFile.objects.create(
                original_name=uploaded_file.name, 
                file_path=uploaded_file, # Updated: file -> file_path
                user=request.user if request.user.is_authenticated else None)

            try:
                # Updated: file.path -> file_path.path
                file_path = uf.file_path.path
                md5_hash, sha1_hash, sha256_hash = calculate_file_hashes(file_path)
                file_type = get_file_type(file_path)

                # update the uploaded file with calculated values
                uf.file_size = uploaded_file.size
                uf.md5_hash = md5_hash
                uf.sha1_hash = sha1_hash
                uf.sha256_hash = sha256_hash
                uf.file_type = file_type
                uf.save()
            except Exception as e:
                return render(request, 'upload.html', {'error': 'Calculate hash failed!'})

            #start background task to analyze file using VM
            threading.Thread(target=_analyze_file, args=(uf.id,), daemon=True).start()
            return redirect(reverse('result', kwargs={'file_id': uf.id}))
        except:
            return render(request, 'upload.html', {'error': 'Upload fail!'})

    return render(request, 'upload.html')

@login_required
def history(request: HttpRequest) -> HttpResponse:
    try:
        ufs = UploadedFile.objects.filter(
            user=request.user
        ).select_related('analysis_result').order_by('-created_at')
        
        files_with_status = []
        for uf in ufs:
            try:
                status = uf.analysis_result.status
            except ResultAnalysis.DoesNotExist: # Updated Exception
                status = 'pending'
            except Exception:
                status = 'pending'
            
            files_with_status.append({
                'file': uf,
                'status': status,
                'has_result': hasattr(uf, 'analysis_result')
            })
        
        return render(request, 'history.html', {'files': files_with_status})
    except Exception as e:
        # Log error but still return empty history
        print(f"Error loading history: {e}")
        return render(request, 'history.html', {'files': []})

@login_required
def delete_history(request: HttpRequest, file_id: int) -> HttpResponse:
    if request.method == 'POST':
        uf = get_object_or_404(UploadedFile, id=file_id)
        
        # Security check: ensure user owns the file
        if uf.user != request.user:
             from django.http import HttpResponseForbidden
             return HttpResponseForbidden("You don't have permission to delete this file.")
        
        try:
            # Cleanup physical files
            from utils.clean_folder import delete_analysis_data
            delete_analysis_data(uf)
            
            # Delete from database
            uf.delete()
        except Exception as e:
            print(f"Error deleting file {file_id}: {e}")
            # Optionally add a flash message here
            
    return redirect('history')


def result_page(request: HttpRequest, file_id: int) -> HttpResponse:
    uf = get_object_or_404(UploadedFile, id=file_id)
    
    # Security: If file has a user, only that user can view it
    # If file has no user (public), anyone can view it
    if uf.user is not None and request.user != uf.user:
        from django.contrib.auth.decorators import login_required
        if not request.user.is_authenticated:
            # Redirect to login
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.path)
        else:
            # User is logged in but not the owner
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You don't have permission to view this file.")
    
    return render(request, 'result.html', {'file': uf})

@login_required
def profile_view(request):
    from django.contrib import messages
    # Use update_session_auth_hash to keep user logged in after password change
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        username = request.POST.get('username')
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Incorrect current password.')
            return redirect('profile')
            
        # Update username
        if username and username != request.user.username:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken.')
                return redirect('profile')
            request.user.username = username
            
        # Update password
        if new_password:
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                return redirect('profile')
            request.user.set_password(new_password)
            update_session_auth_hash(request, request.user) # Important!
            
        request.user.save()
        messages.success(request, 'Account updated successfully.')
        return redirect('profile')
        
    return render(request, 'profile.html')

def register_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Auto-login after registration
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form})

def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    print('You have been logged out successfully.')
    return redirect('home')

#################
# API Endpoint
#################

@require_http_methods(['GET'])
def api_progress(request: HttpRequest, file_id: int) -> JsonResponse:
    uf = get_object_or_404(UploadedFile, id=file_id)
    
    # Check if JSON progress file exists
    from pathlib import Path
    from django.conf import settings
    progress_file = settings.SHARED_FOLDERS['TO_VM'] / 'progress' / f"{file_id}.json"
    json_file_exists = progress_file.exists()
    
    # Get progress from JSON (only progress/status)
    progress_data = get_progress(file_id)
    
    # Get results from database
    try:
        analysis_result = uf.analysis_result
        
        # If JSON file doesn't exist, use database status and set progress to 100% if done
        if not json_file_exists:
            progress_data['status'] = analysis_result.status
            if analysis_result.status in ['done', 'error']:
                progress_data['progress'] = 100
        # If JSON exists but status is pending and DB has different status, use DB status
        elif progress_data.get('status') == 'pending' and analysis_result.status != 'pending':
            progress_data['status'] = analysis_result.status
            if analysis_result.status in ['done', 'error']:
                progress_data['progress'] = 100
        
        # Helper to safely get child model or dict
        def get_child_data(model_attr, default_dict=None):
            if default_dict is None: default_dict = {}
            if hasattr(analysis_result, model_attr):
                return getattr(analysis_result, model_attr)
            return type('Dummy', (), default_dict)

        yara = get_child_data('yara_analysis')
        bazaar = get_child_data('bazaar_analysis')
        lstm = get_child_data('lstm_analysis')

        progress_data.update({
            'yara_filtered_matches': getattr(yara, 'matches', []), # Renamed field
            'yara_raw_matches': getattr(yara, 'raw_matches', []), # Renamed field
            'yara_error': getattr(yara, 'error', None), # Renamed field
            
            'bazaar_success': not getattr(bazaar, 'error', True), # Infer success
            'bazaar_is_malicious': getattr(bazaar, 'is_malicious', False),
            'bazaar_malware_info': getattr(bazaar, 'malware_info', {}),
            'bazaar_error': getattr(bazaar, 'error', None),
            
            'lstm_final_decision': getattr(lstm, 'final_decision', None),
            'lstm_max_prob_anomaly': getattr(lstm, 'max_prob_anomaly', None),
            'lstm_mean_prob_anomaly': getattr(lstm, 'mean_prob_anomaly', None),
            'lstm_num_windows': getattr(lstm, 'num_windows', None),
            'lstm_error': getattr(lstm, 'error', None),
            
            'interpreter': analysis_result.interpreter,
        })
    except ResultAnalysis.DoesNotExist:
        # No analysis result yet, keep JSON progress data
        pass
    
    # Add file info
    file_info = {
        'file_size': uf.file_size,
        'file_type': uf.file_type,
        'md5_hash': uf.md5_hash,
        'sha1_hash': uf.sha1_hash,
        'sha256_hash': uf.sha256_hash,
    }
    progress_data['file_info'] = file_info
    return JsonResponse(progress_data)

@require_http_methods(['GET'])
def api_vm_logs(request: HttpRequest, file_id: int, filename: str = None) -> JsonResponse:
    uf = get_object_or_404(UploadedFile, id=file_id)

    from_vm_dir = settings.SHARED_FOLDERS['FROM_VM']

    if filename:
        if not filename.startswith(f"{file_id}_"):
            return JsonResponse({'error': 'Invalid log file'}, status=403)

        log_path = from_vm_dir / filename

        if not log_path.exists() or not log_path.is_file():
            return JsonResponse({'error': 'Log file not found'}, status=404)

        try:
            with open(log_path, 'r', encoding="utf-8", errors='ignore') as f:
                content = f.read()

            return JsonResponse({
                'filename': filename,
                'content': content,
                'size': log_path.stat().st_size
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # Otherwise, return list of log files
    log_files = []
    pattern = f"{file_id}_*_analysis.log"
    
    try:
        for log_file in from_vm_dir.glob(pattern):
            if log_file.is_file():
                log_files.append({
                    'filename': log_file.name,
                    'size': log_file.stat().st_size,
                    'modified': log_file.stat().st_mtime,
                })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'logs': log_files})

@require_http_methods(['GET'])
def api_download_log(request: HttpRequest, file_id: int, filename: str) -> FileResponse:
    """Download a log file."""
    uf = get_object_or_404(UploadedFile, id=file_id)
    
    # Security check: verify filename belongs to this file_id
    if not filename.startswith(f"{file_id}_"):
        raise Http404("Invalid log file")
    
    from_vm_dir = settings.SHARED_FOLDERS['FROM_VM']
    log_path = from_vm_dir / filename
    
    if not log_path.exists() or not log_path.is_file():
        raise Http404(f"Log file not found: {filename}")
    
    try:
        file_handle = open(log_path, 'rb')
        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=filename
        )
        return response
    except Exception as e:
        raise Http404(f"Error reading log file: {str(e)}")

@require_http_methods(['GET'])
def api_download_report(request: HttpRequest, file_id:int) -> HttpResponse:
    uf = get_object_or_404(UploadedFile, id=file_id)
    
    # Get progress (only progress/status)
    progress_data = get_progress(file_id)
    
    # Get results from database
    try:
        analysis_result = uf.analysis_result
        
        def get_child_data(model_attr, default_dict=None):
            if default_dict is None: default_dict = {}
            if hasattr(analysis_result, model_attr):
                return getattr(analysis_result, model_attr)
            return type('Dummy', (), default_dict)

        yara = get_child_data('yara_analysis')
        bazaar = get_child_data('bazaar_analysis')
        lstm = get_child_data('lstm_analysis')

        progress_data.update({
             'yara_filtered_matches': getattr(yara, 'matches', []), 
            'yara_raw_matches': getattr(yara, 'raw_matches', []),
            'yara_error': getattr(yara, 'error', None),
            
            'bazaar_success': not getattr(bazaar, 'error', True),
            'bazaar_is_malicious': getattr(bazaar, 'is_malicious', False),
            'bazaar_malware_info': getattr(bazaar, 'malware_info', {}),
            'bazaar_error': getattr(bazaar, 'error', None),
            
            'lstm_final_decision': getattr(lstm, 'final_decision', None),
            'lstm_max_prob_anomaly': getattr(lstm, 'max_prob_anomaly', None),
            'lstm_mean_prob_anomaly': getattr(lstm, 'mean_prob_anomaly', None),
            'lstm_num_windows': getattr(lstm, 'num_windows', None),
            'lstm_error': getattr(lstm, 'error', None),
            
            'interpreter': analysis_result.interpreter,
        })
    except ResultAnalysis.DoesNotExist:
        pass
    
    file_info = {
        'original_name': uf.original_name,
        'file_size': uf.file_size,
        'file_type': uf.file_type,
        'md5_hash': uf.md5_hash,
        'sha1_hash': uf.sha1_hash,
        'sha256_hash': uf.sha256_hash,
    }
    
    pdf_buffer = generate_pdf(file_info, progress_data)

    pdf = pdf_buffer.getvalue()
    pdf_buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"MalSandbox_Report_{uf.original_name.replace(' ', '_')}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response