# 📊 Stock Market Data Pipeline with Airflow, Finnhub API & Postgres

## 🚀 Project Overview
This project implements an end-to-end data pipeline that fetches real-time stock market data using the **Finnhub API**, processes it with **Airflow DAGs**, and stores it in a **Postgres database**.

Everything runs in **Docker containers** for portability and easy deployment.

---

## ⚙️ Architecture
- **Airflow Scheduler & Webserver** → Orchestrates DAGs (tasks).  
- **Python Script (`fetch_and_upsert.py`)** → Calls Finnhub API, parses data, and upserts into Postgres.  
- **Postgres Database** → Stores stock data (`stock_quotes` table).  
- **Docker Compose** → Manages all services and networking.  

---

## 📦 Tech Stack
- **Apache Airflow** (workflow orchestration)  
- **PostgreSQL** (data warehouse)  
- **Finnhub API** (real-time stock quotes)  
- **Docker + Docker Compose** (containerized setup)  
- **Python** (`requests`, `psycopg2`)  

---

## 🔑 Why Finnhub API?
Originally, we tested with Yahoo Finance (`yfinance`) and Alpha Vantage, but:  
- `yfinance` → easy, but sometimes slow and rate-limited  
- `Alpha Vantage` → free but very restrictive (5 API calls/minute)  
- ✅ **Finnhub API** → Free plan allows **60 API calls/minute**, faster and more reliable for multiple stocks  

That’s why **Finnhub** was chosen — better performance and scalability in Airflow pipelines.  

---

## 🔌 Why Port `5433:5432`?
In the `docker-compose.yml`, Postgres is mapped like this:

```yaml
ports:
  - "5433:5432"
```

- **5432** → internal port inside the Postgres container (default for Postgres)  
- **5433** → external port on the host machine (Windows/Mac/Linux)  

👉 Inside Docker containers (Airflow → Postgres), use `5432`.  
👉 From your host machine (DBeaver, pgAdmin, psql), connect via `5433`.  

---

## 📂 Project Structure
```bash
stock-pipeline-finnhub/
│── dags/
│   └── stock_pipeline_dag.py       # Airflow DAG definition
│── scripts/
│   └── fetch_and_upsert.py         # Finnhub API → Postgres upsert
│── logs/                           # Airflow logs (gitignored)
│── .env.example                    # Example environment variables
│── docker-compose.yml              # Service orchestration
│── README.md                       # Project documentation
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/stock-pipeline-finnhub.git
cd stock-pipeline-finnhub
```

### 2️⃣ Configure environment variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and add your Finnhub API key:
```env
FINNHUB_API_KEY=your_api_key_here
TARGET_STOCKS=AAPL,MSFT,GOOGL,TSLA,NVDA,AMZN,META,MCD,DIS
DB_HOST=postgres
DB_PORT=5432      # inside Docker, keep 5432
DB_NAME=airflow
DB_USER=airflow
DB_PASSWORD=airflow
TARGET_TABLE=stock_quotes
```
⚠️ **Do not commit your real `.env` file. Keep it private.**

### 3️⃣ Start Docker containers
```bash
docker-compose up -d
```

### 4️⃣ Access Airflow
Open [http://localhost:8080](http://localhost:8080)  
- Username: `admin`  
- Password: `admin`  

Find and trigger the DAG: `stock_pipeline_dag`.  

### 5️⃣ Check Postgres Data
Enter Postgres container:
```bash
docker exec -it sp_postgres psql -U airflow -d airflow
```
Run queries:
```sql
\dt
SELECT * FROM stock_quotes LIMIT 5;
```

Example output:
```
 symbol | trading_day |  open  |  high  |  low   | close  | prev_close
--------+-------------+--------+--------+--------+--------+------------
 AAPL   | 2025-08-24  | 226.17 | 229.09 | 225.41 | 227.76 |      224.9
 MSFT   | 2025-08-24  | 504.25 | 510.73 | 502.41 | 507.23 |     504.24
```

---

## 🌟 Future Improvements
- Add dashboards (Metabase/Superset) for visualization  
- Batch API calls for 50+ tickers  
- Store historical daily data (not just current quote)  
- Deploy on cloud (AWS/GCP/Azure)  
