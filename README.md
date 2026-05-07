# Automated Report Bot

Pulls data from any source, builds a formatted Excel or PDF report, and delivers it by email on schedule. No human involved after setup.

---

## Quick Start

```bash
cp .env.example .env
# fill in your SMTP/SendGrid and DB credentials
pip install -r requirements.txt
python run_report.py reports/config/monthly_summary.yaml
```

Run the full scheduler:
```bash
python main.py
```

---

## How to Add a New Report

1. Create a YAML file in `reports/config/my_report.yaml`
2. Follow the schema below — no code changes needed
3. Restart the scheduler (or it picks it up on next start)

```yaml
name: "My Custom Report"
schedule: "every friday at 17:30"
format: "excel"          # excel | pdf | both

source:
  type: "csv"            # postgres | csv | api | excel
  path: "data/myfile.csv"

transform:               # optional
  - type: "sort"
    by: "revenue"
    ascending: false

delivery:
  recipients:
    - "you@company.com"
  subject: "My Report — {date_range}"
  body: "Attached is the report for {date_range}."
  attach_file: true
```

---

## Data Source Types

| Type       | Key config fields                              |
|------------|------------------------------------------------|
| `postgres` | `query` (SQL string)                           |
| `csv`      | `path`, `separator`, `skip_rows`, `columns`    |
| `api`      | `url`, `bearer_token`, `data_key`, `params`    |
| `excel`    | `path`, `sheet`, `skip_rows`, `columns`        |

---

## Transformer Reference

| Type             | Config fields                              |
|------------------|--------------------------------------------|
| `add_column`     | `name`, `formula` (pandas eval expression) |
| `format_currency`| `columns`, `symbol` (default `$`)          |
| `format_percent` | `columns`, `decimals`                      |
| `sort`           | `by`, `ascending`                          |
| `filter`         | `query` (pandas query string)              |
| `rename`         | `columns` (dict old→new)                   |
| `drop_columns`   | `columns` (list)                           |
| `fill_na`        | `value`, `columns` (optional)              |
| `week_over_week` | `revenue_column`                           |
| `region_rank`    | `metric`                                   |

---

## Schedule Format Reference

```
"every monday at 08:00"
"every friday at 17:30"
"every day at 06:00"
"every 1 hours"
"every 30 minutes"
```

Missed jobs within 1 hour of their schedule run automatically on startup.

---

## Email Delivery

### SMTP (Gmail, Outlook, custom)

```env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=you@gmail.com
```

### SendGrid (recommended for production)

```env
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxx
EMAIL_FROM=reports@yourcompany.com
```

### Per-report delivery config

```yaml
delivery:
  recipients: ["ceo@co.com", "ops@co.com"]
  cc: ["manager@co.com"]
  bcc: ["archive@co.com"]
  subject: "Report — {date_range}"
  body: "Attached for {date_range}."
  attach_file: true
```

---

## Running with Docker

```bash
cp .env.example .env
# edit .env
docker compose up --build
```

The bot starts, seeds the PostgreSQL database via `data/seed.sql`, and runs all configured reports on schedule.

To run a single report immediately inside Docker:
```bash
docker compose run report-bot python run_report.py reports/config/monthly_summary.yaml
```

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Minimum 15 tests — all must pass before shipping.

---

## Project Structure

```
bot/
  sources/        # Data extraction (postgres, csv, api, excel)
  transformers/   # Data transformation pipeline
  builders/       # Excel + PDF report generation
  delivery/       # Email delivery (SMTP + SendGrid)
  pipeline.py     # Orchestration: extract → transform → build → deliver
  scheduler.py    # Schedule-based job runner
  config.py       # YAML loader + env config

reports/config/   # YAML report definitions (one file = one report)
data/             # Seed data and CSV files
tests/            # Pytest test suite
main.py           # Entrypoint: start scheduler
run_report.py     # CLI: run one report now
```

---

## Environment Variables

| Variable              | Description                              |
|-----------------------|------------------------------------------|
| `DB_HOST/PORT/NAME`   | PostgreSQL connection                    |
| `DB_USER/PASSWORD`    | PostgreSQL credentials                   |
| `EMAIL_PROVIDER`      | `smtp` or `sendgrid`                     |
| `SMTP_HOST/PORT`      | SMTP server settings                     |
| `SMTP_USER/PASSWORD`  | SMTP credentials                         |
| `SENDGRID_API_KEY`    | SendGrid API key                         |
| `EMAIL_FROM`          | Sender address                           |
| `EMAIL_FROM_NAME`     | Sender display name                      |
| `ALERT_EMAIL`         | Where to send pipeline failure alerts    |
| `REPORTS_CONFIG_DIR`  | Directory for YAML configs (default: `reports/config`) |
| `OUTPUT_DIR`          | Where generated files are saved (default: `output`) |
