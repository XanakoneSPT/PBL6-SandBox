# Malware Analysis Sandbox

A Django-based web application for automated malware analysis using VM sandboxing.

## 🔍 How It Works

1. **Upload** - User uploads suspicious file via web interface
2. **Transfer** - Django saves file to VM shared folder
3. **Analysis** - VM sandbox executes file and monitors behavior
4. **Results** - VM writes analysis results back to shared folder
5. **Display** - Django shows classification and report to user
6. **Reset** - VM snapshot restored to clean state

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Django    │    │   Shared     │    │   VM Sandbox    │
│ (Web UI)    │◄──►│   Folders    │◄──►│  (Analysis)     │
└─────────────┘    └──────────────┘    └─────────────────┘
       │                   │                     │
   Web Interface     File Transfer         Real Analysis
   User Management   to_vm/ from_vm/      Behavior Monitor
   Result Display                         Classification
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 
- Redis
- VirtualBox with configured VM

### Installation

1. **Clone and setup environment**
```bash
git clone <repository>
cd malware-analysis-project
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup database**
```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE malware_analysis;
CREATE USER malware_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE malware_analysis TO malware_user;
\q

# Run migrations
python manage.py migrate
python manage.py createsuperuser
```

4. **Create shared folders**
```bash
mkdir -p shared_folders/uploads/to_vm
mkdir -p shared_folders/uploads/from_vm
```

5. **Start services**
```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery (background tasks)
celery -A mysite worker -l info

# Terminal 3: Redis
redis-server
```

## 📁 Project Structure

```
malware-analysis-project/
├── mysite/                     # Django project
├── analysis/                   # Main app
│   ├── models.py              # Database models
│   ├── views.py               # Web views
│   └── tasks.py               # Background tasks
├── shared_folders/uploads/     # VM communication
│   ├── to_vm/                 # Files → VM
│   └── from_vm/               # Results ← VM
├── static/                    # CSS, JS
├── templates/                 # HTML templates
└── manage.py
```

## 🔧 Configuration

### Django Settings (`mysite/settings.py`)
```python
# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'malware_analysis',
        'USER': 'malware_user',
        'PASSWORD': 'your_password',
    }
}

# Shared folders
SHARED_FOLDERS = {
    'TO_VM': BASE_DIR / 'shared_folders/uploads/to_vm/',
    'FROM_VM': BASE_DIR / 'shared_folders/uploads/from_vm/',
}

# File upload limits
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
```

### VM Setup
1. Create VirtualBox VM with your analysis OS
2. Install VM analysis agent (your Python script)  
3. Configure shared folders:
   - Host: `/path/to/shared_folders/uploads/`
   - Guest: `/mnt/analysis/`
4. Create clean snapshot: `VBoxManage snapshot VM_NAME take CleanState`

## 📊 Database Schema

- **MalwareSample**: File info, status, paths
- **AnalysisResult**: VM analysis results
- **User**: Django authentication

## 🔄 Workflow

### File Upload
```python
POST /upload/
→ Save to shared_folders/uploads/to_vm/
→ Start background monitoring task
```

### VM Analysis  
```bash
# VM Agent monitors /mnt/analysis/to_vm/
# Executes file with monitoring (strace, ptrace)
# Writes result to /mnt/analysis/from_vm/result.json
```

### Result Processing
```python
# Django monitors shared_folders/uploads/from_vm/
# Reads JSON result from VM
# Updates database and shows result to user
```

## 🛡️ Security Features

- Files never executed on host system
- Malware stored in non-web-accessible folders
- VM isolation prevents host infection
- Automatic VM snapshot restoration
- User authentication required

## 🚦 API Endpoints

- `GET /` - Dashboard
- `POST /upload/` - Upload file for analysis
- `GET /status/<id>/` - Check analysis progress (AJAX)
- `GET /result/<id>/` - View analysis results

## 🧪 Expected VM Result Format

```json
{
    "filename": "malware.exe",
    "classification": "Malicious",
    "confidence_score": 0.85,
    "is_malicious": true,
    "summary": "Trojan detected - network communication to suspicious IPs",
    "execution_time": 45.2,
    "file_operations": [
        {"action": "write", "path": "/tmp/malware_copy", "timestamp": 1234567890}
    ],
    "network_activity": [
        {"protocol": "tcp", "dest_ip": "192.168.1.100", "dest_port": 80}
    ],
    "process_creation": [
        {"process": "cmd.exe", "args": ["/c", "del /f /q *"]}
    ]
}
```

## 🐛 Troubleshooting

### Common Issues

**VM not detecting files:**
- Check shared folder mounting
- Verify permissions on shared_folders/
- Ensure VM agent is running

**Analysis stuck in 'analyzing' status:**
- Check VM is running and responsive
- Verify VM agent logs
- Check shared folder connectivity

**Database connection errors:**
- Verify PostgreSQL is running
- Check database credentials in settings.py
- Ensure database exists

## 🔧 Development

### Run tests
```bash
python manage.py test
```

### Create new migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Django admin
```bash
# Access at http://localhost:8000/admin/
python manage.py createsuperuser
```

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch  
5. Create Pull Request

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Use responsibly and only analyze malware in isolated environments. The authors are not responsible for any damage caused by misuse of this software.