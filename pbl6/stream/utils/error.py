class SandboxError(Exception):
    """Base exception for sandbox operations."""
    pass

class VMControlError(SandboxError):
    """Exception for VM control operations."""
    pass

class FileOperationError(SandboxError):
    """Exception for file operations."""
    pass

class ExecutionError(SandboxError):
    """Exception for code execution operations."""
    pass