from django.apps import AppConfig
from django.core.signals import request_finished
from django.db.models.signals import post_migrate
import logging
import os
import atexit


class AnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analysis'
    
    def ready(self):
        """
        Initialize VMware VM when Django starts up.
        This method is called once when Django is ready to serve requests.
        """
        # Only run in the main process, not in subprocesses
        if os.environ.get('RUN_MAIN') != 'true':
            return
            
        try:
            # Import here to avoid circular imports
            from .vm_manager import VMManager
            
            # Initialize and start the VM
            VMManager.initialize_vm()
            logging.info("VMware VM initialized and started successfully")
            
            # Register cleanup function for when Django shuts down
            atexit.register(self._cleanup_vm)
            
        except Exception as e:
            logging.error(f"Failed to initialize VMware VM: {e}")
            # Don't raise the exception to prevent Django startup failure
            # The VM can be started manually later if needed
    
    def _cleanup_vm(self):
        """Clean up VM when Django shuts down."""
        try:
            from .vm_manager import VMManager
            VMManager.cleanup_vm()
            logging.info("VMware VM cleanup completed")
        except Exception as e:
            logging.error(f"Failed to cleanup VMware VM: {e}")

