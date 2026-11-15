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


def parse_text(raw, label="Value"):
    """Return trimmed text, or raise ValueError if it is empty."""
    cleaned = str(raw).strip()
    if not cleaned:
        raise ValueError(f"{label} cannot be empty.")
    return cleaned


def parse_quantity(raw):
    """Convert input to a whole number greater than zero, or raise ValueError."""
    try:
        value = int(str(raw).strip())
    except ValueError:
        raise ValueError("Quantity must be a whole number, like 1 or 3.")
    if value <= 0:
        raise ValueError("Quantity must be greater than zero.")
    return value


def parse_price(raw):
    """Convert input to a positive, finite number, or raise ValueError."""
    try:
        value = float(str(raw).strip().replace(",", ""))
    except ValueError:
        raise ValueError("Price must be a number, like 4500 or 1899.50.")
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Price must be a real number greater than zero.")
    return value


def parse_date(raw):
    """Check a date is written as YYYY-MM-DD and return it, or raise ValueError."""
    text = str(raw).strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must look like 2026-11-15 (year-month-day).")
    return text


def parse_status(raw):
    """Match input to one of VALID_STATUSES (case-insensitive), or raise ValueError."""
    text = str(raw).strip().lower()
    for status in VALID_STATUSES:
        if text == status.lower():
            return status
    raise ValueError("Status must be one of: " + ", ".join(VALID_STATUSES) + ".")


def order_total(order):
    """Return quantity x unit_price for one order."""
    return order["quantity"] * order["unit_price"]


def next_order_id(orders):
    """Work out the next free order ID, such as 'RR-017'.

    Args:
        orders (list[dict]): current orders.

    Returns:
        str: ID one higher than the largest existing RR-number.
    """
    highest = 0
    for order in orders:
        try:
            number = int(order["order_id"].split("-")[1])
        except (IndexError, ValueError):
            continue  # ignore IDs that don't follow the RR-### pattern
        highest = max(highest, number)
    return f"RR-{highest + 1:03d}"


def add_record(orders, customer_name, city, item, quantity, unit_price,
               order_date=None, status="Pending"):
    """Validate the details and add a new order to the list.

    Nothing is added unless every field is valid.

    Args:
        orders (list[dict]): current orders (modified in place).
        customer_name, city, item (str): text fields.
        quantity (int | str): number of units.
        unit_price (float | str): price per unit in PKR.
        order_date (str | None): YYYY-MM-DD, defaults to today.
        status (str): one of VALID_STATUSES, defaults to "Pending".

    Returns:
        dict: the order that was added.

    Raises:
        ValueError: if any field is invalid.
    """
    if order_date is None:
        order_date = datetime.now().strftime("%Y-%m-%d")

    new_order = {
        "order_id": next_order_id(orders),
        "customer_name": parse_text(customer_name, "Customer name").title(),
        "city": parse_text(city, "City").title(),
        "item": parse_text(item, "Item"),
        "quantity": parse_quantity(quantity),
        "unit_price": parse_price(unit_price),
        "order_date": parse_date(order_date),
        "status": parse_status(status),
    }
    orders.append(new_order)
    return new_order


def search_record(orders, keyword):
    """Find orders where the keyword appears in the ID, customer, city, item or status.

    The search ignores upper/lower case, so 'lahore' finds 'Lahore'.

    Args:
        orders (list[dict]): current orders.
        keyword (str): text to look for.

    Returns:
        list[dict]: matching orders (empty list if none, or if keyword is blank).
    """
    keyword = keyword.strip().lower()
    if not keyword:
        return []
    matches = []
    for order in orders:
        searchable = [order["order_id"], order["customer_name"],
                      order["city"], order["item"], order["status"]]
        for value in searchable:
            if keyword in value.lower():
                matches.append(order)
                break  # one hit is enough, avoid listing the same order twice
    return matches
