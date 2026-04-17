# QwebsiteAutomationBot - Architecture & Workflow Documentation

> **Version 2.4.0** | Last Updated: 2026-01-23

## 📊 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              QwebsiteAutomationBot v2.4                                      │
│                                                                                              │
│  ┌─────────────┐                                                                            │
│  │  task.py    │ ◄─── Entry Point (Robocorp Task)                                           │
│  └──────┬──────┘                                                                            │
│         │                                                                                    │
│         ▼                                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐      │
│  │                    workflow/process.py (outside src/)                              │      │
│  │                      (Main Process Orchestrator)                                   │      │
│  │  ┌──────────────────────────────────────────────────────────────────────────────┐ │      │
│  │  │  1. Initialize Configuration & Bitwarden                                     │ │      │
│  │  │  2. Run UpdatePaymentProcess (if enabled)                                     │ │      │
│  │  │  3. Run OrderManagementProcess (if enabled)                                   │ │      │
│  │  │  4. Run UserManagementProcess (if enabled)                                    │ │      │
│  │  │  5. Run AdvertisementManagementProcess (if enabled)                           │ │      │
│  │  │  6. Run SignupIDManagementProcess (if enabled)                                │ │      │
│  │  │  7. Run DataAnalysisProcess (includes BusinessReport!)                        │ │      │
│  │  │  8. Generate Workflow HTML Report (10 tabs)                                   │ │      │
│  │  └──────────────────────────────────────────────────────────────────────────────┘ │      │
│  └──────────────────────────────────────┬───────────────────────────────────────────┘      │
│                                         │                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐     │
│  │                    src/processes/ (All Process Modules)                            │     │
│  │                                                                                    │     │
│  │   ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐          │     │
│  │   │  payment/ │ │   order/  │ │   user/   │ │advertise- │ │  signup/  │          │     │
│  │   │           │ │           │ │           │ │   ment/   │ │           │          │     │
│  │   │UpdatePay- │ │OrderMgmt- │ │UserMgmt-  │ │ AdMgmt-   │ │SignupID-  │          │     │
│  │   │  ment     │ │  Process  │ │  Process  │ │  Process  │ │ MgmtProc  │          │     │
│  │   └───────────┘ └─────┬─────┘ └───────────┘ └───────────┘ └───────────┘          │     │
│  │                       │                                                           │     │
│  │                       ▼                                                           │     │
│  │                ┌─────────────┐                                                    │     │
│  │                │OrderManager │ ◄── Calculates Doctor Debts                        │     │
│  │                │ ┌─────────┐ │                                                    │     │
│  │                │ │APIHndlr │ │                                                    │     │
│  │                │ │SheetHndl│ │                                                    │     │
│  │                │ │Comparatr│ │                                                    │     │
│  │                │ └─────────┘ │                                                    │     │
│  │                └─────────────┘                                                    │     │
│  │                                                                                    │     │
│  │   ┌───────────────────────────────────────────────────────────────────────┐       │     │
│  │   │            data_analysis/ + business_report/                           │       │     │
│  │   │                                                                        │       │     │
│  │   │  DataAnalysisProcess ─────► BusinessReportProcess (auto-runs inside)  │       │     │
│  │   │         │                            │                                 │       │     │
│  │   │         │                            ▼                                 │       │     │
│  │   │         │                   ┌────────────────┐                         │       │     │
│  │   │         │                   │  Analyzers     │                         │       │     │
│  │   │         │                   │ ┌──────┬─────┐ │                         │       │     │
│  │   │         │                   │ │User  │Order│ │                         │       │     │
│  │   │         │                   │ │Paymt │Rsrch│ │                         │       │     │
│  │   │         │                   │ │Ads   │Financ│                         │       │     │
│  │   │         │                   │ │BusKPI│      │                         │       │     │
│  │   │         │                   │ └──────┴─────┘ │                         │       │     │
│  │   │         │                   └────────────────┘                         │       │     │
│  │   │         │                            │                                 │       │     │
│  │   │         │                            ▼                                 │       │     │
│  │   │         │                   ┌────────────────┐                         │       │     │
│  │   │         │                   │  Analytics     │                         │       │     │
│  │   │         │                   │ ┌──────┬─────┐ │                         │       │     │
│  │   │         │                   │ │Trend │Anom-│ │                         │       │     │
│  │   │         │                   │ │Anlyzr│Detec│ │                         │       │     │
│  │   │         │                   │ │Forec │Compr│ │                         │       │     │
│  │   │         │                   │ └──────┴─────┘ │                         │       │     │
│  │   │         │                   └────────────────┘                         │       │     │
│  │   │         │                            │                                 │       │     │
│  │   │         │                            ▼                                 │       │     │
│  │   │         │                   ┌────────────────┐                         │       │     │
│  │   │         │                   │data_persistence│◄── SQLite DB            │       │     │
│  │   │         │                   │ (Metrics Store)│                         │       │     │
│  │   │         │                   └────────────────┘                         │       │     │
│  │   │         ▼                            │                                 │       │     │
│  │   │   Export ZIP                         ▼                                 │       │     │
│  │   │   (50+ CSVs)              Business Report HTML                        │       │     │
│  │   └───────────────────────────────────────────────────────────────────────┘       │     │
│  └───────────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐     │
│  │                    src/libraries/ (Shared Components)                              │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                 │     │
│  │  │QWebsite  │ │ Google   │ │ Google   │ │ Report   │ │Bitwarden │                 │     │
│  │  │   API    │ │ Sheets   │ │  Drive   │ │Generator │ │Credential│                 │     │
│  │  │          │ │   API    │ │   API    │ │ (10 tabs)│ │ Manager  │                 │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘                 │     │
│  └───────────────────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │         External Services           │
                    │  ┌─────────┐  ┌─────────┐  ┌──────┐│
                    │  │Q Website│  │ Google  │  │Gmail ││
                    │  │   API   │  │  APIs   │  │ IMAP ││
                    │  │(Railway)│  │(Sheets+ │  │(OTP) ││
                    │  │         │  │ Drive)  │  │      ││
                    │  └─────────┘  └─────────┘  └──────┘│
                    └─────────────────────────────────────┘
```

---

## 📁 Project Structure (v2.4.0)

```
qwebsiteautomationbot/
├── task.py                              # 🚀 Entry point
│
├── workflow/                            # 🔄 Orchestration (outside src/)
│   └── process.py                       # Main Process class
│
├── src/
│   ├── config.py                        # ⚙️ Configuration
│   │
│   ├── processes/                       # 📦 ALL PROCESS MODULES
│   │   ├── __init__.py                  # Exports all processes
│   │   │
│   │   ├── order/                       # Order Management
│   │   │   ├── __init__.py
│   │   │   ├── order_management_process.py
│   │   │   ├── order_manager.py         # + Doctor Debt calculation
│   │   │   ├── api_handler.py
│   │   │   ├── sheet_handler.py
│   │   │   └── comparator.py
│   │   │
│   │   ├── payment/                     # Payment Updates
│   │   │   ├── __init__.py
│   │   │   └── update_payment_process.py
│   │   │
│   │   ├── user/                        # User Management
│   │   │   ├── __init__.py
│   │   │   ├── user_management_process.py
│   │   │   └── user_manager.py
│   │   │
│   │   ├── advertisement/               # Advertisement Management
│   │   │   ├── __init__.py
│   │   │   ├── advertisement_management_process.py
│   │   │   └── advertisement_manager.py
│   │   │
│   │   ├── signup/                      # Signup ID Management
│   │   │   ├── __init__.py
│   │   │   ├── signup_id_management_process.py
│   │   │   └── signup_id_manager.py
│   │   │
│   │   ├── data_analysis/               # Data Export (+ BusinessReport!)
│   │   │   ├── __init__.py
│   │   │   ├── data_analysis_process.py
│   │   │   └── data_analysis_manager.py # Runs BusinessReport automatically
│   │   │
│   │   └── business_report/             # Business Intelligence
│   │       ├── __init__.py
│   │       ├── business_report_process.py
│   │       ├── data_loader.py
│   │       ├── report_builder.py
│   │       ├── financial_sheet_setup.py
│   │       ├── financial_tracking_loader.py
│   │       ├── data_persistence/        # SQLite storage
│   │       ├── analytics/               # Trend/Anomaly/Forecast
│   │       └── analyzers/               # Domain analyzers
│   │
│   ├── libraries/                       # 📚 Shared libraries
│   ├── bitwarden/                       # 🔐 Credential management
│   └── models/                          # 📋 Data models
│
├── tests/                               # 🧪 Unit tests
├── output/                              # 📊 Generated outputs
├── devdata/                             # Development data
│
├── pyproject.toml                       # 📦 Project configuration
├── robot.yaml                           # 🤖 Robocorp config
├── conda.yaml                           # 🐍 Conda environment
└── .pre-commit-config.yaml              # ✅ Code quality hooks
```

---

## 🔄 Main Workflow (v2.4.0)

```
                              ┌─────────┐
                              │  START  │
                              └────┬────┘
                                   │
                                   ▼
                         ┌─────────────────┐
                         │ Initialize      │
                         │ Bitwarden +     │
                         │ Configuration   │
                         └────────┬────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐      ┌───────────────┐        ┌───────────────┐
│ 1. Payment    │      │ 2. Order      │        │ 3. User       │
│    Update     │      │    Management │        │    Management │
│               │      │               │        │               │
│ • Update IDs  │      │ • Fetch API   │        │ • Fetch Users │
│   to 'paid'   │      │ • Compare     │        │ • Auto-Approve│
│               │      │ • Update API  │        │   Pending     │
└───────────────┘      │ • Doctor Debts│        └───────────────┘
                       └───────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐      ┌───────────────┐        ┌───────────────┐
│ 4. Advertise- │      │ 5. Signup ID  │        │ 6. Data       │
│    ment Mgmt  │      │    Management │        │    Analysis   │
│               │      │               │        │               │
│ • Update Paid │      │ • Fetch IDs   │        │ • Export Job  │
│ • Approve Ads │      │ • Usage Stats │        │ • Download    │
│ • Update Sheet│      │ • Emergency ⚠ │        │ • BusinessRpt │◄── Auto!
└───────────────┘      └───────────────┘        └───────────────┘
                                  │
                                  ▼
                    ┌───────────────────────┐
                    │ 7. Generate Workflow  │
                    │    Report (HTML)      │
                    │    ─────────────────  │
                    │    10 Tabbed Sections │
                    │    + Doctor Debts     │
                    │    + Financial Track  │
                    │    + Trends/Forecast  │
                    └───────────┬───────────┘
                                │
                                ▼
                           ┌────────┐
                           │  END   │
                           └────────┘
```

---

## 📦 Import Reference (v2.4.0)

```python
# ✅ NEW IMPORT STYLE (v2.4.0+)
from processes.order import OrderManagementProcess
from processes.payment import UpdatePaymentProcess
from processes.user import UserManagementProcess
from processes.advertisement import AdvertisementManagementProcess
from processes.signup import SignupIDManagementProcess
from processes.data_analysis import DataAnalysisProcess  # Includes BusinessReport!
from processes.business_report import BusinessReportProcess

# ❌ OLD IMPORT STYLE (deprecated)
# from orderManagement import OrderManagementProcess
# from UpdatePaymentSheet import UpdatePaymentProcess
# from BusinessReport import BusinessReportProcess
```

---

## 📊 HTML Report Structure (10 Tabs)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      QwebsiteAutomationBot Report                        │
├─────────────────────────────────────────────────────────────────────────┤
│  [📦 Orders] [💳 Payment] [👥 Users] [📺 Ads] [🎟️ SignupIDs]            │
│  [📊 Data] [📈 KPIs] [💹 Tracking] [📈 Trends] [🔮 Forecast]            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📦 ORDER MANAGEMENT                                                    │
│  ├── Status Breakdown (Pending/Paid/Completed)                         │
│  ├── Duplicate Removal Summary                                          │
│  ├── New Orders Added                                                   │
│  ├── Orders Updated to Completed                                        │
│  └── 💰 DOCTOR DEBTS (Expandable!)                                      │
│      └── Click doctor → See all pending orders                          │
│                                                                         │
│  📊 BUSINESS KPIs                                                       │
│  ├── KPI Cards with Trend Indicators (📈📉➡️)                           │
│  ├── Revenue Trajectory Chart                                           │
│  ├── Product Performance (per-product trajectories)                    │
│  └── Growth Metrics (DoD, WoW, MoM)                                    │
│                                                                         │
│  💹 FINANCIAL TRACKING                                                  │
│  ├── 💰 Capital Flow Trajectory                                        │
│  │   └── Investment vs Retrieved vs Capital vs Outstanding             │
│  ├── 🎯 Goal Progress Tracker                                          │
│  │   └── 6 Goals with Progress Bars                                    │
│  └── 📈 Financial Trajectory: Actual vs Target                         │
│                                                                         │
│  📈 HISTORICAL TRENDS                                                   │
│  ├── Growth Rates (DoD, WoW, MoM)                                      │
│  ├── Trend Direction Indicators                                         │
│  ├── Top Revenue Days                                                   │
│  └── Seasonal Patterns                                                  │
│                                                                         │
│  🔮 FORECAST & PREDICTIONS                                              │
│  ├── Revenue Trajectory (Actual vs Forecast vs Target)                 │
│  ├── 7-Day Predictions                                                  │
│  ├── Confidence Intervals (85%)                                        │
│  └── Risk Indicators                                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration Files

### pyproject.toml (v2.4.0)

```toml
[project]
name = "qwebsite-automation-bot"
version = "2.4.0"
requires-python = ">=3.11,<3.13"

dependencies = [
    "robocorp-tasks>=3.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.8.1",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "cryptography>=41.0.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "scikit-learn>=1.3.0",
    "statsmodels>=0.14.0",
]

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "W", "B", "C4", "UP", "SIM", "TCH", "RUF"]
```

### robot.yaml Tasks

```yaml
tasks:
  QWebsite Automation:        # Main task - runs all enabled processes
  Order Management:           # Individual: Order management only
  Payment Update:             # Individual: Payment updates only
  User Management:            # Individual: User management only
  Advertisement Management:   # Individual: Ad management only
  Data Analysis:              # Individual: Data export + Business Report
```

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| **2.4.0** | **2026-01-23** | **Project Restructure**: All processes moved to `src/processes/`, BusinessReport auto-runs inside DataAnalysis, cleaner import paths |
| 2.3.0 | 2026-01-23 | Financial Trajectories: Capital flow charts, goal progress tracker, actual vs target visualization |
| 2.2.0 | 2026-01-23 | Historical Analytics: SQLite persistence, TrendAnalyzer, AnomalyDetector, ForecastEngine |
| 2.1.0 | 2026-01-23 | Financial Tracking: 95-column Google Sheet, Business KPIs tab |
| 2.0.0 | 2026-01-23 | Business Report module: 8-tab HTML dashboard, Chart.js |
| 1.0.0 | 2026-01-22 | Initial release: Order management, Payment updates |

---

## 📄 License

Proprietary - All rights reserved.
