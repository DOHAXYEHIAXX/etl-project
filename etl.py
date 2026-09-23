import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

PRODUCTS_URL = "https://raw.githubusercontent.com/MohammedHameds/test1455/refs/heads/main/products.csv"


def load_sources():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    orders = pd.read_parquet(DATA_DIR / "orders.parquet")

    response = requests.get(PRODUCTS_URL, timeout=30)
    response.raise_for_status()
    products_path = OUTPUT_DIR / "products.csv"
    products_path.write_bytes(response.content)
    products = pd.read_csv(products_path)

    return customers, orders, products


def transform_customers(df):
    df = df.copy()
    df = df.drop_duplicates()

    df["city"] = df["city"].astype("string").str.strip().str.title()
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df.loc[~df["age"].between(0, 120), "age"] = pd.NA

    df["email"] = df["email"].astype("string").str.strip()
    df["email"] = df["email"].replace({"": pd.NA, "nan": pd.NA})

    df["first_name"] = df["first_name"].astype("string").str.strip()
    df["last_name"] = df["last_name"].astype("string").str.strip()
    df["full_name"] = (df["first_name"].fillna("") + " " + df["last_name"].fillna("")).str.strip()

    return df


def transform_orders(df, valid_customer_ids):
    df = df.copy()
    df = df.drop_duplicates(subset=["order_id"])

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df.loc[df["quantity"] <= 0, "quantity"] = pd.NA
    df["quantity"] = df["quantity"].astype("Int64")

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")
    df = df[df["customer_id"].isin(valid_customer_ids)]

    return df


def transform_products(df):
    df = df.copy()
    df = df.drop_duplicates()

    for col in ["product", "category"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip().str.title()

    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df.loc[df["unit_price"] < 0, "unit_price"] = pd.NA

    return df


def build_sales(customers, orders, products):
    customers = transform_customers(customers)
    orders = transform_orders(orders, set(customers["customer_id"].dropna()))
    products = transform_products(products)

    sales = orders.merge(
        customers[["customer_id", "full_name"]],
        on="customer_id",
        how="inner",
    )

    # Support common product-key names while keeping the assignment's output.
    product_key = next((c for c in ["product_id", "id"] if c in products.columns), None)
    order_product_key = next((c for c in ["product_id", "product"] if c in sales.columns), None)

    if product_key and order_product_key:
        sales = sales.merge(
            products,
            left_on=order_product_key,
            right_on=product_key,
            how="inner",
            suffixes=("", "_product"),
        )
    else:
        raise ValueError("Could not identify a compatible product key in orders/products.")

    product_name_col = "product" if "product" in sales.columns else "product_name"
    if product_name_col not in sales.columns:
        raise ValueError("Products data must contain a product/product_name column.")

    sales["total_amount"] = sales["quantity"] * sales["unit_price"]

    final = sales.rename(
        columns={
            "full_name": "customer",
            product_name_col: "product",
        }
    )[
        ["order_id", "customer", "product", "quantity", "unit_price", "total_amount"]
    ].copy()

    final = final.dropna(subset=["order_id", "quantity", "unit_price"])
    return final


def sql_engine():

    server = os.getenv("SQL_SERVER", r".\SQLEXPRESS")
    database = os.getenv("SQL_DATABASE", "BankSystem")
    username = os.getenv("SQL_USERNAME", "")
    password = os.getenv("SQL_PASSWORD", "")
    driver = os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server")
    trusted = os.getenv("SQL_TRUSTED_CONNECTION", "true").lower() == "true"

    if trusted:
        conn = (
            f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
            "Trusted_Connection=yes;TrustServerCertificate=yes;"
        )
    else:
        conn = (
            f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
            f"UID={username};PWD={password};TrustServerCertificate=yes;"
        )

    return create_engine(
        "mssql+pyodbc:///?odbc_connect=" + quote_plus(conn),
        fast_executemany=True,
    )


def load_to_sql(sales):
    engine = sql_engine()
    with engine.begin() as connection:
        connection.execute(text("""
            IF OBJECT_ID('dbo.Sales', 'U') IS NULL
            CREATE TABLE dbo.Sales (
                order_id INT NOT NULL,
                customer VARCHAR(201) NULL,
                product VARCHAR(255) NULL,
                quantity INT NULL,
                unit_price DECIMAL(18, 2) NULL,
                total_amount DECIMAL(18, 2) NULL
            )
        """))
        connection.execute(text("DELETE FROM dbo.Sales"))

    sales.to_sql("Sales", engine, schema="dbo", if_exists="append", index=False)


def main():
    customers, orders, products = load_sources()
    sales = build_sales(customers, orders, products)
    sales.to_csv(OUTPUT_DIR / "sales.csv", index=False)
    load_to_sql(sales)
    print(f"ETL completed successfully. {len(sales)} rows loaded into dbo.Sales.")


if __name__ == "__main__":
    main()
