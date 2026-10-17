# ⚡ SkillSight

> **Automated Data Pipeline & Analytics Dashboard for Software Engineering Job Market Trends**

SkillSight continuously monitors and visualizes live trends in the software engineering job market. It automatically extracts daily job postings from public APIs (such as Arbeitnow), cleans and normalizes the data with **Pandas**, scans job descriptions for high-demand technical skills, loads aggregated time-series metrics into a **MySQL** database, and serves an interactive web dashboard with **Django** and **Chart.js**.

---

## 📋 Table of Contents
- [Architecture & Data Flow](#architecture--data-flow)
- [Tech Stack](#tech-stack)
- [Key Features & User Stories](#key-features--user-stories)
- [Project Directory Structure](#project-directory-structure)
- [Quick Start Guide (Local Setup)](#quick-start-guide-local-setup)
- [Running the ETL Pipeline](#running-the-etl-pipeline)
- [Apache Airflow Orchestration](#apache-airflow-orchestration)
- [MySQL Database Setup](#mysql-database-setup)
- [Docker Compose Deployment](#docker-compose-deployment)
- [REST API Reference](#rest-api-reference)
- [Running Tests](#running-tests)

---

## 🏛️ Architecture & Data Flow

```mermaid
flowchart LR
    A["Public Job APIs\n(Arbeitnow / Adzuna)"] -->|Extract (Daily 00:00 UTC)| B["ETL Engine (Python & Pandas)\nText Cleaning & Keyword Extraction"]
    B -->|Transform & Aggregate| C[("MySQL Database\nOptimized Aggregates")]
    D["Apache Airflow\nDAG Scheduler & Monitor"] -.->|Orchestrates| B
    C -->|Sub-1.5s Queries| E["Django REST Framework\nAnalytics APIs"]
    E -->|JSON Responses| F["Interactive UI\n(Chart.js, HTML5 & CSS3)"]
```

The system operates across four distinct automated phases:
1. **Extract:** Triggered daily at midnight UTC via Apache Airflow, Python queries public job APIs (such as Arbeitnow) to retrieve the latest postings in JSON.
2. **Transform:** Pandas parses the payload, strips HTML, normalizes text, and matches technical skill taxonomy using regex with word boundary checks.
3. **Load:** Normalized postings and precomputed daily aggregate metrics are atomically committed to MySQL.
4. **Visualize:** The Django dashboard queries optimized aggregate tables to render interactive trend charts in under 1.5 seconds.

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Workflow Orchestration** | **Apache Airflow** | Schedules and monitors daily automated ETL DAGs (`0 0 * * *`) |
| **Data Processing** | **Python 3 & Pandas** | API extraction, text normalization, regex skill extraction |
| **Database** | **MySQL** (with SQLite fallback) | Stores historical job postings, skills taxonomy, and daily aggregates |
| **Backend Framework** | **Django & Django REST Framework** | High-performance REST APIs and web controllers |
| **Frontend UI** | **HTML5 & Modern CSS3** | Responsive dark-mode dashboard layout |
| **Data Visualization** | **JavaScript & Chart.js** | Interactive bar charts, 30-day multi-line trend lines, and doughnut charts |
| **Containerization** | **Docker & Docker Compose** | Multi-container orchestration (Django, MySQL, Airflow) |

---

## 🚀 Key Features & User Stories

- **Top In-Demand Languages Bar Chart (User Story 1):** Real-time interactive bar chart of the top 10 requested programming languages (with 7-day, 30-day, and 90-day filters).
- **30-Day Historical Trend Lines (User Story 2):** Compare multi-technology demand trajectories (e.g., *Django vs. Flask*, *React vs. Vue vs. Angular*, *AWS vs. Azure vs. GCP*).
- **Automated Airflow DAG (User Story 3):** Scheduled to run daily at midnight UTC (`0 0 * * *`) with automated retries and failure alerting.
- **SysAdmin Logs & Diagnostics (User Story 4):** Comprehensive operational logs tracking run durations, jobs processed, and API failure diagnostics.
- **Blazing Fast Performance (< 1.5s):** Precomputed daily aggregate tables (`DailySkillAggregate`) ensure charts load near-instantaneously without slow full-table scans.
- **Fault-Tolerant Resilience:** Built-in offline fallback dataset ensures the pipeline never crashes if third-party APIs experience network hiccups or rate limits.

---

## 📂 Project Directory Structure

```text
Skillsight/
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── .env.example                # Environment configuration template
├── .env                        # Local environment configuration
├── docker-compose.yml          # Multi-container stack (Django + MySQL + Airflow)
├── Dockerfile                  # Application container spec
├── PRD.md                      # Product Requirements Document
├── README.md                   # Project documentation
│
├── skillsight/                 # Django project core
│   ├── settings.py             # Database (MySQL/SQLite), DRF, and app settings
│   ├── urls.py                 # Root URL routing
│   ├── wsgi.py                 # WSGI web entrypoint
│   └── asgi.py                 # ASGI entrypoint
│
├── dashboard/                  # Dashboard web application
│   ├── models.py               # Skill, JobPosting, DailySkillAggregate, PipelineRunLog
│   ├── serializers.py          # DRF API serializers
│   ├── views.py                # Dashboard view & REST endpoints
│   ├── urls.py                 # Endpoint routing
│   ├── admin.py                # Django Admin models
│   ├── templates/dashboard/
│   │   ├── base.html           # Dark-theme HTML5 shell
│   │   └── index.html          # Interactive analytics dashboard
│   └── static/
│       ├── css/dashboard.css   # Responsive CSS styling
│       └── js/dashboard.js     # Chart.js visualization logic & API fetching
│
├── etl/                        # Standalone ETL pipeline module
│   ├── config.py               # Skills taxonomy, regex patterns, and API configs
│   ├── extract.py              # Public job API extraction with fallback
│   ├── transform.py            # Pandas normalization & skill keyword matching
│   ├── load.py                 # Atomic MySQL persistence
│   └── pipeline.py             # End-to-end pipeline orchestrator
│
├── dags/                       # Apache Airflow DAGs
│   └── skillsight_etl_dag.py   # Airflow DAG (Daily 00:00 UTC)
│
├── scripts/                    # Developer and operations utilities
│   ├── run_etl.py              # Manual / cron CLI pipeline runner
│   ├── seed_historical_data.py # Seeds 45-90 days of realistic trend data
│   └── setup_mysql.sh          # Helper script for MySQL initialization
│
└── tests/                      # Automated unit and integration test suite
    ├── test_etl.py             # ETL regex, Pandas transforms, DB loading
    ├── test_api.py             # REST API endpoints & latency benchmarks
    └── test_views.py           # Dashboard HTML rendering tests
```

---

## ⚡ Quick Start Guide (Local Setup)

### 1. Clone the repository & create virtual environment
```bash
git clone https://github.com/your-username/Skillsight.git
cd Skillsight

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(By default, `.env` is configured with `DB_ENGINE=sqlite3` for zero-configuration instant local runs. To use MySQL, see the MySQL section below).*

### 3. Apply Migrations & Seed Sample Data
```bash
# Run database migrations
python manage.py migrate

# Seed 45 days of realistic historical market data
python scripts/seed_historical_data.py 45
```

### 4. Start the Django Web Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Visit **http://127.0.0.1:8000** in your browser to explore the live interactive dashboard!

---

## 🔄 Running the ETL Pipeline

You can run the ETL pipeline manually via CLI at any time:

```bash
# Run live extraction against Arbeitnow public job API
python scripts/run_etl.py --pages 2

# Force resilient fallback dataset (useful for offline environments)
python scripts/run_etl.py --fallback

# Run for a specific historical date
python scripts/run_etl.py --date 2026-10-15
```

Alternatively, click the **"Run ETL Now"** button located on the top navigation bar of the web dashboard to trigger an on-demand ETL execution via the REST API!

---

## ⏱️ Apache Airflow Orchestration

The daily ETL pipeline is defined in [`dags/skillsight_etl_dag.py`](file:///Users/shamilshiras/projects/Skillsight/dags/skillsight_etl_dag.py).

### Airflow DAG Configuration:
- **DAG ID:** `skillsight_daily_etl`
- **Schedule:** `0 0 * * *` (Daily at 00:00 UTC midnight)
- **Retries:** 3 attempts with a 5-minute exponential backoff delay
- **Tasks Flow:**
  ```text
  extract_jobs >> transform_jobs >> load_data >> verify_data_integrity
  ```

### Running with Local Airflow:
```bash
export AIRFLOW_HOME="$(pwd)/airflow"
airflow standalone
```
Copy `dags/skillsight_etl_dag.py` into your `$AIRFLOW_HOME/dags/` folder. Access the Airflow UI at `http://localhost:8080`.

---

## 🐬 MySQL Database Setup

To use MySQL instead of the default SQLite:

1. Start your local MySQL service (e.g. `brew services start mysql` or `systemctl start mysql`).
2. Run the MySQL setup script to create the database and user:
   ```bash
   bash scripts/setup_mysql.sh
   ```
3. Update `.env`:
   ```dotenv
   DB_ENGINE=mysql
   DB_NAME=skillsight_db
   DB_USER=skillsight_user
   DB_PASSWORD=skillsight_pass
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   python scripts/seed_historical_data.py 45
   ```

---

## 🐳 Docker Compose Deployment

To launch the full production-ready stack (**Django**, **MySQL 8.0**, and **Apache Airflow**) with a single command:

```bash
docker-compose up -d
```

- **Dashboard:** [http://localhost:8000](http://localhost:8000)
- **Airflow Webserver:** [http://localhost:8080](http://localhost:8080)
- **MySQL Port:** `3306`

---

## 📡 REST API Reference

| Endpoint | Method | Query Parameters | Description |
| :--- | :---: | :--- | :--- |
| `/api/summary/` | `GET` | `days` (default `7`) | High-level KPIs (#1 language, #1 framework, fastest growth, ETL status) |
| `/api/top-skills/` | `GET` | `days`, `category`, `limit` | Ranked technical skills for bar charts |
| `/api/trends/` | `GET` | `skills` (comma-separated), `days` | Time-series data for line chart comparisons (e.g. `django,flask`) |
| `/api/categories/` | `GET` | None | Full technical skills taxonomy grouped by category |
| `/api/jobs/` | `GET` | `page`, `page_size`, `skill`, `remote`, `search` | Paginated job postings with matched skill tags |
| `/api/logs/` | `GET` | `limit` (default `20`) | Operational pipeline execution logs for system administrators |
| `/api/trigger-etl/` | `POST` | `pages`, `force_fallback` | Triggers an on-demand ETL execution |

---

## 🧪 Running Tests

The test suite thoroughly verifies text cleaning, regex skill keyword matching, Pandas DataFrame normalization, database atomic transactions, API endpoint responses, and query performance:

```bash
python manage.py test tests
```

Sample output:
```text
Found 16 test(s).
Creating test database for alias 'default'...
................
----------------------------------------------------------------------
Ran 16 tests in 0.110s

OK
```
