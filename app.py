import os
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, render_template
from sqlalchemy import create_engine

load_dotenv()

app = Flask(__name__)


def get_engine():
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

    return create_engine("mssql+pyodbc:///?odbc_connect=" + quote_plus(conn))


@app.route("/")
def dashboard():
    engine = get_engine()
    sales = pd.read_sql("SELECT * FROM dbo.Sales ORDER BY order_id", engine)
    total_sales = sales["total_amount"].sum() if not sales.empty else 0
    return render_template(
        "index.html",
        sales=sales.to_dict("records"),
        total_sales=f"{total_sales:,.2f}",
        row_count=len(sales),
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
