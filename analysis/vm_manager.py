"""
VM Manager for handling global VMware VM instance.
This module manages a single VM instance that starts with Django and stays running.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Add the VM directory to Python path
vm_dir = Path(__file__).parent.parent / 'VM'
sys.path.insert(0, str(vm_dir))

try:
    from VM.SandboxRunner import SandboxRunner
except ImportError as e:
    logging.error(f"Failed to import SandboxRunner: {e}")
    SandboxRunner = None


class VMManager:
    """
    Manages a global VMware VM instance for the Django application.
    The VM starts when Django starts and stays running for fast file analysis.
    """
    
    _vm_instance: Optional[SandboxRunner] = None
    _is_initialized: bool = False
    
    @classmethod
    def initialize_vm(cls) -> bool:
        """
        Initialize and start the VMware VM using SandboxRunner's default configuration.
        
        Returns:
            bool: True if VM was successfully initialized, False otherwise
        """
        if cls._is_initialized:
            return cls._vm_instance is not None
            
        if SandboxRunner is None:
            logging.error("SandboxRunner not available - VM initialization skipped")
            return False
            
        try:
            # Create VM instance with SandboxRunner's default configuration
            cls._vm_instance = SandboxRunner()
            
            # Start the VM
            cls._vm_instance.start_vm(gui=False)  # Start in headless mode
            
            # Ensure the guest directory exists
            cls._vm_instance.ensure_guest_directory(str(cls._vm_instance.base_dir))
            
            cls._is_initialized = True
            logging.info("VMware VM initialized and started successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize VMware VM: {e}")
            cls._vm_instance = None
            cls._is_initialized = False
            return False
    
    @classmethod
    def get_vm(cls) -> Optional[SandboxRunner]:
        """
        Get the global VM instance.
        
        Returns:
            SandboxRunner or None: The VM instance if available, None otherwise
        """
        if not cls._is_initialized and cls._vm_instance is None:
            # Try to initialize if not already done
            cls.initialize_vm()
            
        return cls._vm_instance
    
    @classmethod
    def is_vm_ready(cls) -> bool:
        """
        Check if the VM is ready for use.
        
        Returns:
            bool: True if VM is ready, False otherwise
        """
        if not cls._is_initialized or cls._vm_instance is None:
            return False
            
        try:
            # Check VM status
            vm_info = cls._vm_instance.get_vm_info()
            return vm_info.get('status') == 'running'
        except Exception as e:
            logging.warning(f"Failed to check VM status: {e}")
            return False
    
    @classmethod
    def restart_vm(cls) -> bool:
        """
        Restart the VM if it's not working properly.
        
        Returns:
            bool: True if VM was successfully restarted, False otherwise
        """
        try:
            if cls._vm_instance:
                # Stop the current VM
                cls._vm_instance.stop_vm()
                
            # Reset state
            cls._vm_instance = None
            cls._is_initialized = False
            
            # Reinitialize
            return cls.initialize_vm()
            
        except Exception as e:
            logging.error(f"Failed to restart VM: {e}")
            return False
    
    @classmethod
    def cleanup_vm(cls) -> None:
        """
        Clean up the VM instance.
        This should be called when Django shuts down.
        """
        try:
            if cls._vm_instance:
                cls._vm_instance.cleanup()
                logging.info("VMware VM cleaned up successfully")
        except Exception as e:
            logging.error(f"Failed to cleanup VM: {e}")
        finally:
            cls._vm_instance = None
            cls._is_initialized = False


# Convenience function for views to use
def get_vm() -> Optional[SandboxRunner]:
    """
    Get the global VM instance for use in views.
    
    Returns:
        SandboxRunner or None: The VM instance if available, None otherwise
    """
    return VMManager.get_vm()


def is_vm_ready() -> bool:
    """
    Check if the VM is ready for use.
    
    Returns:
        bool: True if VM is ready, False otherwise
    """
    return VMManager.is_vm_ready()
