import pandas as pd

# Load the data
customers = pd.read_csv("data/customers.csv")
orders = pd.read_parquet("data/orders.parquet")

print("Customers:")
print(customers.head())

print("\nOrders:")
print(orders.head())
