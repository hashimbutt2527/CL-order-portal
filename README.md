# Rangg Roop Order Portal

A console-based order management portal for **Rangg Roop**, a small women's clothing business in Pakistan.
Staff log in, record customer orders, search them, update delivery status and generate a sales report.
All data is saved in CSV files, so nothing is lost when the program closes.

Built in pure Python (standard library only) for **Assignment 3: End-to-End Portal Design**.

**Team:** [Muhammad Hashim Butt, 25L-5241] and [Muhammad Mohsin, 25L-5020]

---

## Features

| Feature | Function | Notes |
|---|---|---|
| Login with roles | `user_login()` | `admin` and `staff`, 3 attempts, passwords stored as SHA-256 hashes |
| Add an order | `add_record()` | Every field validated before anything is saved |
| Search orders | `search_record()` | Case-insensitive, across ID, customer, city, item and status |
| Update status | `update_status()` | Pending / Delivered / Returned |
| Delete an order | `delete_record()` | Admin only, asks for confirmation |
| Sales report | `generate_report()` | Revenue by city, best-selling item, return rate, average order value |

## Project structure

```
.
├── portal.py                  # the full portal, run this in a terminal
├── Rangg_Roop_Portal.ipynb    # same code, with explanations and sample test runs
├── orders.csv                 # order data (16 sample orders)
├── users.csv                  # login accounts (passwords hashed)
└── README.md
```

## How to run

You need Python 3.8 or newer. No extra packages.

```bash
python portal.py
```

Or open `Rangg_Roop_Portal.ipynb` in Jupyter and choose **Run All**. The sample test runs in section 7 use pre-written inputs, so no typing is needed.

**Test accounts**

| Username | Password | Role |
|---|---|---|
| admin | admin123 | admin (can delete orders) |
| staff | staff123 | staff |

## Data format

`orders.csv` has one row per order:

| Column | Example |
|---|---|
| order_id | RR-001 |
| customer_name | Ayesha Khan |
| city | Lahore |
| item | Lawn 3-Piece |
| quantity | 2 |
| unit_price | 4500.0 |
| order_date | 2026-10-20 |
| status | Delivered |

The order total is not stored. It is calculated as `quantity x unit_price` whenever needed, so it can never go out of date.

## How errors are handled

The portal is built to never crash on bad input or a bad file.

| Problem | What happens |
|---|---|
| `orders.csv` missing | Created automatically with a header row |
| File locked or read-only (`PermissionError`) | Clear message, portal keeps running |
| Damaged row in the CSV | That row is skipped with a warning, the rest load |
| Letters typed as quantity or price (`ValueError`) | Rejected with a hint, the question is asked again |
| Invalid date, status, or `nan` / negative price | Rejected with a hint |
| Ctrl+C or closed input | Portal closes cleanly and prints a goodbye |

## Report revenue rule

*Returned* orders are not counted as revenue. Their value is shown separately in the report as "Returned (not counted)".
