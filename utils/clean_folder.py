import shutil
import os
from pathlib import Path
from django.conf import settings
import logging

def cleanup_uploaded_file() -> None:
    """Clears the entire TO_VM directory. Used for system reset."""
    logger = logging.getLogger(__name__)
    to_vm_dir = settings.SHARED_FOLDERS['TO_VM']

    try:
        shutil.rmtree(to_vm_dir)
        to_vm_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Cleaned up TO_VM folder successfully")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

def delete_analysis_data(uploaded_file) -> None:
    """Deletes all physical files associated with an UploadedFile."""
    logger = logging.getLogger(__name__)
    
    # 1. Delete original uploaded file
    try:
        if uploaded_file.file_path and os.path.exists(uploaded_file.file_path.path):
            os.remove(uploaded_file.file_path.path)
            logger.info(f"Deleted file: {uploaded_file.file_path.path}")
    except Exception as e:
        logger.error(f"Failed to delete original file: {e}")

    # 2. Delete progress JSON
    try:
        progress_path = settings.SHARED_FOLDERS['TO_VM'] / 'progress' / f"{uploaded_file.id}.json"
        if progress_path.exists():
            os.remove(progress_path)
            logger.info(f"Deleted progress file: {progress_path}")
    except Exception as e:
        logger.error(f"Failed to delete progress file: {e}")

    # 3. Delete VM logs
    try:
        from_vm_dir = settings.SHARED_FOLDERS['FROM_VM']
        # Pattern: {file_id}_*_analysis.log
        for log_file in from_vm_dir.glob(f"{uploaded_file.id}_*_analysis.log"):
            try:
                os.remove(log_file)
                logger.info(f"Deleted log file: {log_file}")
            except OSError as e:
                logger.error(f"Error deleting log {log_file}: {e}")
    except Exception as e:
        logger.error(f"Failed to clean up logs: {e}")