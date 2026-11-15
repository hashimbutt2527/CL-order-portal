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


def find_order(orders, order_id):
    """Return the order with the given ID, or None if it does not exist."""
    wanted = order_id.strip().upper()
    for order in orders:
        if order["order_id"].upper() == wanted:
            return order
    return None


def update_status(orders, order_id, new_status):
    """Change the status of one order.

    Args:
        orders (list[dict]): current orders (modified in place).
        order_id (str): e.g. 'RR-004'.
        new_status (str): one of VALID_STATUSES.

    Returns:
        bool: True if updated, False if no order has that ID.

    Raises:
        ValueError: if new_status is not a valid status.
    """
    new_status = parse_status(new_status)  # validate first
    order = find_order(orders, order_id)
    if order is None:
        return False
    order["status"] = new_status
    return True


def delete_record(orders, order_id):
    """Remove one order from the list.

    Returns:
        bool: True if deleted, False if no order has that ID.
    """
    order = find_order(orders, order_id)
    if order is None:
        return False
    orders.remove(order)
    return True


def top_entries(totals):
    """Return the key with the highest value. If several tie, return all of them joined by ' / '.

    A plain max() would silently pick the first tied key and hide the tie from the reader.

    Args:
        totals (dict): e.g. {"Lahore": 22100.0, "Karachi": 12400.0}

    Returns:
        str | None: the winning key(s), or None if the dictionary is empty.
    """
    if not totals:
        return None
    highest = max(totals.values())
    winners = [key for key, value in totals.items() if value == highest]
    return " / ".join(winners)


def generate_report(orders):
    """Calculate summary statistics for all orders.

    Args:
        orders (list[dict]): current orders.

    Returns:
        dict: total_orders, total_revenue, delivered_revenue, pending_revenue,
        returned_value, return_rate_pct, avg_order_value, revenue_by_city,
        units_by_item, orders_by_status, top_city, best_selling_item.
    """
    report = {
        "total_orders": len(orders),
        "total_revenue": 0.0,
        "delivered_revenue": 0.0,
        "pending_revenue": 0.0,
        "returned_value": 0.0,
        "return_rate_pct": 0.0,
        "avg_order_value": 0.0,
        "revenue_by_city": {},
        "units_by_item": {},
        "orders_by_status": {status: 0 for status in VALID_STATUSES},
        "top_city": None,
        "best_selling_item": None,
    }

    for order in orders:
        total = order_total(order)
        report["orders_by_status"][order["status"]] += 1

        if order["status"] == "Returned":
            report["returned_value"] += total
            continue  # returned orders are not revenue

        report["total_revenue"] += total
        if order["status"] == "Delivered":
            report["delivered_revenue"] += total
        else:
            report["pending_revenue"] += total

        city = order["city"]
        report["revenue_by_city"][city] = report["revenue_by_city"].get(city, 0.0) + total
        item = order["item"]
        report["units_by_item"][item] = report["units_by_item"].get(item, 0) + order["quantity"]

    kept_orders = report["total_orders"] - report["orders_by_status"]["Returned"]
    if report["total_orders"] > 0:
        report["return_rate_pct"] = report["orders_by_status"]["Returned"] / report["total_orders"] * 100
    if kept_orders > 0:
        report["avg_order_value"] = report["total_revenue"] / kept_orders
    report["top_city"] = top_entries(report["revenue_by_city"])
    report["best_selling_item"] = top_entries(report["units_by_item"])
    return report


def print_report(report):
    """Print the dictionary from generate_report() in a readable layout."""
    print("\n" + "=" * 52)
    print("  RANGG ROOP - SALES REPORT")
    print("=" * 52)
    print(f"  Total orders           : {report['total_orders']}")
    print(f"  Total revenue          : PKR {report['total_revenue']:,.0f}")
    print(f"    - Delivered          : PKR {report['delivered_revenue']:,.0f}")
    print(f"    - Pending            : PKR {report['pending_revenue']:,.0f}")
    print(f"  Returned (not counted) : PKR {report['returned_value']:,.0f}")
    print(f"  Return rate            : {report['return_rate_pct']:.1f}%")
    print(f"  Average order value    : PKR {report['avg_order_value']:,.0f}")
    print("\n  Orders by status:")
    for status, count in report["orders_by_status"].items():
        print(f"    {status:<10} {count}")
    print("\n  Revenue by city (highest first):")
    ranked = sorted(report["revenue_by_city"].items(), key=lambda pair: pair[1], reverse=True)
    for city, revenue in ranked:
        print(f"    {city:<12} PKR {revenue:>10,.0f}")
    print("\n  Units sold by item (highest first):")
    ranked = sorted(report["units_by_item"].items(), key=lambda pair: pair[1], reverse=True)
    for item, units in ranked:
        print(f"    {item:<20} {units}")
    print(f"\n  Top city          : {report['top_city']}")
    print(f"  Best-selling item : {report['best_selling_item']}")
    print("=" * 52)


def display_orders(orders):
    """Print a list of orders as a table, with a count at the bottom."""
    if not orders:
        print("  (no orders to show)")
        return
    print(f"\n  {'ID':<8}{'Customer':<18}{'City':<12}{'Item':<20}{'Qty':>4}{'Total (PKR)':>13}  {'Date':<11}{'Status'}")
    print("  " + "-" * 98)
    for order in orders:
        print(f"  {order['order_id']:<8}{order['customer_name']:<18}{order['city']:<12}"
              f"{order['item']:<20}{order['quantity']:>4}{order_total(order):>13,.0f}  "
              f"{order['order_date']:<11}{order['status']}")
    print(f"\n  {len(orders)} order(s) shown.")


def ask_until_valid(prompt, parser):
    """Keep asking until the parser accepts the answer, then return the clean value."""
    while True:
        raw = input(prompt)
        try:
            return parser(raw)
        except ValueError as error:
            print(f"  [!] {error}")


def show_menu(role):
    """Print the menu. The delete option is shown to admins only."""
    print("\n------ RANGG ROOP ORDER PORTAL ------")
    print("  1. Add new order")
    print("  2. View all orders")
    print("  3. Search orders")
    print("  4. Update order status")
    print("  5. Sales report")
    if role == "admin":
        print("  6. Delete an order (admin)")
    print("  0. Exit")


def prompt_add_order(orders, orders_file):
    """Collect details from the user, add the order, and append it to the file."""
    print("\nNew order (press Ctrl+C to cancel)")
    name = ask_until_valid("  Customer name: ", lambda r: parse_text(r, "Customer name"))
    city = ask_until_valid("  City: ", lambda r: parse_text(r, "City"))
    item = ask_until_valid("  Item: ", lambda r: parse_text(r, "Item"))
    quantity = ask_until_valid("  Quantity: ", parse_quantity)
    price = ask_until_valid("  Unit price (PKR): ", parse_price)
    today = datetime.now().strftime("%Y-%m-%d")
    order_date = ask_until_valid(f"  Date [Enter = {today}]: ", lambda r: parse_date(r or today))
    status = ask_until_valid("  Status [Pending/Delivered/Returned, Enter = Pending]: ",
                             lambda r: parse_status(r or "Pending"))

    order = add_record(orders, name, city, item, quantity, price, order_date, status)
    if append_order(orders_file, order):
        print(f"  Saved. New order ID: {order['order_id']}  (total PKR {order_total(order):,.0f})")
    else:
        print(f"  Order {order['order_id']} is in memory but was NOT saved to the file.")


def prompt_search(orders):
    """Ask for a keyword and show the matching orders."""
    keyword = input("  Search (ID, customer, city, item or status): ")
    results = search_record(orders, keyword)
    if results:
        display_orders(results)
    else:
        print("  No matching orders found.")


def prompt_update_status(orders, orders_file):
    """Ask for an order ID and a new status, then save the file."""
    order_id = input("  Order ID to update (e.g. RR-004): ")
    new_status = ask_until_valid("  New status [Pending/Delivered/Returned]: ", parse_status)
    if update_status(orders, order_id, new_status):
        saved = save_orders(orders_file, orders)
        print("  Status updated and saved." if saved else "  Updated in memory only, file NOT saved.")
    else:
        print(f"  No order found with ID '{order_id.strip()}'.")


def prompt_delete(orders, orders_file):
    """Ask for an order ID, confirm, delete it, then save the file."""
    order_id = input("  Order ID to delete: ")
    order = find_order(orders, order_id)
    if order is None:
        print(f"  No order found with ID '{order_id.strip()}'.")
        return
    confirm = input(f"  Type YES to delete {order['order_id']} ({order['customer_name']}): ")
    if confirm.strip() == "YES":
        delete_record(orders, order['order_id'])
        saved = save_orders(orders_file, orders)
        print("  Order deleted and saved." if saved else "  Deleted in memory only, file NOT saved.")
    else:
        print("  Cancelled. Nothing was deleted.")


def main(orders_file=ORDERS_FILE, users_file=USERS_FILE):
    """Run the portal: login, then a menu loop until the user exits."""
    print("=" * 40)
    print("   RANGG ROOP ORDER PORTAL")
    print("=" * 40)
    try:
        users = load_users(users_file)
        session = user_login(users)
        if session is None:
            return
        orders = load_orders(orders_file)

        while True:
            show_menu(session["role"])
            choice = input("Choose an option: ").strip()

            if choice == "1":
                prompt_add_order(orders, orders_file)
            elif choice == "2":
                display_orders(orders)
            elif choice == "3":
                prompt_search(orders)
            elif choice == "4":
                prompt_update_status(orders, orders_file)
            elif choice == "5":
                print_report(generate_report(orders))
            elif choice == "6" and session["role"] == "admin":
                prompt_delete(orders, orders_file)
            elif choice == "6":
                print("  Only admins can delete orders.")
            elif choice == "0":
                break
            else:
                print("  Invalid choice. Please type a number from the menu.")
    except (KeyboardInterrupt, EOFError):
        print("\n  Input interrupted. Closing the portal.")
    finally:
        print("Session closed. Goodbye.")


if __name__ == "__main__":
    main()
