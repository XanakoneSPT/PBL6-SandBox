from django.apps import AppConfig
import logging
from utils.VM.SandboxRunner import SandboxRunner
from utils.clean_folder import cleanup_uploaded_file

vmRunner = None

class AnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analysis'

    def ready(self):

        global vmRunner

        try:
            vmRunner = SandboxRunner()

            try:
                info = vmRunner.get_vm_info()
                if info.get('status')==('running'):
                    vmRunner.stop_vm(force=True)
            except:
                pass

            vmRunner.revert_to_snapshot()
            cleanup_uploaded_file()
            vmRunner.start_vm(gui=False)
        except:
            pass
        return super().ready()
