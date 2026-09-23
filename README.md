# ETL Project + Flask Dashboard

A Python ETL pipeline that reads customers and orders, retrieves products from the API specified in the assignment README, cleans and transforms the data, creates a final Sales dataset, loads it into SQL Server, and displays the Sales table through a Flask dashboard.

## Project requirements

The pipeline follows the supplied assignment requirements:
- Sources: `customers.csv`, `orders.parquet`, and `products.csv` retrieved from the provided API.
- Customers: remove duplicates, standardize city, validate age, handle missing email, create `full_name`.
- Orders: remove duplicate `order_id`, validate quantity, convert `order_date` to datetime, validate `customer_id`.
- Products: remove duplicates, standardize product/category, validate `unit_price`, convert price to numeric.
- Sales: merge the three datasets and calculate `total_amount = quantity * unit_price`.
- Final Sales columns: `order_id`, `customer`, `product`, `quantity`, `unit_price`, `total_amount`.
- Load `Sales` into SQL Server and show it in a Flask dashboard.

## Structure

```text
etl-project/

├── data/
│   ├── customers.csv
│   └── orders.parquet
├── output/
│   ├── products.csv
│   └── sales.csv
├── templates/
│   └── index.html
├── app.py
├── etl.py
├── schema.sql
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set your SQL Server connection values.
4. Run the ETL:

```bash
python etl.py
```

5. Start the dashboard:

```bash
python app.py
```

Then open `http://127.0.0.1:5000`.

> The products dataset is retrieved at runtime from the API URL required by the supplied assignment README.
