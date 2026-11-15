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


def hash_password(password):
    """Turn a password into a SHA-256 hash string.

    Args:
        password (str): the plain-text password.

    Returns:
        str: 64-character hexadecimal hash.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def default_users():
    """Return the two starter accounts used when users.csv does not exist yet."""
    return [
        {"username": "admin", "password_hash": hash_password("admin123"), "role": "admin"},
        {"username": "staff", "password_hash": hash_password("staff123"), "role": "staff"},
    ]


def load_users(filename):
    """Read user accounts from a CSV file.

    If the file is missing, it is created with the default accounts.

    Args:
        filename (str): path of the users CSV file.

    Returns:
        list[dict]: accounts with keys username, password_hash, role.
    """
    users = []
    try:
        with open(filename, newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                users.append({field: (row.get(field) or "").strip() for field in USER_FIELDS})
    except FileNotFoundError:
        print(f"  [info] '{filename}' not found. Creating it with default accounts.")
        users = default_users()
        try:
            with open(filename, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=USER_FIELDS)
                writer.writeheader()
                writer.writerows(users)
        except (PermissionError, OSError) as error:
            print(f"  [warning] Could not save '{filename}': {error}. Using defaults in memory only.")
    except PermissionError:
        print(f"  [error] No permission to read '{filename}'.")
    return users


def check_credentials(users, username, password):
    """Check a username and password against the stored accounts.

    Args:
        users (list[dict]): accounts from load_users().
        username (str): typed username.
        password (str): typed plain-text password.

    Returns:
        str | None: the account's role ("admin" or "staff") if correct, otherwise None.
    """
    typed_hash = hash_password(password)
    for user in users:
        if user["username"] == username.strip() and user["password_hash"] == typed_hash:
            return user["role"]
    return None


def user_login(users, max_attempts=3):
    """Ask for a username and password, allowing a limited number of attempts.

    Args:
        users (list[dict]): accounts from load_users().
        max_attempts (int): how many tries before giving up.

    Returns:
        dict | None: {"username": ..., "role": ...} on success, None if all attempts fail.
    """
    for attempt in range(1, max_attempts + 1):
        username = input("Username: ")
        password = input("Password: ")
        role = check_credentials(users, username, password)
        if role is not None:
            print(f"\nWelcome, {username.strip()} ({role}).")
            return {"username": username.strip(), "role": role}
        remaining = max_attempts - attempt
        print(f"  Wrong username or password. {remaining} attempt(s) left.")
    print("Too many failed attempts. Portal locked.")
    return None
