import SandboxRunner as sr

# ============ Usage Examples ============

def example_usage():
    """
    Example usage of SandboxRunner
    """
    # Initialize sandbox
    sandbox = sr.SandboxRunner()
    
    try:
        # Start VM
        sandbox.start_vm()
        
        # Copy malicious code to VM
        sandbox.copy_to_vm(".cache/suspicious_code.py", "analysis/suspicious_code.py")
        
        # Execute with system call tracing
        log_file = sandbox.analyze_with_strace(
            "analysis/suspicious_code.py",
            "analysis_log.txt",
            ["--verbose"]
        )
        
        # Copy results back to host
        sandbox.copy_from_vm("analysis_log.txt", "host_analysis_log.txt")
        
        # Cleanup (rollback to clean state)
        sandbox.cleanup()
        
    except (sr.SandboxError, Exception) as e:
        print(f"Analysis failed: {e}")
        sandbox.rollback_vm()  # Emergency rollback


if __name__ == "__main__":
    # Run example if script is executed directly
    example_usage()