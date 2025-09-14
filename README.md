# K-Lab Member Management System

A comprehensive member management and payment tracking system for K-Lab, built with Streamlit and Python. This system helps manage member information, track monthly contributions, and automate payment reminders.

## 🚀 Features

### 👥 Member Management
- **Interactive Member Database**: Add, edit, and manage member information
- **Member Categories**: Support for Active (Aktiv), Passive (Passiv), and Inactive (Inaktiv) members
- **Introduction Course Tracking**: Track completion status of required introduction courses
- **Monthly Payment Tracking**: Visual matrix showing payment status for each month
- **Real-time Statistics**: Overview of member counts and payment status

### 💰 Payment Management
- **Automated Payment Calculation**: 
  - Active members: 50 CHF/month
  - Passive members: 25 CHF/month
  - Inactive members: No payments required
- **Payment Status Matrix**: Visual grid showing which members have paid for each month
- **Outstanding Payment Tracking**: Automatic calculation of missing payments
- **Payment History**: Detailed transaction records with dates and references

### 📥 CSV Import System
- **Bank Statement Import**: Import ZKB bank statements directly
- **Smart Auto-Assignment**: Automatically assign transactions to members based on payment details
- **Interactive Data Editor**: Review and modify imported data before processing
- **Duplicate Detection**: Prevents duplicate entries in the database
- **Validation System**: Comprehensive data validation before import

### 📱 Communication Features
- **Telegram Integration**: Send automated payment reminders via Telegram
- **CSV Export**: Export payment reminders for manual processing
- **Customizable Messages**: Personalized reminder messages with payment details
- **Delivery Status Tracking**: Monitor success/failure of message delivery

### 📊 Reporting & Analytics
- **Payment Overview**: Monthly payment statistics and trends
- **Outstanding Payments Report**: Detailed list of members with missing payments
- **Financial Summary**: Total outstanding amounts and member statistics
- **Export Capabilities**: Generate CSV reports for external processing

## 🛠️ Technology Stack

- **Frontend**: Streamlit 1.32.0
- **Backend**: Python 3.11+
- **Data Processing**: Pandas 2.2.0, NumPy 1.26.4
- **Visualization**: Plotly 5.18.0
- **Communication**: python-telegram-bot 20.0+
- **Package Management**: UV (ultra-fast Python package manager)
- **Data Storage**: JSON files
- **Environment**: Virtual environment with UV

## 📋 Prerequisites

- **Python 3.11 or higher** - Required for the application
- **UV package manager** - Ultra-fast Python package manager (install with `pip install uv`)
- **Telegram Bot** (optional, for automated reminders)

### Installing UV
```bash
# Install UV package manager
pip install uv

# Verify installation
uv --version
```

## ⚡ Quick Start

```bash
# 1. Install UV (if not already installed)
pip install uv

# 2. Clone or download the project
git clone <repository-url>
cd buchhaltung

# 3. Set up and run
uv venv
source .venv/bin/activate  # Linux/Mac
uv pip install -r requirements.txt
streamlit run member_management.py
```

## 🚀 Installation

### Option 1: Git Clone (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd buchhaltung
   ```

2. **Create virtual environment and install dependencies using UV**
   ```bash
   uv venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   
   uv pip install -r requirements.txt
   ```

### Option 2: ZIP Download

1. **Download and extract the project**
   - Download the ZIP file from the repository
   - Extract to your desired location
   - Open terminal in the project directory

2. **Create virtual environment and install dependencies using UV**
   ```bash
   uv venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   
   uv pip install -r requirements.txt
   ```

3. **Set up environment variables (optional, for Telegram)**
   ```bash
   # Windows PowerShell
   $env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
   $env:TELEGRAM_CHAT_ID="your_chat_id_here"
   
   # Linux/Mac
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   export TELEGRAM_CHAT_ID="your_chat_id_here"
   ```

4. **Run the application**
   ```bash
   streamlit run member_management.py
   ```

## 📖 Usage

### Starting the Application
```bash
streamlit run member_management.py
```

The application will open in your default web browser at `http://localhost:8501`.

### Managing Members

1. **Add New Members**
   - Click "Mitglied hinzufügen" to expand the form
   - Fill in name, phone, email, and member type
   - Click "Mitglied hinzufügen" to save

2. **Edit Member Information**
   - Use the interactive table to modify member details
   - Change member type, introduction course status, or payment status
   - Click "Änderungen speichern" to save changes

3. **Track Payments**
   - Use checkboxes in the monthly columns to mark payments
   - The system automatically calculates amounts based on member type
   - View outstanding payments in the summary section

### Importing Bank Statements

1. **Prepare CSV File**
   - Export bank statement in ZKB format (semicolon-separated)
   - Ensure columns include: Datum, Gutschrift CHF, Details, Zahlungszweck

2. **Import Process**
   - Go to "CSV Import" tab
   - Upload your CSV file
   - Review and assign transactions to members
   - Select appropriate month for each payment
   - Click "Daten in die Matrix übertragen" to import

3. **Auto-Assignment**
   - The system learns from your assignments
   - Future imports will automatically suggest member assignments
   - Add new mappings in the categories.json file

### Sending Payment Reminders

1. **Telegram Reminders**
   - Ensure Telegram bot is configured (see TELEGRAM_SETUP.md)
   - Click "Telegram Erinnerungen senden"
   - Review delivery status in the results

2. **CSV Export**
   - Click "CSV Export" to generate a reminder file
   - Use the exported CSV for manual processing
   - File includes member details and personalized messages

## 📁 Project Structure

```
buchhaltung/
├── member_management.py          # Main Streamlit application
├── csv_import_manager.py         # CSV import functionality
├── telegram_reminder.py          # Telegram bot integration
├── telegram_config.py            # Telegram configuration
├── payment_reminder_export.py    # CSV export functionality
├── test_csv_import.py            # Test file for CSV import
├── k-lab_member_database.json    # Member database (auto-generated)
├── categories.json               # Member mapping rules (auto-generated)
├── pyproject.toml               # Project configuration with dependencies
├── requirements.txt             # Python dependencies (backup)
├── uv.lock                      # UV lockfile for exact versions
├── TELEGRAM_SETUP.md           # Telegram setup instructions
├── .gitignore                  # Git ignore rules
├── .python-version             # Python version specification
└── README.md                   # This file
```

### 📦 Distribution Files
- `buchhaltung_project.zip` - Complete project package for non-Git distribution

## 🔧 Configuration

### Telegram Bot Setup
See `TELEGRAM_SETUP.md` for detailed instructions on setting up Telegram integration.

### Member Mappings
The system automatically learns member assignments from CSV imports. You can manually edit `categories.json` to add or modify mappings.

### Database Files
- `k-lab_member_database.json`: Main member database
- `categories.json`: Auto-assignment rules for CSV import
- Log files: `member_management.log`, `csv_import.log`

## 🐛 Troubleshooting

### Common Issues

1. **Virtual Environment Issues**
   - **Problem**: `source .venv/bin/activate` not working
   - **Solution**: Ensure you're using the correct path (`.venv/Scripts/activate` on Windows)
   - **Alternative**: Recreate with `uv venv` if corrupted

2. **UV Package Manager Issues**
   - **Problem**: `uv` command not found
   - **Solution**: Install UV with `pip install uv`
   - **Problem**: Dependencies not installing
   - **Solution**: Use `uv pip install -r requirements.txt` instead of `uv sync`

3. **"Telegram Bot nicht konfiguriert"**
   - Check environment variables are set correctly
   - Verify bot token and chat ID

4. **CSV Import Errors**
   - Ensure CSV is in correct ZKB format
   - Check file encoding (should be UTF-8)
   - Verify all required columns are present

5. **Member Not Found in Dropdown**
   - Ensure member exists in database
   - Check for typos in member name
   - Refresh the page after adding new members

6. **Payment Status Not Updating**
   - Click "Änderungen speichern" after making changes
   - Check if member type is set correctly
   - Verify payment amount matches member type

### Log Files
Check the following log files for detailed error information:
- `member_management.log`: General application logs
- `csv_import.log`: CSV import specific logs

### Environment Issues
- **Cross-platform compatibility**: If virtual environment was created on different OS, recreate it
- **Python version**: Ensure Python 3.11+ is installed
- **UV installation**: Verify UV is properly installed and accessible

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section above
- Review log files for error details
- Create an issue in the repository

## 🔄 Version History

- **v0.1.0**: Initial release with basic member management and CSV import functionality
  - Features: Member database, payment tracking, CSV import, Telegram integration, reporting
  - Technology: Streamlit, Pandas, Plotly, python-telegram-bot
  - Package Management: UV for fast dependency management
  - Distribution: Both Git and ZIP download options available

---

**Note**: This system is designed specifically for K-Lab's member management needs. Adapt the payment amounts and member types as needed for your organization.