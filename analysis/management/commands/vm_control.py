"""
Django management command for VM control operations.
"""

from django.core.management.base import BaseCommand, CommandError
from analysis.vm_manager import VMManager
import logging


class Command(BaseCommand):
    help = 'Control the VMware VM instance'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'restart', 'status', 'cleanup'],
            help='Action to perform on the VM'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        try:
            if action == 'start':
                self.start_vm()
            elif action == 'stop':
                self.stop_vm()
            elif action == 'restart':
                self.restart_vm()
            elif action == 'status':
                self.check_status()
            elif action == 'cleanup':
                self.cleanup_vm()
                
        except Exception as e:
            raise CommandError(f'VM operation failed: {e}')

    def start_vm(self):
        """Start the VM."""
        self.stdout.write('Starting VMware VM...')
        success = VMManager.initialize_vm()
        if success:
            self.stdout.write(
                self.style.SUCCESS('VM started successfully')
            )
        else:
            raise CommandError('Failed to start VM')

    def stop_vm(self):
        """Stop the VM."""
        self.stdout.write('Stopping VMware VM...')
        vm = VMManager.get_vm()
        if vm:
            vm.stop_vm()
            self.stdout.write(
                self.style.SUCCESS('VM stopped successfully')
            )
        else:
            self.stdout.write('No VM instance found')

    def restart_vm(self):
        """Restart the VM."""
        self.stdout.write('Restarting VMware VM...')
        success = VMManager.restart_vm()
        if success:
            self.stdout.write(
                self.style.SUCCESS('VM restarted successfully')
            )
        else:
            raise CommandError('Failed to restart VM')

    def check_status(self):
        """Check VM status."""
        vm = VMManager.get_vm()
        if vm:
            vm_info = vm.get_vm_info()
            self.stdout.write(f"VM Status: {vm_info['status']}")
            self.stdout.write(f"VM Path: {vm_info['vm_path']}")
            self.stdout.write(f"Base Snapshot: {vm_info['base_snapshot']}")
            self.stdout.write(f"Guest User: {vm_info['guest_user']}")
            self.stdout.write(f"Base Directory: {vm_info['base_dir']}")
        else:
            self.stdout.write('No VM instance found')

    def cleanup_vm(self):
        """Cleanup the VM."""
        self.stdout.write('Cleaning up VMware VM...')
        VMManager.cleanup_vm()
        self.stdout.write(
            self.style.SUCCESS('VM cleanup completed')
        )
