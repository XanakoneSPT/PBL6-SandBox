import shutil
from django.conf import settings
from django.utils.autoreload import logging

def cleanup_uploaded_file() -> None:
    logger = logging.getLogger(__name__)
    to_vm_dir = settings.SHARED_FOLDERS['TO_VM']

    try:
        shutil.rmtree(to_vm_dir)
        to_vm_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Cleaned up TO_VM folder successfully")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")