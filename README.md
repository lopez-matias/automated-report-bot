# Automated Report Bot

Pulls data from any source, builds a formatted Excel or PDF report, and delivers it by email on a schedule. No human involvement after setup.

---

## Quick Start

```bash
cp .env.example .env      # fill in credentials
pip install -r requirements.txt
python -m bot.main        # starts the scheduler
```

Run with Docker (one command):

```bash
docker compose up --build
```

---

## Adding a New Report

Create a YAML file in `reports/config/`. The scheduler picks it up automatically on next start.

```yaml
name: "My New Report"
schedule: "every monday at 09:00"
format: "excel"          # excel | pdf | both

source:
  type: "csv"            # postgres | csv | api | excel
  path: "data/myfile.csv"

transform:
  - type: "sort"
    by: "revenue"
    ascending: false

delivery:
  recipients:
    - "team@company.com"
  subject: "My Report — {date_range}"
  body: "Please find the report attached."
  attach_file: true
```

No code changes required.

---

## Data Source Types

| Type       | Config keys                                           |
|------------|-------------------------------------------------------|
| `postgres` | `url` (or `host/user/password/database/port`), `query` |
| `csv`      | `path`, `separator` (default `,`), `columns`          |
| `api`      | `url`, `token`, `data_key`, `params`, `paginate`, `page_param` |
| `excel`    | `path`, `sheet` (name or index), `skiprows`           |

### PostgreSQL example

```yaml
source:
  type: "postgres"
  url: "${DATABASE_URL}"
  query: "SELECT * FROM sales WHERE date >= NOW() - INTERVAL '7 days'"
```

### CSV example

```yaml
source:
  type: "csv"
  path: "data/inventory.csv"
  separator: ","
```

### REST API example

```yaml
source:
  type: "api"
  url: "https://open.er-api.com/v6/latest/USD"
  data_key: "rates"
  paginate: false
```

### Excel file example

```yaml
source:
  type: "excel"
  path: "data/report.xlsx"
  sheet: "Sheet1"
  skiprows: 0
```

---

## Transformations

| Type             | Config keys                                  |
|------------------|----------------------------------------------|
| `add_column`     | `name`, `formula` (pandas eval expression)   |
| `format_currency`| `columns` (list), `symbol`                   |
| `sort`           | `by`, `ascending`                            |
| `filter`         | `column`, `op` (`eq/ne/gt/lt/gte/lte/contains`), `value` |
| `rename`         | `mapping` (dict old→new)                     |
| `drop_columns`   | `columns` (list)                             |
| `group_by`       | `by` (list), `agg` (dict col→func)           |
| `wow_change`     | `column` — adds week-over-week % change      |
| `revenue_kpi`    | `column` — returns single-row KPI summary    |
| `region_rank`    | `column` — adds rank column                  |

---

## Schedule Format Reference

```
every monday at 08:00
every tuesday at 09:30
every friday at 17:00
every day at 06:00
every 1 hours
every 30 minutes
```

Supported day names: `monday tuesday wednesday thursday friday saturday sunday day`

---

## Email Delivery

### SMTP (Gmail, Outlook, any SMTP)

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=you@gmail.com
```

For Gmail, generate an **App Password** at myaccount.google.com/apppasswords.

### SendGrid (recommended for production)

```env
USE_SENDGRID=true
SENDGRID_API_KEY=SG.xxxxx
FROM_EMAIL=reports@yourdomain.com
```

### Failure alerts

```env
ALERT_EMAIL=admin@company.com
```

---

## Running with Docker

```bash
# 1. Fill in .env
cp .env.example .env

# 2. Start everything (bot + PostgreSQL)
docker compose up --build

# 3. View logs
docker compose logs -f bot

# 4. Stop
docker compose down
```

The PostgreSQL database is seeded automatically via `db/init.sql`.

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Minimum 15 tests, all passing.

---

## Project Structure

```
automated-report-bot/
├── bot/
│   ├── sources/          # Data source adapters
│   ├── transformers/     # Data transformation steps
│   ├── builders/         # Excel & PDF report builders
│   ├── delivery/         # Email delivery + HTML template
│   ├── scheduler.py      # Job scheduler
│   ├── config.py         # YAML config loader
│   ├── pipeline.py       # Orchestrator
│   └── main.py           # Entry point
├── reports/config/       # YAML report definitions
├── data/                 # Seed CSV files
├── db/                   # SQL init scripts
├── tests/                # Pytest test suite
├── output/               # Generated reports (git-ignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Environment Variables

| Variable          | Description                          | Default           |
|-------------------|--------------------------------------|-------------------|
| `DATABASE_URL`    | SQLAlchemy PostgreSQL URL            | —                 |
| `SMTP_HOST`       | SMTP server hostname                 | `smtp.gmail.com`  |
| `SMTP_PORT`       | SMTP port                            | `587`             |
| `SMTP_USER`       | SMTP username                        | —                 |
| `SMTP_PASS`       | SMTP password / app password         | —                 |
| `FROM_EMAIL`      | Sender address                       | SMTP_USER         |
| `USE_SENDGRID`    | Use SendGrid instead of SMTP         | `false`           |
| `SENDGRID_API_KEY`| SendGrid API key                     | —                 |
| `ALERT_EMAIL`     | Address for failure alerts           | —                 |
| `OUTPUT_DIR`      | Directory for generated files        | `output`          |
| `CONFIG_DIR`      | Directory containing YAML configs    | `reports/config`  |
| `LOG_LEVEL`       | Python logging level                 | `INFO`            |
# automate-report-bot
