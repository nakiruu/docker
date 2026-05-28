# Superset + Financial Dataset

Local [Apache Superset](https://superset.apache.org/) wired to the [Financial dataset](https://relational.fel.cvut.cz/dataset/Financial) from CTU Prague. Everything runs in Docker — no cloud hosting required.

## Quick start

```bash
docker compose up
```

First boot takes **3–5 minutes**:

1. MariaDB starts and streams the Financial dataset (~78 MB) from `relational.fel.cvut.cz`
2. Superset migrates its metadata DB and creates the admin user
3. Superset starts on port 8088

Open **http://localhost:8088** and log in:

| Username | Password |
|---|---|
| `admin` | `admin` |

## Connect Superset to the Financial database

Do this once after first login:

**Settings → Database Connections → + Database → MySQL**

| Field | Value |
|---|---|
| Host | `financial-db` |
| Port | `3306` |
| Database | `financial` |
| Username | `financial` |
| Password | `financial` |

Or paste the SQLAlchemy URI directly:
```
mysql+pymysql://financial:financial@financial-db:3306/financial
```

Once connected, go to **SQL Lab** or **Datasets** to start exploring.

## Dataset overview

| Table | Rows | Description |
|---|---|---|
| `trans` | 1,056,320 | All bank transactions |
| `account` | 4,500 | Bank accounts |
| `client` | 5,369 | Customers |
| `disp` | 5,369 | Client ↔ account relationships |
| `order` | 6,471 | Permanent payment orders |
| `loan` | 682 | Loans — `status` column is the ML target |
| `card` | 892 | Credit cards |
| `district` | 77 | Regional demographic stats |

The classic task: predict `loan.status` (paid off vs. defaulted) using account behaviour.

## Useful starting queries

```sql
-- Loan outcomes
SELECT status, COUNT(*) AS n FROM loan GROUP BY status;

-- Average balance by district
SELECT d.A2 AS district, AVG(t.balance) AS avg_balance
FROM trans t
JOIN account a ON t.account_id = a.account_id
JOIN district d ON a.district_id = d.district_id
GROUP BY d.A2
ORDER BY avg_balance DESC;

-- Monthly transaction volume
SELECT DATE_FORMAT(date, '%Y-%m') AS month,
       SUM(amount) AS total, COUNT(*) AS count
FROM trans
GROUP BY month
ORDER BY month;
```

## Configuration

Edit `.env` to change ports or credentials. Set `SUPERSET_SECRET_KEY` to a long random string for anything beyond local play.

## Reset everything

```bash
docker compose down -v   # removes all volumes
docker compose up        # re-downloads data and re-initializes
```

## Services

| Service | Port | Purpose |
|---|---|---|
| `superset` | 8088 | Superset UI |
| `financial-db` | 3307 | Financial dataset (MariaDB) |
| `superset-db` | — | Superset metadata (PostgreSQL, internal) |
| `redis` | — | Cache (internal) |
