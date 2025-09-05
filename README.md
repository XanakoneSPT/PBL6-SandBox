    # SandboxRunner.py

    ## Overview

    **SandboxRunner.py** is a Python module that provides a secure sandbox environment for executing and analyzing potentially untrusted code using VMware virtual machines. It supports multiple programming languages and offers system call tracing for advanced code analysis.

    ## Features

    - **VM Control:** Start, stop, rollback, and snapshot VMware virtual machines.
    - **File Operations:** Securely copy files between the host and guest VM.
    - **Code Execution:** Run code in various languages (Python, C, C++, Java, Go, etc.) inside the VM.
    - **Compilation Support:** Compile source code in the guest VM before execution.
    - **System Call Tracing:** Analyze code behavior using `strace` for syscall logging.
    - **Custom Tracker:** Compile and run custom C trackers to monitor other programs.
    - **Automatic Cleanup:** Rollback VM to a clean state after analysis.

    ## Requirements

    - VMware Workstation or Player
    - `vmrun` utility available in PATH
    - Kali Linux VM with VMware Tools installed

    ## Usage

    1. Configure the VM path, guest credentials, and snapshot name.
    2. Use the `SandboxRunner` class to manage VM lifecycle and run code securely.
    3. Analyze code with system call tracing or custom trackers as needed.