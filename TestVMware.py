import os
import SandboxRunner as sr

# ============ Usage Examples ============
def random_string(length=8):
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def example_usage():
    # Initialize sandbox
    sandbox = sr.SandboxRunner()
    
    try:
        # Start VM
        sandbox.start_vm()

        files = sandbox.copy_directory_to_vm(".cache")
        # Ensure .logs directory exists
        os.makedirs("./.logs", exist_ok=True)
        # print("Files copied to VM:", files)
        # Cleanup (rollback to clean state)
        for file in files:
            log_path = sandbox.analyze_with_strace(file)
            print(f"Strace log created at: {log_path}")
            # create random name log file
            sandbox.get_log_file(log_path, f"./.logs/strace_log_{random_string(5)}.log")
        # Uncomment the following line to cleanup after analysis
        # sandbox.cleanup()
        
    except (sr.SandboxError, Exception) as e:
        print(f"Analysis failed: {e}")
        # Uncomment the following line to rollback VM on error
        # sandbox.rollback_vm() 


if __name__ == "__main__":
    example_usage()