# AestheticRxNetworkIntelligentBot 🤖

A comprehensive automation bot for managing AestheticRxNetwork operations with Google Sheets integration, business intelligence reporting, and financial tracking.

## 🚀 Features

- **Order Management**: Fetch, compare, and update orders between AestheticRxNetwork API and Google Sheets
- **Payment Processing**: Update payment statuses in bulk with revenue tracking
- **User Management**: Auto-approve pending user registrations
- **Advertisement Management**: Manage and approve video advertisements
- **Signup ID Management**: Monitor signup ID usage with emergency alerts when running low
- **Data Export & Analysis**: Export platform data and generate comprehensive business reports
- **Business Intelligence Dashboard**: Interactive HTML reports with 10 tabbed sections and Chart.js visualizations
- **Historical Analytics**: SQLite-based metrics persistence with trend analysis, anomaly detection, and forecasting
- **Financial Tracking**: 95-column Google Sheet integration with capital flow trajectories and goal tracking
- **Doctor Debt Tracking**: Expandable debt view per doctor with pending order details
- **Google Integration**: Full Google Sheets and Drive API support (including Shared Drives)
- **Credential Security**: Bitwarden integration for secure credential management
- **HTML Reports**: Beautiful, detailed workflow execution reports with tabbed interface
- **Duplicate Detection**: Automatic detection and removal of duplicate orders

## 📁 Project Structure

```text
AestheticRxNetworkIntelligentBot/
├── task.py                              # 🚀 Entry point (Robocorp task)
│
├── workflow/                            # 🔄 Main orchestration layer
│   └── process.py                       # Main Process class
│
├── src/
│   ├── config.py                        # ⚙️ Application configuration
│   │
│   ├── processes/                       # 📦 All automation processes
│   │   ├── __init__.py                  # Process exports
│   │   │
│   │   ├── order/                       # 📦 Order management
│   │   │   ├── order_management_process.py
│   │   │   ├── order_manager.py
│   │   │   ├── sheet_handler.py
│   │   │   ├── api_handler.py
│   │   │   └── comparator.py
│   │   │
│   │   ├── payment/                     # 💳 Payment updates
│   │   │   └── update_payment_process.py
│   │   │
│   │   ├── user/                        # 👤 User management
│   │   │   ├── user_management_process.py
│   │   │   └── user_manager.py
│   │   │
│   │   ├── advertisement/               # 📺 Advertisement management
│   │   │   ├── advertisement_management_process.py
│   │   │   └── advertisement_manager.py
│   │   │
│   │   ├── signup/                      # 🎟️ Signup ID management
│   │   │   ├── signup_id_management_process.py
│   │   │   └── signup_id_manager.py
│   │   │
│   │   ├── data_analysis/               # 📊 Data export & analysis
│   │   │   ├── data_analysis_process.py
│   │   │   └── data_analysis_manager.py # Includes BusinessReport!
│   │   │
│   │   └── business_report/             # 📈 Business intelligence
│   │       ├── business_report_process.py
│   │       ├── data_loader.py
│   │       ├── report_builder.py
│   │       ├── financial_sheet_setup.py
│   │       ├── financial_tracking_loader.py
│   │       ├── data_persistence/        # SQLite storage
│   │       │   ├── schema.py
│   │       │   ├── metrics_storage.py
│   │       │   ├── historical_loader.py
│   │       │   └── mock_data_generator.py
│   │       ├── analytics/               # Advanced analytics
│   │       │   ├── trend_analyzer.py
│   │       │   ├── comparative_analyzer.py
│   │       │   ├── anomaly_detector.py
│   │       │   └── forecast_engine.py
│   │       └── analyzers/               # Domain analyzers
│   │           ├── user_analyzer.py
│   │           ├── order_analyzer.py
│   │           ├── payment_analyzer.py
│   │           ├── research_analyzer.py
│   │           ├── advertisement_analyzer.py
│   │           ├── financial_analyzer.py
│   │           └── business_kpi_analyzer.py
│   │
│   ├── libraries/                       # 📚 Shared libraries
│   │   ├── credentials.py
│   │   ├── google_sheets.py
│   │   ├── google_drive.py              # Shared Drive support
│   │   ├── aestheticrxnetwork_api.py
│   │   ├── report_generator.py
│   │   ├── sheet_utils.py
│   │   ├── workitems.py
│   │   └── logger.py
│   │
│   ├── bitwarden/                       # 🔐 Bitwarden integration
│   │   ├── auth.py
│   │   └── credentials.py
│   │
│   ├── models/                          # 📋 Data models
│   │   ├── inputs.py
│   │   └── order.py
│   │
│   └── email_reader.py                  # 📧 Gmail OTP reader
│
├── tests/                               # 🧪 Unit tests
│   ├── conftest.py
│   └── test_*.py
│
├── 12_Financial_Tracking/               # 📊 Financial tracking templates
│   ├── Q_Financial_Tracking.csv
│   ├── Q_Complete_Structure_Summary.md
│   └── Q_CSV_Column_Definitions.md
│
├── output/                              # 📊 Generated outputs
│   ├── exports/
│   │   └── extracted_data/
│   └── business_report_*.html
│
├── devdata/                             # 🧪 Development data
│   ├── env.json
│   └── vault.json
│
├── pyproject.toml                       # 📦 Project config & dependencies
├── robot.yaml                           # 🤖 Robocorp configuration
├── conda.yaml                           # 🐍 Conda environment
├── .pre-commit-config.yaml              # ✅ Pre-commit hooks
├── MacroFile.md                         # 📖 Architecture documentation
└── README.md                            # 📖 This file
```

## 🛠️ Setup

### Prerequisites

- Python 3.11 or 3.12
- Bitwarden CLI (optional, for secure credentials)
- pandas, scikit-learn, statsmodels (for analytics)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/AestheticRxNetworkIntelligentBot.git
cd AestheticRxNetworkIntelligentBot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install
```

### Google Sheets Setup

| Sheet | ID | Purpose |
|-------|-----|---------|
| **Orders** | `1wNrE75TQzg4Qkyj0enRvdKw1QSFq1NhU3ZGqbhnzX1E` | Order management |
| **Advertisements** | `1E9eA0XrEv7BqvYUgvLQOlaqw9walZUmC7p8atgh2D_s` | Ad management |
| **Financial Tracking** | `1C4W-25vnzHHROsM-pBIEurK3wGc3HQJGCsPtdM9_-gg` | KPIs & goals |

Share all sheets with: `googledrive@aestheticrxnetwork.iam.gserviceaccount.com` (Editor access)

### Environment Variables

| Variable | Description | Default | GitHub CI |
|----------|-------------|---------|-----------|
| `RUN_UPDATE_PAYMENT_PROCESS` | Enable payment update | `False` | ✅ Works without credentials |
| `PAYMENT_IDS_LIST` | Payment IDs (comma-separated) | `[]` | ✅ Works without credentials |
| `RUN_ORDER_MANAGE_SYSTEM` | Enable order management | `True` | ⚠️ Requires credentials |
| `RUN_USER_MANAGEMENT_PROCESS` | Enable user management | `True` | ⚠️ Requires credentials |
| `RUN_ADVERTISEMENT_MANAGEMENT_PROCESS` | Enable ad management | `True` | ⚠️ Requires credentials |
| `ADVERTISEMENT_PAID_IDS_LIST` | Ad IDs (comma-separated) | `[]` | ✅ Works without credentials |
| `RUN_SIGNUP_ID_MANAGEMENT_PROCESS` | Enable signup ID mgmt | `True` | ⚠️ Requires credentials |
| `RUN_DATA_ANALYSIS_PROCESS` | Enable data export | `True` | ⚠️ Requires credentials |
| `RUN_BUSINESS_REPORT_PROCESS` | Enable BI report | `True` | ⚠️ Requires credentials |

#### GitHub Actions Variables (No Credentials Required)

For **tests-only** CI/CD pipelines without external API access:

```bash
RUN_UPDATE_PAYMENT_PROCESS=False          # ✅ Tests pass without AestheticRxNetwork API
RUN_ORDER_MANAGE_SYSTEM=False             # ✅ Tests pass without AestheticRxNetwork API
RUN_USER_MANAGEMENT_PROCESS=False         # ✅ Tests pass without AestheticRxNetwork API
RUN_ADVERTISEMENT_MANAGEMENT_PROCESS=False # ✅ Tests pass without AestheticRxNetwork API
RUN_SIGNUP_ID_MANAGEMENT_PROCESS=False    # ✅ Tests pass without AestheticRxNetwork API
RUN_DATA_ANALYSIS_PROCESS=False           # ✅ Tests pass without Google Sheets API
RUN_BUSINESS_REPORT_PROCESS=False         # ✅ Tests pass without Google Sheets API
```

## 🚀 Usage

### Run the Automation

```bash
# Run with default settings (Order Management only)
python task.py

# Run full business intelligence workflow
export RUN_DATA_ANALYSIS_PROCESS=True
python task.py  # BusinessReport runs automatically inside DataAnalysis!

# Run all processes
export RUN_UPDATE_PAYMENT_PROCESS=True
export RUN_ORDER_MANAGE_SYSTEM=True
export RUN_USER_MANAGEMENT_PROCESS=True
export RUN_ADVERTISEMENT_MANAGEMENT_PROCESS=True
export RUN_SIGNUP_ID_MANAGEMENT_PROCESS=True
export RUN_DATA_ANALYSIS_PROCESS=True
python task.py
```

### Import Processes Directly

```python
# New import style (v2.4.0+)
from processes.order import OrderManagementProcess
from processes.payment import UpdatePaymentProcess
from processes.user import UserManagementProcess
from processes.advertisement import AdvertisementManagementProcess
from processes.signup import SignupIDManagementProcess
from processes.data_analysis import DataAnalysisProcess  # Includes BusinessReport!
from processes.business_report import BusinessReportProcess
```

## 📊 Workflow

### Execution Order

1. **Update Payment Process** - Updates payment IDs to 'paid' status
2. **Order Management Process** - Syncs orders between API and Sheets, calculates doctor debts
3. **User Management Process** - Auto-approves pending users
4. **Advertisement Management Process** - Approves pending ads, updates payment status
5. **Signup ID Management Process** - Monitors signup ID usage with emergency alerts
6. **Data Analysis Process** - Exports platform data + runs Business Report automatically
7. **Workflow Report** - Generates comprehensive HTML report

## 📈 Business Intelligence Dashboard

### 10 Tabbed Sections

| Tab | Description |
|-----|-------------|
| 👥 **Users & Doctors** | Tier distribution, top doctors, approval rates |
| 📦 **Orders** | Status breakdown, products, doctor debts with expandable details |
| 💳 **Payments & Revenue** | Payment status, methods, trends |
| 📄 **Research** | Papers, views, upvotes |
| 📺 **Advertisements** | Ad types, performance |
| 💵 **System** | Wallets, debt, notifications |
| 📊 **Business KPIs** | Revenue trajectories, growth metrics |
| 💹 **Financial Tracking** | Capital flow, goal progress |
| 📈 **Historical Trends** | Growth rates (DoD/WoW/MoM) |
| 🔮 **Forecast & Predictions** | 7-day predictions, confidence intervals |

### Interactive Features

- **KPI Cards** with trend indicators (📈 up, 📉 down, ➡️ flat)
- **Expandable Doctor Debts** - Click to see all pending orders per doctor
- **Trajectory Charts** - Actual vs Forecast vs Target
- **Goal Progress Bars** - Achievement percentages
- **Google Drive Upload** - Automatic upload to Shared Drive

## 🧪 Development

### Testing Architecture

#### Test Status: ✅ **All 167 Tests Passing**

```bash
# Run all tests (no credentials required)
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_order_manager.py -v

# Run with verbose output
pytest -xvs
```

**Why Tests Pass Without Credentials:**

1. **Module Mocking** - All external dependencies are properly mocked:
   - `processes.order.api_handler.AestheticRxNetworkAPI` ✅
   - `processes.order.sheet_handler.GoogleSheetsAPI` ✅
   - `processes.payment.update_payment_process.GoogleSheetsAPI` ✅
   - `processes.user.user_manager.AestheticRxNetworkAPI` ✅

2. **Proper Test Fixtures** - Each test class has fixtures that mock:
   - API handlers
   - Sheet handlers
   - Process classes
   - Report generators

3. **Environment Variable Isolation** - Tests use `monkeypatch` to:
   - Override environment variables per test
   - Isolate module-level state
   - Reload libraries with test configurations

#### Module Import Paths (v2.4.0+)

All processes are now under `src/processes/` with clean imports:

```python
from processes.order import OrderManagementProcess
from processes.payment import UpdatePaymentProcess
from processes.user import UserManagementProcess
from processes.advertisement import AdvertisementManagementProcess
from processes.signup import SignupIDManagementProcess
from processes.data_analysis import DataAnalysisProcess
from processes.business_report import BusinessReportProcess
```

### Running Tests

```bash
pytest                                    # Run all tests (✅ 167 passing)
pytest --cov=src --cov-report=html       # With coverage
pytest tests/test_order_manager.py -v    # Specific file
pytest -xvs tests/test_invoice_manager.py::test_download_drive_file_uses_cache  # Specific test
```

### GitHub Actions CI/CD

The project includes an automated GitHub Actions workflow (`.github/workflows/ci.yml`) that:

1. **Runs on every push and pull request** to `main` and `develop` branches
2. **Executes pre-commit checks** for code quality:
   - Ruff linting and formatting
   - Trailing whitespace removal
   - YAML validation
3. **Runs pytest** with 167 unit tests

#### GitHub Workflow Variables (CI/CD Safe)

The workflow automatically disables processes that require external credentials:

```yaml
env:
  RUN_UPDATE_PAYMENT_PROCESS: "False"          # ✅ No external API
  RUN_ORDER_MANAGE_SYSTEM: "False"             # ⚠️ Needs credentials
  RUN_USER_MANAGEMENT_PROCESS: "False"         # ⚠️ Needs credentials
  RUN_ADVERTISEMENT_MANAGEMENT_PROCESS: "False" # ⚠️ Needs credentials
  RUN_SIGNUP_ID_MANAGEMENT_PROCESS: "False"    # ⚠️ Needs credentials
  RUN_DATA_ANALYSIS_PROCESS: "False"           # ⚠️ Needs credentials
  RUN_BUSINESS_REPORT_PROCESS: "False"         # ⚠️ Needs credentials
```

#### Setting Up GitHub Secrets (For Full Workflow Automation)

To run the full workflow with all processes enabled on GitHub Actions (especially the scheduled automation):

1. Go to **Settings → Secrets and variables → Actions**
2. Add these **secrets**:

| Secret | Value | Purpose |
|--------|-------|---------|
| `AESTHETIC_RX_NETWORK_EMAIL` | Your AestheticRxNetwork email | API authentication |
| `AESTHETIC_RX_NETWORK_PASSWORD` | Your AestheticRxNetwork password | API authentication |
| `AESTHETIC_RX_NETWORK_BASE_URL` | Base URL for AestheticRxNetwork API | API endpoint |
| `AESTHETIC_RX_NETWORK_FRONTEND_URL` | Frontend URL for AestheticRxNetwork | Web interface URL |
| `AESTHETIC_RX_NETWORK_OTP` | OTP code (if required) | Two-factor authentication |
| `API_BASE_URL` | Base URL for additional APIs | API endpoint |
| `GMAIL_EMAIL` or `GMAIL_USER` | Your Gmail address | OTP reading |
| `GMAIL_APP_PASSWORD` or `GMAIL_PASSWORD` | Gmail app password | OTP reading |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google Service Account JSON | Google Sheets/Drive API |
| `GOOGLE_SERVICE_ACCOUNT_EMAIL` | Service account email | Google authentication |
| `GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY` | Service account private key | Google authentication |
| `SLACK_WEBHOOK_URL` | Slack webhook URL | Failure notifications |

3. Add these **variables** (Settings → Secrets and variables → Variables):

| Variable | Default | Purpose |
|----------|---------|---------|
| `GOOGLE_PROJECT_ID` | Your Google Cloud project ID | Google Cloud project |
| `RUN_UPDATE_PAYMENT_PROCESS` | `False` | Enable payment updates |
| `RUN_ORDER_MANAGE_SYSTEM` | `True` | Enable order management |
| `RUN_USER_MANAGEMENT_PROCESS` | `False` | Enable user management |
| `RUN_ADVERTISEMENT_MANAGEMENT_PROCESS` | `False` | Enable ad management |
| `RUN_SIGNUP_ID_MANAGEMENT_PROCESS` | `False` | Enable signup ID management |
| `RUN_DATA_ANALYSIS_PROCESS` | `False` | Enable data analysis |
| `RUN_BUSINESS_REPORT_PROCESS` | `False` | Enable business reports |

4. The scheduled automation workflow (`.github/workflows/scheduled-automation.yml`) will use these secrets and variables to run the bot automatically.
