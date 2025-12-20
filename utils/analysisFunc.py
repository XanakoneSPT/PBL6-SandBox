import os
import shutil
import logging
from hashlib import sha256
from ntpath import isdir, isfile
from pathlib import Path

from django.conf import settings
from django.db import transaction

from analysis.models import UploadedFile, ResultAnalysis, YaraAnalysis, BazaarAnalysis, LstmAnalysis

from utils.progress import _update_progress
from utils.Bazaar_helper.checker_bazaar import check_hash
from utils.lstm_detection.anormaly_predictor import AnomalyDetector

def _run_yara_scan(file_path: str) -> dict:

    logger = logging.getLogger(__name__)
    result = {
        'filtered_matches': [],
        'raw_matches': [],
        'error': None
    }

    try:
        from utils.YARA_helper.YARAScanner import YARAScanner
        scanner = YARAScanner(auto_filter=True)
        
        filtered_matches = scanner.scan_file(file_path, filter_results=True)
        raw_matches = scanner.scan_file(file_path, filter_results=False)

        #Convert to dictionaries
        result['filtered_matches'] = [
            {
                'rule': m.rule, 
                'description': m.meta.get('description', 'No description') if m.meta else 'No description'
            } for m in filtered_matches
        ]
        result['raw_matches'] = [
            {
                'rule': m.rule,
                'description': m.meta.get('description', 'No description') if m.meta else 'No description'
            } for m in raw_matches]
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"YARA scan failed: {e}")

    return result

def _run_bazaar_scan(sha256_hash: str) -> dict:

    logger = logging.getLogger(__name__)
    result = {
        'success': False,
        'is_malicious': False,
        'malware_info': None,
        'error': None
    }

    try:
        bazaar_result = check_hash(sha256_hash, "sha256")

        result['success'] = bazaar_result['success']
        result['is_malicious'] = bazaar_result['is_malicious']
        result['malware_info'] = bazaar_result['malware_info']
        result['error'] = bazaar_result.get('error')

    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Bazaar scan failed: {e}")

    return result

def _run_lstm_scan(log_path: str) -> dict:
    logger = logging.getLogger(__name__)
        
    lstm_base = settings.BASE_DIR / "utils" / "lstm_detection"
    model_path = lstm_base / "model" / "lstm_adfa_model.keras"
    syscall_map_path = lstm_base / "lib" / "linux_syscalls_x86_64_parsed.json"

    result = {
        'final_decision': None,
        'max_prob_anomaly': None,
        'mean_prob_anomaly': None,
        'num_windows': None,
        'error': None
    }

    try:
        detector = AnomalyDetector(
            model_path= str(model_path),
            syscall_map_path= str(syscall_map_path)
        )

        lstm_result = detector.predict_from_log(log_path)

        result['final_decision'] = lstm_result['final_decision']
        result['max_prob_anomaly'] = lstm_result['max_prob_anomaly']
        result['mean_prob_anomaly'] = lstm_result['mean_prob_anomaly']
        result['num_windows'] = lstm_result['num_windows']
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"LSTM failed: {e}")

    return result

def _analyze_file(uploaded_file_id: int) -> None:
    logger = logging.getLogger(__name__)
    
    # Get uploaded file from database
    try:
        uf = UploadedFile.objects.get(id=uploaded_file_id)
    except UploadedFile.DoesNotExist:
        logger.error(f"UploadedFile not found: id={uploaded_file_id}")
        return
    except Exception as e:
        logger.error(f"Failed to get file: {e}")
        return

    # Use ResultAnalysis
    analysis_result, created = ResultAnalysis.objects.get_or_create(
        uploaded_file=uf,
        defaults={'status': 'pending'}
    )
    
    _update_progress(uploaded_file_id, 5, "processing")
    
    # Get file path on Django server
    try:
        host_file_path = uf.file_path.path # Updated field name to file_path
    except Exception as e:
        logger.error(f"Failed to get file path: {e}")
        return
    _update_progress(uploaded_file_id, 10)
    
    # YARA scan
    _update_progress(uploaded_file_id, 15)
    try:
        yara_results = _run_yara_scan(host_file_path)
        
        # Save to YaraAnalysis
        YaraAnalysis.objects.update_or_create(
            result_analysis=analysis_result,
            defaults={
                'matches': yara_results.get('filtered_matches', []),
                'raw_matches': yara_results.get('raw_matches', []),
                'error': yara_results.get('error')
            }
        )
        
        # Debug print
        print("\n" + "="*50)
        print("YARA SCAN RESULTS:")
        print("="*50)
        print(f"Filtered matches: {len(yara_results.get('filtered_matches', []))}")
        print(f"Raw matches: {len(yara_results.get('raw_matches', []))}")
        print("="*50 + "\n")
    except Exception as e:
        logger.error(f"YARA scan failed: {e}")
        YaraAnalysis.objects.update_or_create(
            result_analysis=analysis_result,
            defaults={'error': str(e)}
        )
        print(f"\n[YARA ERROR] {e}\n")
    _update_progress(uploaded_file_id, 20)
    
    # Bazaar scan
    _update_progress(uploaded_file_id, 30)
    try:
        if uf.sha256_hash:
            bazaar_results = _run_bazaar_scan(uf.sha256_hash)
            
            BazaarAnalysis.objects.update_or_create(
                result_analysis=analysis_result,
                defaults={
                    'is_malicious': bazaar_results.get('is_malicious', False),
                    'malware_info': bazaar_results.get('malware_info') if bazaar_results.get('malware_info') is not None else {},
                    'error': bazaar_results.get('error')
                }
            )

            # Debug print
            print("\n" + "="*50)
            print("BAZAAR SCAN RESULTS:")
            print("="*50)
            print(f"Success: {bazaar_results.get('success', False)}")
            print("="*50 + "\n")
        else:
            BazaarAnalysis.objects.update_or_create(
                result_analysis=analysis_result,
                defaults={'error': 'No hash'}
            )
            print("\n[BAZAAR] No SHA256 hash available\n")
    except Exception as e:
        logger.error(f"Bazaar scan failed: {e}")
        BazaarAnalysis.objects.update_or_create(
            result_analysis=analysis_result,
            defaults={'error': str(e)}
        )
        print(f"\n[BAZAAR ERROR] {e}\n")
    _update_progress(uploaded_file_id, 40)
    
    # Create SandboxRunner instance
    try:
        from utils.VM.SandboxRunner import SandboxRunner
        VMrunner = SandboxRunner()
        _update_progress(uploaded_file_id, 45)
    except Exception as e:
        logger.error(f"Failed to create SandboxRunner: {e}")
        analysis_result.status = 'error'
        analysis_result.save()
        _update_progress(uploaded_file_id, 100, "error")
        return
    
    # Copy file to VM and run analysis
    try:
        guest_full_path = VMrunner.copy_to_vm(host_file_path)
        _update_progress(uploaded_file_id, 50)
        guest_filename = Path(guest_full_path).name
        interpreter, ext, _ = VMrunner.detect_language(guest_full_path)
        _update_progress(uploaded_file_id, 55)
        
        analysis_result.interpreter = interpreter if interpreter else None
        analysis_result.save()
        
        # Run VM analysis
        _update_progress(uploaded_file_id, 60)
        try:
            if ext in (".pdf", ".doc", ".docx", ".txt", ".rtf"):
                log_path_in_vm = VMrunner.analyze_document(guest_filename, log_file="document_analysis.txt")
            else:
                log_path_in_vm = VMrunner.analyze_with_strace(guest_filename, log_file="syscall_log.txt")
        except Exception as e:
            logger.error(f"VM analysis failed: {e}")
            log_path_in_vm = None
        
        # Copy log file back from VM
        _update_progress(uploaded_file_id, 75)
        if log_path_in_vm:
            dest_dir = settings.SHARED_FOLDERS["FROM_VM"]
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / f"{uf.id}_{Path(host_file_path).stem}_analysis.log"
            
            try:
                VMrunner.get_log_file(log_path_in_vm, str(dest_path))
                if dest_path and dest_path.exists():
                    analysis_result.vm_log_file_path = dest_path.name
                    analysis_result.save()
            except Exception as e:
                logger.error(f"Failed to copy log file from VM: {e}")
                dest_path = None
            
            # Run LSTM detection (only for strace logs)
            if dest_path and dest_path.exists() and ext not in (".pdf", ".doc", ".docx", ".txt", ".rtf"):
                _update_progress(uploaded_file_id, 85)
                try:
                    lstm_results = _run_lstm_scan(str(dest_path))
                    
                    LstmAnalysis.objects.update_or_create(
                        result_analysis=analysis_result,
                        defaults={
                            'final_decision': lstm_results.get('final_decision'),
                            'max_prob_anomaly': lstm_results.get('max_prob_anomaly'),
                            'mean_prob_anomaly': lstm_results.get('mean_prob_anomaly'),
                            'num_windows': lstm_results.get('num_windows'),
                            'error': lstm_results.get('error'),
                            'is_anomalous': lstm_results.get('final_decision') == 'Anomaly' # Infer boolean
                        }
                    )
                    
                    # Debug print
                    print("\n" + "="*50)
                    print("LSTM DETECTION RESULTS:")
                    print("="*50)
                    print(f"Final Decision: {lstm_results.get('final_decision')}")
                    print("="*50 + "\n")
                    _update_progress(uploaded_file_id, 90)
                except Exception as e:
                    logger.error(f"LSTM detection failed: {e}")
                    LstmAnalysis.objects.update_or_create(
                        result_analysis=analysis_result,
                        defaults={'error': str(e)}
                    )
                    print(f"\n[LSTM ERROR] {e}\n")
                    _update_progress(uploaded_file_id, 90)
            else:
                _update_progress(uploaded_file_id, 80)
        else:
            _update_progress(uploaded_file_id, 80)
            
    except Exception as e:
        logger.error(f"Failed to copy file to VM or run analysis: {e}")
        analysis_result.status = 'error'
        analysis_result.save()
        _update_progress(uploaded_file_id, 100, "error")
        return
    
    _update_progress(uploaded_file_id, 95)
    analysis_result.status = 'done'
    analysis_result.save()
    _update_progress(uploaded_file_id, 100, "done")
    print("\n[ANALYSIS COMPLETE] All scans finished!\n")