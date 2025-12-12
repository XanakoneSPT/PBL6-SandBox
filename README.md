# MalSandbox - Malware Analysis Sandbox Platform

A comprehensive Django-based web application for automated malware analysis using multiple detection engines including YARA pattern matching, Bazaar malware intelligence, LSTM anomaly detection, and virtual machine sandbox execution.

## 🎯 Features

- **Multi-Engine Analysis**: Combines multiple detection methods for comprehensive threat analysis
  - **YARA Pattern Matching**: Signature-based detection using YARA rules
  - **Bazaar Integration**: Malware intelligence lookup via Bazaar API
  - **LSTM Anomaly Detection**: Machine learning-based behavioral analysis
  - **VM Sandbox Execution**: Safe execution environment for dynamic analysis

- **User Management**: 
  - User registration and authentication
  - Secure file upload with user-specific history
  - Support for anonymous uploads

- **Real-time Progress Tracking**: 
  - Live progress updates during analysis
  - Status monitoring via API endpoints

- **Comprehensive Reporting**:
  - Detailed analysis results with all detection engine outputs
  - PDF report generation
  - VM execution logs access

- **File Information**:
  - Automatic hash calculation (MD5, SHA1, SHA256)
  - File type detection
  - File size tracking

## 🏗️ Architecture

### Technology Stack

- **Backend**: Django 5.2.8
- **Database**: PostgreSQL
- **Machine Learning**: TensorFlow (LSTM model)
- **Pattern Matching**: YARA-Python
- **Report Generation**: ReportLab

### Project Structure

```
Server_v4/
├── analysis/              # Main Django app
│   ├── models.py         # Database models (UploadedFile, AnalysisResult)
│   ├── views.py          # View handlers and API endpoints
│   ├── urls.py           # URL routing
│   └── migrations/       # Database migrations
├── mysite/               # Django project settings
│   ├── settings.py       # Configuration
│   └── urls.py           # Root URL configuration
├── utils/                # Analysis utilities
│   ├── YARA_helper/      # YARA rule files and integration
│   ├── Bazaar_helper/    # Bazaar API integration
│   ├── lstm_detection/   # LSTM anomaly detection
│   ├── VM/               # Virtual machine sandbox runner
│   ├── analysisFunc.py   # Main analysis orchestration
│   ├── hashes_cal.py     # Hash calculation utilities
│   ├── getFileType.py    # File type detection
│   ├── progress.py       # Progress tracking
│   └── report_gen.py     # PDF report generation
├── templates/            # HTML templates
│   ├── base.html
│   ├── upload.html
│   ├── result.html
│   ├── history.html
│   ├── login.html
│   └── register.html
├── shared_folders/       # VM communication directories
│   ├── to_vm/           # Files sent to VM
│   └── from_vm/          # Logs received from VM
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
└── ERD.md                # Database schema documentation
```

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- YARA installed on system
- Virtual machine setup (for VM sandbox analysis)
- Git (for YARA rules repository)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Server_v4
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup

1. Create PostgreSQL database:

```sql
CREATE DATABASE MalSanbox_db;
```

2. Update database credentials in `mysite/settings.py`:

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

3. Run migrations:

```bash
python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Environment Configuration

Create a `.env` file in the project root for sensitive configuration (if needed):

```env
BAZAAR_API_KEY=your_bazaar_api_key
SECRET_KEY=your_django_secret_key
```

### 7. YARA Rules Setup

Ensure YARA rules are properly configured in `utils/YARA_helper/`. The system will automatically load and use these rules for pattern matching.

### 8. LSTM Model

The LSTM model should be located at `utils/lstm_detection/model/lstm_adfa_model.keras`. Ensure this file exists for anomaly detection to work.

## 🎮 Usage

### Starting the Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

### Web Interface

1. **Upload File**: Navigate to the home page and upload a file for analysis (max 100MB)
2. **View Results**: After upload, you'll be redirected to the results page with real-time progress
3. **History**: Logged-in users can view their analysis history
4. **Download Reports**: Generate and download PDF reports from the results page

### API Endpoints

#### Get Analysis Progress
```
GET /api/progress/<file_id>/
```
Returns JSON with current analysis progress and results.

#### Get VM Logs List
```
GET /api/vm-logs/<file_id>/
```
Returns list of available VM log files for the analysis.

#### Get VM Log Content
```
GET /api/vm-logs/<file_id>/<filename>/
```
Returns content of a specific VM log file.

#### Download Log File
```
GET /api/download-log/<file_id>/<filename>/
```
Downloads a VM log file.

#### Download PDF Report
```
GET /api/download-report/<file_id>/
```
Generates and downloads a PDF report of the analysis.

## 📊 Database Schema

The application uses three main models:

- **User**: Django's built-in user model for authentication
- **UploadedFile**: Stores uploaded file information and hashes
- **AnalysisResult**: Stores results from all analysis engines (YARA, Bazaar, LSTM, VM)

See `ERD.md` for detailed database schema documentation.

## 🔧 Configuration

### File Upload Limits

Default maximum file size is 100MB. Modify in `analysis/views.py`:

```python
max_size = 100*1024*1024  # 100MB
```

### Shared Folders

VM communication folders are automatically created at:
- `shared_folders/to_vm/` - Files sent to VM
- `shared_folders/from_vm/` - Logs received from VM

These paths are configured in `mysite/settings.py`.

## 🧪 Testing

Run Django tests:

```bash
python manage.py test
```

## 📝 Development Notes

### Analysis Flow

1. User uploads a file
2. System calculates file hashes (MD5, SHA1, SHA256)
3. File type is detected
4. Background thread starts analysis:
   - YARA pattern matching
   - Bazaar malware lookup
   - LSTM anomaly detection
   - VM sandbox execution (if applicable)
5. Results are stored in database
6. User can view results and download reports

### Threading

File analysis runs in background threads to avoid blocking the web interface. Progress is tracked via JSON files and database updates.

## 🔒 Security Considerations

- **File Access Control**: Users can only view their own uploaded files (unless anonymous)
- **CSRF Protection**: Django's CSRF middleware is enabled
- **File Size Limits**: Maximum upload size enforced
- **Input Validation**: File type and content validation
- **Secret Key**: Change `SECRET_KEY` in production
- **DEBUG Mode**: Set `DEBUG = False` in production

## 🐛 Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check database credentials in `settings.py`
- Ensure database exists

### YARA Errors
- Verify YARA is installed: `yara --version`
- Check YARA rules are in correct directory
- Review `yara_error` field in AnalysisResult

### VM Analysis Not Working
- Verify VM is properly configured
- Check shared folders exist and have correct permissions
- Review VM log files in `shared_folders/from_vm/`

### LSTM Errors
- Ensure model file exists at `utils/lstm_detection/model/lstm_adfa_model.keras`
- Check TensorFlow installation
- Review `lstm_error` field in AnalysisResult

## 📄 License

[Specify your license here]

## 👥 Contributors

[Add contributor information]

## 🙏 Acknowledgments

- Django Framework
- YARA Project
- Bazaar Malware Intelligence
- TensorFlow/Keras

---

For detailed database schema information, see [ERD.md](ERD.md)
