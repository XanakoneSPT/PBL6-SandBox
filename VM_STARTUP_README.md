# VMware Auto-Start Implementation

This implementation automatically starts the VMware VM when Django starts, making file analysis much faster.

## How It Works

1. **Django App Ready Signal**: When Django starts, the `AnalysisConfig.ready()` method is called
2. **VM Initialization**: The VM is started in headless mode during Django startup
3. **Global VM Instance**: A single VM instance is shared across all requests
4. **Background Analysis**: File analysis runs in background threads using the pre-started VM

## Files Modified/Created

### Modified Files:
- `analysis/apps.py` - Added AppConfig.ready() method for VM startup
- `analysis/views.py` - Updated to use pre-started VM for file analysis
- `analysis/urls.py` - Added VM status API endpoint
- `mysite/settings.py` - Added VM configuration settings

### New Files:
- `analysis/vm_manager.py` - Manages the global VM instance
- `analysis/management/commands/vm_control.py` - Django management command for VM control
- `analysis/management/__init__.py` - Management commands package
- `analysis/management/commands/__init__.py` - Management commands package

## Configuration

VM settings are configured in `mysite/settings.py`:

```python
VM_PATH = "E:\\Downloads\\kali-linux-2025.2-vmware-amd64.vmwarevm\\kali-linux-2025.2-vmware-amd64.vmx"
VM_GUEST_USER = "kali"
VM_GUEST_PASS = "kali"
VM_BASE_SNAPSHOT = "CleanSnapshot1"
VM_BASE_DIR = "/home/kali/SandboxAnalysis"
VM_TIMEOUT = 100
```

## Usage

### Starting Django Server
```bash
python manage.py runserver
```
The VM will automatically start when Django starts.

### VM Management Commands
```bash
# Check VM status
python manage.py vm_control status

# Start VM manually
python manage.py vm_control start

# Stop VM
python manage.py vm_control stop

# Restart VM
python manage.py vm_control restart

# Cleanup VM
python manage.py vm_control cleanup
```

### API Endpoints
- `GET /api/vm-status/` - Check VM status and availability

## Benefits

1. **Faster File Analysis**: No VM startup delay when users upload files
2. **Resource Efficiency**: Single VM instance shared across all requests
3. **Simple Implementation**: Minimal code changes required
4. **Error Handling**: Graceful handling of VM startup failures
5. **Management Tools**: Easy VM control through Django commands

## Error Handling

- If VM fails to start during Django startup, the server will still start
- VM can be started manually later using management commands
- File analysis will show appropriate error messages if VM is not available
- Proper cleanup when Django shuts down

## Troubleshooting

1. **VM Not Starting**: Check VMware installation and VM path in settings
2. **VM Not Ready**: Use `python manage.py vm_control status` to check VM state
3. **File Analysis Fails**: Check VM status API endpoint for debugging info
4. **VM Crashes**: Use `python manage.py vm_control restart` to restart VM

## Notes

- The VM runs in headless mode (no GUI) for better performance
- VM is automatically cleaned up when Django shuts down
- All VM operations are logged for debugging
- The implementation is thread-safe for concurrent file analysis
