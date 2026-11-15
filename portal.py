"""
Rangg Roop Order Portal
-----------------------
A console-based order management portal for a small women's clothing business.

Features : login (admin / staff), add, view, search, update and delete orders,
           and a sales analytics report.
Storage  : CSV files (orders.csv, users.csv)
Run      : python portal.py
"""

import csv
import hashlib
import math
import os
from datetime import datetime

ORDERS_FILE = "orders.csv"
USERS_FILE = "users.csv"

ORDER_FIELDS = ["order_id", "customer_name", "city", "item",
                "quantity", "unit_price", "order_date", "status"]
USER_FIELDS = ["username", "password_hash", "role"]
VALID_STATUSES = ["Pending", "Delivered", "Returned"]


def save_orders(filename, orders):
    """Write the full list of orders to a CSV file (overwrites the file).

    Args:
        filename (str): path of the CSV file.
        orders (list[dict]): every order currently in memory.

    Returns:
        bool: True if saved, False if the file could not be written.
    """
    try:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=ORDER_FIELDS)
            writer.writeheader()
            writer.writerows(orders)
        return True
    except PermissionError:
        print(f"  [error] No permission to write '{filename}'. Close it in Excel and try again.")
        return False
    except OSError as error:
        print(f"  [error] Could not write '{filename}': {error}")
        return False


def append_order(filename, order):
    """Add a single order to the end of the CSV file.

    Writes the header row first if the file is new or empty.

    Args:
        filename (str): path of the CSV file.
        order (dict): one order, with the keys listed in ORDER_FIELDS.

    Returns:
        bool: True if appended, False if the write failed.
    """
    try:
        needs_header = (not os.path.exists(filename)) or os.path.getsize(filename) == 0
        with open(filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=ORDER_FIELDS)
            if needs_header:
                writer.writeheader()
            writer.writerow(order)
        return True
    except PermissionError:
        print(f"  [error] No permission to write '{filename}'. Close it in Excel and try again.")
        return False
    except OSError as error:
        print(f"  [error] Could not write '{filename}': {error}")
        return False


def load_orders(filename):
    """Read all orders from a CSV file into a list of dictionaries.

    - Missing file  -> a new file with just the header row is created.
    - No permission -> a message is printed and an empty list is returned.
    - Damaged row   -> that row is skipped with a warning, the rest still load.

    Args:
        filename (str): path of the CSV file.

    Returns:
        list[dict]: orders, with quantity as int and unit_price as float.
    """
    orders = []
    skipped = 0
    try:
        with open(filename, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row_number, row in enumerate(reader, start=2):  # row 1 is the header
                try:
                    order = {field: (row.get(field) or "").strip() for field in ORDER_FIELDS}
                    order["quantity"] = int(order["quantity"])
                    order["unit_price"] = float(order["unit_price"])
                    if not order["order_id"]:
                        raise ValueError("missing order_id")
                    if order["status"] not in VALID_STATUSES:
                        raise ValueError("unknown status")
                    orders.append(order)
                except ValueError:
                    skipped += 1
                    print(f"  [warning] Skipped row {row_number}: data is damaged.")
    except FileNotFoundError:
        print(f"  [info] '{filename}' not found. Creating a new empty file.")
        save_orders(filename, [])
    except PermissionError:
        print(f"  [error] No permission to read '{filename}'.")
    finally:
        print(f"  [load] {len(orders)} order(s) loaded, {skipped} skipped.")
    return orders
