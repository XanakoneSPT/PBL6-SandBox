# 🛡️ PBL6 Malware Analysis Sandbox

**A comprehensive malware analysis platform combining static, dynamic, and ML-based detection.**

---

## 📋 Project Overview

This repository hosts a robust malware analysis system designed to detect zero-day threats and known signatures. It orchestrates a secure pipeline involving **YARA** pattern matching, **MalwareBazaar** intelligence, **LSTM** anomaly detection, and isolated **VM execution**.

### 🎯 Key Features
- **Multi-Engine Analysis**:
  - **Static**: YARA signature matching & PE header analysis.
  - **Intelligence**: Real-time hash lookups via MalwareBazaar.
  - **Dynamic**: VM-based execution monitoring (syscalls, file ops).
  - **ML-Based**: LSTM model for anomaly detection in behavioral logs.
- **Glassmorphism UI**: Modern, responsive web interface for file submissions and tracking.
- **Automated Orchestration**: Seamless handling of VM snapshots and file injection.
- **Detailed Reporting**: Comprehensive PDF reports and raw log access.

### 🏗️ System Architecture
```mermaid
graph LR
    User[User] --> Web[Django Web Interface]
    Web --> DB[(PostgreSQL)]
    Web --> Celery{Task Queue}
    Celery --> Static[Static Analysis]
    Celery --> Intel[Threat Intel]
    Celery --> VM[VM Sandbox]
    VM --> Logs[Behavioral Logs]
    Logs --> LSTM[LSTM Model]
    LSTM --> Result[Final Report]
```

---

## 🌟 Live Branches

The project is organized into feature branches for a modular development workflow:

### 🖥️ [`webserver`](../../tree/webserver) Branch
**Django Web Application & Core Backend**
- **Location**: `Server_v4/`
- **Core Logic**: Orchestrates the entire analysis pipeline.
- **Features**: User auth, file handling, VM control (`SandboxRunner.py`), and result aggregation.
- **ML Integration**: Includes the LSTM detection module and analysis utilities.

### 🔧 Other Components
- **`vm-agent`**: Analysis agent running inside the Guest VM.
- **`api`**: Standalone REST API (if separated from main webserver).

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/XanakoneSPT/PBL6-SandBox.git
cd pbl6-sandbox
```

### 2. Switch to Web Application
```bash
git checkout webserver
cd Server_v4
# Follow the detailed README.md in this directory for setup
```

### 3. System Requirements
- **Host**: Windows/Linux
- **Python**: 3.8+ (with `virtualenv`)
- **Database**: PostgreSQL (Recommended) or SQLite
- **Virtualization**: VirtualBox (configured with Snapshot)
- **External Tools**: YARA, properly configured shared folders

---

## 📂 Branch & Feature Structure

| Feature | Branch/Location | Status | Description |
|---------|-----------------|--------|-------------|
| **Web Interface** | [`webserver`](../../tree/webserver) | ✅ Active | Glassmorphism UI, Auth, Dashboard |
| **Analysis Core** | `Server_v4/analysis` | ✅ Active | Models, Views, Celery Tasks |
| **VM Orchestrator** | `Server_v4/utils/VM` | 🚧 Beta | `SandboxRunner` for VM control |
| **LSTM Detection** | `Server_v4/utils/lstm` | 🚧 Beta | ML model for behavioral analysis |
| **Report Gen** | `Server_v4/utils` | 🚧 Beta | PDF generation & log parsing |

---

## 🔄 Development Workflow

### For Contributors:
1.  **Clone**: `git clone <repo>`
2.  **Branch**: checkout `webserver` (main dev branch for backend).
3.  **Feature**: `git checkout -b feature/my-cool-feature`
4.  **PR**: Submit Pull Requests targeting **`webserver`**.

### For Users:
- **Deployment**: See [`Server_v4/README.md`](../../tree/webserver/Server_v4/README.md) for production deployment steps.

---

## 🛡️ Security Notice
⚠️ **DANGER: LIVE MALWARE HANDLING**
- This system executes real malware.
- **NEVER** run the Sandbox on a machine with sensitive data without strict isolation.
- Ensure the Host-Guest shared folders are strictly configured to prevent breakout.

---

## 📊 Project Status

| Component | Status | Progress | Notes |
|-----------|--------|----------|-------|
| **Django Backend** | ✅ Stable | 95% | Core logic complete |
| **Web Interface** | ✅ Stable | 90% | UI/UX polished |
| **VM Integration** | 🚧 Testing | 80% | Runner implemented, refining agent |
| **Analysis Engine** | 🚧 Integrated | 85% | YARA/Bazaar/LSTM integrated |
| **Documentation** | 📝 Active | 70% | Guides being updated |

---

## 🎓 Academic Project
**Course:** PBL6 - Advanced System Security
**Focus:** Automated Malware Analysis & Sandboxing techniques.

---

## 📝 License
This project is licensed under the **MIT License**.
