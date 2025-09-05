# 🛡️ PBL6 Malware Analysis Sandbox

**A Django-based web application for automated malware analysis using VM sandboxing.**

---

## 📋 Project Overview

This repository contains a complete malware analysis system that safely executes suspicious files in isolated virtual machines and provides detailed behavioral analysis reports.

### 🎯 Key Features
- **Web-based file upload** interface
- **VM isolation** for safe malware execution  
- **Automated analysis** with behavior monitoring
- **Real-time status** tracking
- **Detailed reporting** of malware activities
- **VM snapshot restoration** for clean environments

### 🏗️ System Architecture
```
User → Django Web Interface → Shared Folders → VM Sandbox → Analysis Results
```

---

## 🌟 Live Branches

The project is organized into feature branches for better development workflow:

### 🖥️ [`webserver`](../../tree/webserver) Branch
**Django Web Application & API**
- User authentication and file upload interface
- Background task processing with Celery
- Database models for samples and results  
- Real-time analysis status monitoring
- Web-based report viewing

### 🔧 Other Branches (Coming Soon)
- **`vm-agent`** - VM analysis agent and monitoring scripts
- **`api`** - REST API for external integrations
- **`frontend`** - Vue.js frontend (if separated from Django)

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/pbl6-sandbox.git
cd pbl6-sandbox
```

### 2. Switch to Feature Branch
```bash
# For Django web application
git checkout webserver

# Follow the setup instructions in that branch's README
```

### 3. System Requirements
- **Python 3.8+**
- **PostgreSQL** database
- **Redis** for task queue
- **VirtualBox** with configured VM
- **Linux/Windows** host system

---

## 📂 Branch Structure

| Branch | Purpose | Status | Documentation |
|--------|---------|--------|---------------|
| [`main`](../../tree/main) | Repository entry point | ✅ Active | This README |
| [`webserver`](../../tree/webserver) | Django web application | 🚧 Development | [Webserver README](../../tree/webserver#readme) |
| `vm-agent` | VM analysis scripts | 📅 Planned | Coming Soon |
| `api` | REST API endpoints | 📅 Planned | Coming Soon |

---

## 🔄 Development Workflow

### For Contributors:

1. **Clone and explore**
   ```bash
   git clone https://github.com/your-username/pbl6-sandbox.git
   cd pbl6-sandbox
   git branch -a  # See all available branches
   ```

2. **Work on features**
   ```bash
   git checkout webserver           # Switch to feature branch
   git checkout -b feature/my-task  # Create your feature branch
   # Make changes, commit, and push
   ```

3. **Create Pull Requests**
   - Create PR **into the feature branch** (e.g., `webserver`)
   - **Not into `main`** (main stays clean)

### For Users:
- Check the [`webserver`](../../tree/webserver) branch for installation instructions
- Follow the setup guide in that branch's README

---

## 🛡️ Security Notice

⚠️ **This system handles potentially dangerous malware files.**

- Only run in **isolated environments**
- Use **dedicated VMs** for analysis
- Never execute malware on production systems
- Follow proper **incident response** procedures

---

## 🎓 Academic Project

This is a **PBL6 (Project-Based Learning)** academic project focused on:
- Cybersecurity and malware analysis
- Web application development
- Virtual machine orchestration
- Automated security testing

**Institution:** [Your University]  
**Course:** PBL6 - Advanced System Security  
**Team:** [Your Team Name]

---

## 📊 Project Status

| Component | Status | Progress |
|-----------|--------|----------|
| Django Backend | 🚧 In Development | 80% |
| Web Interface | 🚧 In Development | 70% |
| VM Integration | 📅 Planned | 0% |
| Analysis Engine | 📅 Planned | 0% |
| Documentation | ✅ Active | 60% |

---

## 🤝 Contributing

We welcome contributions! Please:

1. **Check existing branches** for relevant work
2. **Create feature branches** for new development  
3. **Follow coding standards** established in each branch
4. **Submit PRs** to appropriate feature branches
5. **Update documentation** as needed

### Code of Conduct
- Respectful collaboration
- Clear commit messages
- Proper testing before PR
- Security-first mindset

---

## 📚 Documentation

- **[Webserver Setup](../../tree/webserver#readme)** - Django application setup
- **[API Reference](../../tree/api#readme)** - REST API documentation (coming soon)
- **[VM Configuration](../../wiki)** - Virtual machine setup guide
- **[Security Guidelines](../../wiki/Security)** - Safe handling procedures

---

## 📞 Support & Contact

- **Issues:** [GitHub Issues](../../issues)
- **Discussions:** [GitHub Discussions](../../discussions)  
- **Wiki:** [Project Wiki](../../wiki)
- **Email:** [your-email@university.edu]

---

## 📝 License

This project is licensed under the **MIT License**.

```
MIT License - Educational and Research Use Only
See LICENSE file for full details.
```

---

## ⚡ Quick Links

- 🌐 **[Web Application](../../tree/webserver)** - Django malware analysis interface
- 📖 **[Documentation](../../wiki)** - Complete setup and usage guides  
- 🐛 **[Report Issues](../../issues)** - Bug reports and feature requests
- 💬 **[Discussions](../../discussions)** - Community support and ideas

---

**⭐ Star this repository if you find it useful!**