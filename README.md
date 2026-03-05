# PPW - Personal Password Manager 🔐

A secure, feature-rich password manager built with Python, MongoDB Atlas, and modern security practices. Store, manage, and protect your passwords with enterprise-grade encryption.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/cloud/atlas)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🌟 Features

### Security First
- **AES-256-GCM Encryption** - Military-grade encryption for all passwords
- **PBKDF2 Key Derivation** - 100,000 iterations to prevent brute-force attacks
- **Zero-Knowledge Architecture** - Your master password never leaves your device
- **Two-Layer Encryption** - Separate encryption key for easy master password changes
- **Account Lockout Protection** - Automatic lockout after failed login attempts
- **Activity Audit Trail** - Complete logging of all security-related actions
- **Secure Session Management** - Automatic timeout and secure token handling

### Core Functionality
- 🔑 **Master Password Protection** - Single password to access all accounts
- 📝 **Account Management** - Store unlimited passwords with metadata
- 🏷️ **Organization** - Categories, tags, and favorites
- 🔍 **Smart Search** - Quick filtering and search across all accounts
- 💪 **Password Generator** - Create strong, random passwords
- 📊 **Password Strength Analysis** - Real-time security scoring
- 📱 **Cross-Platform** - Works on Windows, macOS, and Linux
- ☁️ **Cloud Sync** - MongoDB Atlas for secure cloud storage

### User Interface
- 🖥️ **Desktop GUI** - Modern PyQt6 interface
- 🌐 **Web Interface** - Flask-based web application
- 💻 **CLI** - Command-line interface for power users
- 🎨 **Dark/Light Themes** - Customizable appearance

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Architecture](#architecture)
- [Security](#security)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- MongoDB Atlas account (free tier available)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/PPW.git
cd PPW
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure MongoDB Atlas

1. **Create Free Account**: Visit [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. **Create Cluster**: Choose M0 free tier (512MB)
3. **Database Access**: Create user with read/write permissions
4. **Network Access**: Whitelist your IP (or 0.0.0.0/0 for development)
5. **Get Connection String**: 
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/
   ```

### Step 5: Environment Configuration

Create a `.env` file:
```bash
cp .env.example .env
```

Edit `.env` with your details:
```env
MONGO_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/
DATABASE_NAME=password_manager
SECRET_KEY=your-secret-key-here
SESSION_TIMEOUT_MINUTES=15
```

### Step 6: Initialize Database
```bash
python -c "from db.database import db_manager; db_manager.connect(); db_manager.initialize_collections(); print('✓ Database initialized')"
```

## 🎯 Quick Start

### CLI Interface
```bash
python main.py
```

### Desktop GUI (Recommended)
```bash
python gui_app.py
```

### Web Interface
```bash
python web_app.py
# Open browser: http://localhost:5000
```

### First Time Setup
1. Launch the application
2. Create your master password (minimum 12 characters)
3. Add your first account
4. Start securing your passwords!

## 📖 Usage

### Creating Master Password
```bash
# CLI
python main.py
> Select: 1. Create Master Password
> Enter username, password, and optional email

# GUI
Click "Create Account" → Fill form → Submit
```

### Adding Accounts
```bash
# CLI
python main.py → Login → 1. Add new account

# GUI
File → New Account (Ctrl+N)
```

### Generating Strong Passwords
```bash
# CLI
python main.py → Login → 5. Generate password

# GUI
Tools → Password Generator (Ctrl+G)
```

### Searching Accounts
```bash
# CLI
python main.py → Login → 3. Search accounts

# GUI
Use search bar or Ctrl+F
```

## 🏗️ Architecture

### Project Structure
```
PPW/
├── main.py                      # CLI application
├── gui_app.py                   # Desktop GUI (PyQt6)
├── web_app.py                   # Web interface (Flask)
├── config.py                    # Configuration settings
├── requirements.txt             # Python dependencies
│
├── api/                         # API Layer
│   ├── __init__.py
│   ├── routes.py               # API endpoints
│   ├── middleware.py           # Authentication & security
│   └── validators.py           # Input validation
│
├── controllers/                 # Business Logic Controllers
│   ├── __init__.py
│   ├── auth_controller.py      # Authentication logic
│   ├── account_controller.py   # Account management
│   └── security_controller.py  # Security operations
│
├── db/                         # Database Layer
│   ├── __init__.py
│   ├── database.py            # MongoDB connection
│   └── schemas.py             # Data schemas
│
├── services/                   # Service Layer
│   ├── __init__.py
│   ├── master_password_service.py
│   └── account_service.py
│
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── encryption.py          # Encryption utilities
│   ├── logger.py              # Activity logging
│   ├── validators.py          # Input validation
│   └── security.py            # Security helpers
│
├── gui/                        # GUI Components
│   ├── __init__.py
│   ├── main_window.py         # Main window
│   ├── dialogs.py             # Dialog windows
│   └── widgets.py             # Custom widgets
│
└── static/                     # Web assets
    ├── css/
    ├── js/
    └── img/
```

### Database Schema

#### Collections

**master_password**
```json
{
  "user_id": "uuid",
  "username": "string",
  "password_hash": "string (PBKDF2)",
  "salt": "string",
  "encryption_key_encrypted": "string (AES-256)",
  "failed_attempts": "int",
  "locked_until": "datetime",
  "created_at": "datetime",
  "last_login": "datetime",
  "email": "string"
}
```

**accounts**
```json
{
  "account_id": "uuid",
  "user_id": "uuid",
  "title": "string",
  "username": "string",
  "password_encrypted": "string (AES-256-GCM)",
  "url": "string",
  "category": "string",
  "notes_encrypted": "string",
  "tags": ["array"],
  "favorite": "boolean",
  "strength_score": "int (0-100)",
  "two_factor_enabled": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime",
  "last_accessed": "datetime"
}
```

**activity_logs**
```json
{
  "log_id": "uuid",
  "user_id": "uuid",
  "action_type": "string",
  "status": "string",
  "ip_address": "string",
  "timestamp": "datetime",
  "details": "string"
}
```

## 🔒 Security

### Encryption Architecture

```
Master Password (User Input)
    ↓
PBKDF2 (100,000 iterations) + Unique Salt
    ↓
Master Key (never stored)
    ↓
Encrypts → Main Encryption Key (AES-256)
    ↓
Main Encryption Key (stored encrypted)
    ↓
Decrypts → Account Passwords (AES-256-GCM)
```

### Security Features

#### 1. Password Security
- **PBKDF2-HMAC-SHA256**: 100,000 iterations
- **Unique Salt**: Per-user salt generation
- **AES-256-GCM**: Authenticated encryption
- **Zero-Knowledge**: Server never sees plaintext passwords

#### 2. Authentication Security
- **Account Lockout**: 5 failed attempts = 30-minute lockout
- **Session Management**: Automatic timeout after inactivity
- **Secure Tokens**: Cryptographically secure session tokens
- **Brute-Force Protection**: Rate limiting on login attempts

#### 3. Data Protection
- **Encryption at Rest**: All passwords encrypted in database
- **Encryption in Transit**: TLS/SSL for all connections
- **Secure Memory**: Sensitive data cleared after use
- **Activity Logging**: Complete audit trail

#### 4. Application Security
- **Input Validation**: All inputs sanitized and validated
- **SQL Injection Protection**: Parameterized queries (MongoDB)
- **XSS Protection**: Output encoding in web interface
- **CSRF Protection**: Token-based CSRF prevention
- **Secure Dependencies**: Regular security updates

### Security Best Practices

✅ **DO:**
- Use a strong master password (16+ characters, mixed case, numbers, symbols)
- Enable two-factor authentication on MongoDB Atlas
- Keep your `.env` file private (never commit to Git)
- Regularly update dependencies
- Review activity logs for suspicious activity
- Backup your database regularly
- Use HTTPS in production
- Set strong session timeouts

❌ **DON'T:**
- Share your master password
- Use simple or dictionary words
- Reuse passwords across accounts
- Disable security features
- Expose your connection string
- Use default configurations in production
- Store sensitive data in logs

## 📡 API Documentation

### Authentication Endpoints

#### POST `/api/auth/register`
Create new user account
```json
{
  "username": "john_doe",
  "password": "secure_password",
  "email": "john@example.com"
}
```

#### POST `/api/auth/login`
Authenticate user
```json
{
  "username": "john_doe",
  "password": "secure_password"
}
```

### Account Endpoints

#### GET `/api/accounts`
Get all accounts for authenticated user

#### POST `/api/accounts`
Create new account
```json
{
  "title": "Gmail",
  "username": "john@gmail.com",
  "password": "account_password",
  "url": "https://gmail.com",
  "category": "Email"
}
```

#### GET `/api/accounts/{account_id}`
Get specific account

#### PUT `/api/accounts/{account_id}`
Update account

#### DELETE `/api/accounts/{account_id}`
Delete account

#### GET `/api/accounts/{account_id}/password`
Get decrypted password

### Utility Endpoints

#### POST `/api/password/generate`
Generate strong password
```json
{
  "length": 16,
  "use_symbols": true,
  "use_numbers": true,
  "use_uppercase": true,
  "use_lowercase": true
}
```

#### POST `/api/password/strength`
Check password strength
```json
{
  "password": "test_password"
}
```

## 🧪 Testing

### Run Tests
```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# Security tests
python -m pytest tests/security/

# Coverage report
python -m pytest --cov=. --cov-report=html
```

### Manual Testing
```bash
# Test database connection
python -c "from db.database import db_manager; db_manager.connect() and print('✓ Connected')"

# Test encryption
python -c "from utils.encryption import PasswordGenerator; print(PasswordGenerator.generate_password(16))"

# Test services
python -c "from services.master_password_service import MasterPasswordService; print('✓ Services loaded')"
```

## 🔧 Configuration

### Environment Variables
```env
# MongoDB Configuration
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/
DATABASE_NAME=password_manager

# Security Settings
SECRET_KEY=your-secret-key-min-32-chars
SESSION_TIMEOUT_MINUTES=15
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
PBKDF2_ITERATIONS=100000

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Customization
Edit `config.py` to customize:
- Password requirements
- Session timeouts
- Lockout settings
- Encryption parameters

## 🐛 Troubleshooting

### Connection Issues
```bash
# Test MongoDB connection
python -c "from pymongo import MongoClient; client = MongoClient('your-uri'); client.admin.command('ping')"

# Check network access in MongoDB Atlas
# Security → Network Access → Verify IP whitelist
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -r {} +
```

### Database Errors
```bash
# Reset database (WARNING: Deletes all data)
python -c "from db.database import db_manager; db_manager.connect(); db_manager.db.drop_database('password_manager')"

# Reinitialize
python -c "from db.database import db_manager; db_manager.connect(); db_manager.initialize_collections()"
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Coding Standards
- Follow PEP 8 style guide
- Add docstrings to all functions
- Include unit tests for new features
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This password manager is provided "as is" for educational and personal use. While we follow security best practices:

- Use at your own risk
- Always maintain backups
- Review code before storing sensitive data
- Keep dependencies updated
- Report security issues responsibly

## 🙏 Acknowledgments

- [cryptography](https://cryptography.io/) - Encryption library
- [PyMongo](https://pymongo.readthedocs.io/) - MongoDB driver
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) - Cloud database

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/PPW/issues)
- **Security**: Report vulnerabilities privately to security@yourproject.com
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/PPW/discussions)

## 🗺️ Roadmap

- [ ] Browser extension
- [ ] Mobile apps (iOS/Android)
- [ ] Password sharing with encryption
- [ ] Biometric authentication
- [ ] Hardware key support (YubiKey)
- [ ] Breach detection API integration
- [ ] Password history tracking
- [ ] Secure file attachments
- [ ] Team/family sharing
- [ ] Import from other password managers

---

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by the PPW Team

