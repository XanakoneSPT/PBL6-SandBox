# MalSandbox - Malware Analysis Sandbox Platform

**MalSandbox** is a modern, comprehensive malware analysis platform designed to automate the detection and analysis of malicious files. It combines multiple state-of-the-art detection engines—including **YARA** pattern matching, **Bazaar** threat intelligence, **LSTM** anomaly detection, and a **Virtual Machine (VM)** sandbox—into a single, unified interface.

The platform features a sleek **Glassmorphism UI**, ensuring a premium user experience with real-time progress tracking, responsive design, and intuitive data visualization.

---

## 🚀 Key Features

### 🛡️ Multi-Engine Analysis
- **YARA Pattern Matching**: Leverages signature-based detection to identify known malware families using custom and community rules.
- **Bazaar Intelligence**: Integrates with MalwareBazaar API to cross-reference file hashes against a global database of known threats.
- **LSTM Anomaly Detection**: Utilizes a TensorFlow-powered Long Short-Term Memory (LSTM) model to detect zero-day threats based on system call sequences.
- **VM Sandbox Execution**: Safely executes files in a controlled Virtual Machine environment to capture behavioral data (syscalls, file operations).

### 💻 Modern User Interface
- **Glassmorphism Design**: A sophisticated, dark-themed UI with translucent cards, blurred backgrounds, and neon accents.
- **Real-Time Progress**: Live updates during analysis using server-side polling, providing immediate feedback on scan status.
- **Responsive Layout**: Fully optimized for desktops and tablets, featuring smart tables and adaptive grids.
- **Interactive Reports**: Detailed drill-downs into match rules, behavioral logs, and risk scores.

### 👤 User Management
- **Secure Authentication**: Robust login and registration system with password encryption.
- **Analysis History**: Users can track their previous submissions, view statuses (Safe, Malicious, Pending), and re-download reports.
- **Anonymous Uploads**: Support for guest analysis with limited retention.

### 📄 Reporting & Export
- **PDF Generation**: One-click export of comprehensive analysis reports.
- **Log Access**: Direct access to raw VM logs (`syscalls`, `strace`) for deep-dive manual analysis.

---

## 🏗️ Technical Architecture

### Tech Stack
- **Backend Framework**: Django 5.2.8
- **Database**: PostgreSQL (Production) / SQLite (Dev)
- **Machine Learning**: TensorFlow / Keras (LSTM Model)
- **Analysis Tools**: YARA-Python, Python-Requests (Bazaar)
- **Frontend**: HTML5, CSS3 (Glassmorphism), JavaScript (Vanilla)
- **Report Engine**: ReportLab

### Analysis Pipeline
1.  **Ingestion**: File upload & hash calculation (MD5, SHA1, SHA256).
2.  **Static Analysis**: YARA rules scan the file content.
3.  **Intelligence Lookup**: SHA256 hash is queried against MalwareBazaar.
4.  **Dynamic Analysis**: File is executed in a VM Sandbox; syscalls are logged.
5.  **Behavioral Analysis**: Syscall logs are fed into the LSTM model to predict anomalies.
6.  **Result Aggregation**: All findings are compiled into a central report.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL (recommended) or SQLite
- YARA installed on the host system
- Virtual Machine (e.g., VirtualBox/VMware) with shared folder configuration (for Sandbox mode)

### 1. Clone the Repository
```bash
git clone https://github.com/XanakoneSPT/PBL6-SandBox.git
cd Server_v4
```

### 2. Environment Setup
Create and activate a virtual environment:
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Configuration
**Option A: PostgreSQL (Recommended)**
Create a database named `MalSanbox_db` and update `mysite/settings.py` with your credentials:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'MalSanbox_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**Option B: SQLite (Quick Start)**
No configuration needed; Django uses SQLite by default if PostgreSQL is not configured.

Run migrations:
```bash
python manage.py migrate
```

### 5. Configuration (Optional)
Create a `.env` file in the project root:
```env
BAZAAR_API_KEY=your_key_here
SECRET_KEY=your_django_secret
DEBUG=True
```

### 6. Run the Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` to start analyzing files.

---

## 📁 Project Structure

```
Server/
├── analysis/           # core Django application (models, views, urls)
├── mysite/             # project configuration (settings.py)
├── static/             # assets (CSS, JS, Images)
│   ├── css/            # Glassmorphism stylesheets (base.css, app.css, etc.)
│   └── img/            # Brand assets
├── templates/          # HTML templates (base.html, upload.html, etc.)
├── utils/              # Analysis Engines
│   ├── YARA_helper/    # YARA rules & scanner
│   ├── Bazaar_helper/  # Threat intelligence API
│   ├── lstm_detection/ # ML detection model
│   └── VM/             # Sandbox orchestrator
├── shared_folders/     # VM IO (to_vm/ from_vm/)
└── requirements.txt    # Python dependencies
```

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
