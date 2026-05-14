"""
============================================================
  KORING'S KARINDERIA ORDER SYSTEM WITH DAILY PROFIT ANALYSIS
  Refactored with: OOP, Loops, Functions, Tuples, Sets,
  Recursion, Encapsulation, Inheritance, Polymorphism
============================================================
"""

import datetime
import os
import mysql.connector
from mysql.connector import Error


# ══════════════════════════════════════════════
#  DATABASE CONFIGURATION (Tuple -- immutable)
# ══════════════════════════════════════════════

DB_CONFIG = {
    "host":               "127.0.0.1",
    "port":               3306,
    "database":           "test",
    "user":               "root",
    "password":           "",
    "connection_timeout": 10,
    "ssl_disabled":       True,
}

# Tuple: valid port options (immutable, ordered)
VALID_PORTS = (3306, 3307)

# Set: valid yes/no inputs
YES_INPUTS = {"y", "yes"}
NO_INPUTS  = {"n", "no"}

# ── ASCII Icon Constants (no emojis) ──
ICON_OK      = "[OK]"
ICON_ERR     = "[!!]"
ICON_WARN    = "[??]"
ICON_SAVE    = "[DB]"
ICON_MENU    = "[**]"
ICON_ORDER   = "[>>]"
ICON_HIST    = "[==]"
ICON_REPORT  = "[$$]"
ICON_EXIT    = "[<<]"
ICON_ADD     = "[+]"
ICON_EDIT    = "[~]"
ICON_DEL     = "[x]"
ICON_VIEW    = "[i]"
ICON_CONN    = "[~]"
ICON_RECEIPT = "[R]"
ICON_BEST    = "[*]"
ICON_DATE    = "[D]"
ICON_BOX     = "[#]"


# ══════════════════════════════════════════════
#  BASE CLASS -- DatabaseEntity
#  (Encapsulation + reusable connection logic)
# ══════════════════════════════════════════════

class DatabaseEntity:
    """Base class providing shared DB connection for all entities."""

    # ── No Parameters, No Return Value ──
    def _print_divider(self):
        print("  " + "-" * 58)

    # ── No Parameters, No Return Value ──
    def _print_double_divider(self):
        print("  " + "=" * 58)

    # ── With Parameters, No Return Value ──
    def _print_section(self, title):
        """Print a decorated section header."""
        W     = 58
        inner = f"  {title}  "
        side  = (W - len(inner)) // 2
        print("  +" + "-" * (W - 2) + "+")
        print("  |" + " " * side + inner + " " * (W - 2 - side - len(inner)) + "|")
        print("  +" + "-" * (W - 2) + "+")

    # ── No Parameters, With Return Value ──
    def _get_connection(self):
        """Try each port in VALID_PORTS tuple."""
        for port in VALID_PORTS:                  # For loop over tuple
            try:
                cfg  = {**DB_CONFIG, "port": port}
                conn = mysql.connector.connect(**cfg)
                return conn
            except Error:
                continue                           # Continue to next port
        print(f"\n  {ICON_ERR} Database connection failed.")
        return None

    # ── With Parameters, With Return Value ──
    def _execute_query(self, sql, params=None, fetch=False, many=False):
        """Generic query executor. Returns rows if fetch=True."""
        conn = self._get_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            if many:
                cursor.executemany(sql, params)
            else:
                cursor.execute(sql, params or ())
            if fetch:
                return cursor.fetchall()
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            conn.rollback()
            print(f"  {ICON_ERR} Query error: {e}")
            return None
        finally:
            cursor.close()
            conn.close()


# ══════════════════════════════════════════════
#  MENU CLASS -- inherits DatabaseEntity
#  (Inheritance + Encapsulation)
# ══════════════════════════════════════════════

class Menu(DatabaseEntity):
    """Manages all menu-related operations."""

    # Constructor
    def __init__(self):
        self.__items = {}          # Encapsulated: private dict of menu items

    # ── No Parameters, With Return Value ──
    def load(self):
        """Load active menu items from DB. Returns dict."""
        rows = self._execute_query(
            "SELECT name, price, cost FROM menu WHERE is_active = 1 ORDER BY name",
            fetch=True
        )
        if rows is None:
            return {}
        self.__items = {
            row["name"]: {"price": float(row["price"]), "cost": float(row["cost"])}
            for row in rows
        }
        return self.__items

    # ── No Parameters, No Return Value ──
    def display(self):
        """Print the menu table."""
        items = self.load()
        print()
        self._print_section("CURRENT MENU")
        print(f"  | {'No.':<4} {'Item':<22} {'Price':>8}  {'Cost':>8}  {'Margin':>8} |")
        self._print_divider()

        idx        = 1                            # While loop
        item_names = list(items.keys())
        while idx <= len(item_names):
            name   = item_names[idx - 1]
            info   = items[name]
            margin = info["price"] - info["cost"]
            print(f"  | {idx:<4} {name:<22} P{info['price']:>7.2f}  P{info['cost']:>7.2f}  P{margin:>7.2f} |")
            idx += 1
        self._print_divider()

    # ── With Parameters, No Return Value ──
    def add_item(self, name, price, cost):
        """Insert or re-activate a menu item."""
        self._execute_query(
            "INSERT INTO menu (name, price, cost) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE price=%s, cost=%s, is_active=1",
            (name, price, cost, price, cost)
        )
        print(f"  {ICON_OK} '{name}' saved to database.")

    # ── With Parameters, No Return Value ──
    def update_item(self, name, price, cost):
        """Update price and cost of an existing item."""
        self._execute_query(
            "UPDATE menu SET price=%s, cost=%s WHERE name=%s",
            (price, cost, name)
        )
        print(f"  {ICON_OK} '{name}' updated in database.")

    # ── With Parameters, No Return Value ──
    def remove_item(self, name):
        """Soft-delete a menu item."""
        self._execute_query(
            "UPDATE menu SET is_active=0 WHERE name=%s", (name,)
        )
        print(f"  {ICON_OK} '{name}' removed from menu.")

    # ── No Parameters, With Return Value ──
    def get_items(self):
        """Return the currently loaded menu dict (encapsulated access)."""
        return self.__items if self.__items else self.load()

    # ── With Parameters, With Return Value ──
    def item_exists(self, name):
        """Check if item name is in the loaded menu. Returns bool."""
        return name in self.get_items()

    # ── Recursive Function ──
    def calculate_total_margin(self, item_names, index=0, total=0.0):
        """Recursively sum up margin across all items."""
        if index >= len(item_names):              # Base case
            return total
        name   = item_names[index]
        items  = self.get_items()
        margin = items[name]["price"] - items[name]["cost"]
        return self.calculate_total_margin(item_names, index + 1, total + margin)

    # ── No Parameters, No Return Value ──
    def manage(self):
        """Interactive menu management loop."""
        while True:                               # While loop
            self.load()
            print()
            self._print_section("MENU MANAGEMENT")
            # Tuple of options (immutable list of choices)
            options = (
                ("1", ICON_VIEW, "View Menu"),
                ("2", ICON_ADD,  "Add Item"),
                ("3", ICON_EDIT, "Update Item"),
                ("4", ICON_DEL,  "Remove Item"),
                ("0", ICON_EXIT, "Back"),
            )
            for key, icon, label in options:      # For loop over tuple
                print(f"  |  [{key}]  {icon}  {label:<44}|")
            self._print_double_divider()
            choice = input("  Choose: ").strip()

            if choice == "1":
                self.display()
                input("\n  Press Enter to continue...")
            elif choice == "2":
                self._prompt_add()
                input("\n  Press Enter to continue...")
            elif choice == "3":
                self._prompt_update()
                input("\n  Press Enter to continue...")
            elif choice == "4":
                self._prompt_remove()
                input("\n  Press Enter to continue...")
            elif choice == "0":
                break
            else:
                print(f"  {ICON_ERR} Invalid choice.")

    # ── No Parameters, No Return Value ──
    def _prompt_add(self):
        print()
        self._print_section("ADD NEW MENU ITEM")
        name = input("  Item name         : ").strip().title()
        if not name:
            print(f"  {ICON_ERR} Name cannot be empty.")
            return
        try:
            price = float(input("  Selling price (P)  : "))
            cost  = float(input("  Ingredient cost (P): "))
            if price <= 0 or cost <= 0:
                raise ValueError
        except ValueError:
            print(f"  {ICON_ERR} Invalid amount.")
            return
        self.add_item(name, price, cost)

    # ── No Parameters, No Return Value ──
    def _prompt_update(self):
        print()
        self._print_section("UPDATE MENU ITEM")
        self.display()
        name = input("  Enter item name to update: ").strip().title()
        if not self.item_exists(name):
            print(f"  {ICON_ERR} '{name}' not found.")
            return
        items = self.get_items()
        try:
            price = float(input(f"  New price (current P{items[name]['price']:.2f}): "))
            cost  = float(input(f"  New cost  (current P{items[name]['cost']:.2f}):  "))
            if price <= 0 or cost <= 0:
                raise ValueError
        except ValueError:
            print(f"  {ICON_ERR} Invalid amount.")
            return
        self.update_item(name, price, cost)

    # ── No Parameters, No Return Value ──
    def _prompt_remove(self):
        print()
        self._print_section("REMOVE MENU ITEM")
        self.display()
        name = input("  Enter item name to remove: ").strip().title()
        if not self.item_exists(name):
            print(f"  {ICON_ERR} '{name}' not found.")
            return
        confirm = input(f"  Remove '{name}'? (y/n): ").strip().lower()
        if confirm not in YES_INPUTS:             # Set membership check
            print("  Cancelled.")
            return
        self.remove_item(name)


# ══════════════════════════════════════════════
#  ORDER CLASS -- inherits DatabaseEntity
#  (Inheritance + Encapsulation)
# ══════════════════════════════════════════════

class Order(DatabaseEntity):
    """Handles customer order recording."""

    # Constructor
    def __init__(self, customer_name="Walk-in Customer"):
        self.__customer  = customer_name          # Encapsulated
        self.__items     = []                     # List of ordered items
        self.__order_id  = None
        self.__timestamp = None

    # ── No Parameters, With Return Value ──
    def get_customer(self):
        return self.__customer

    # ── No Parameters, With Return Value ──
    def get_order_id(self):
        return self.__order_id

    # ── With Parameters, No Return Value ──
    def add_item(self, item_name, qty, price, cost):
        """Append an item dict to the order list."""
        self.__items.append({
            "item":  item_name,
            "qty":   qty,
            "price": price,
            "cost":  cost,
        })

    # ── No Parameters, With Return Value ──
    def calculate_totals(self):
        """Return (total_sales, total_cost, profit) as a tuple."""
        total_sales = sum(o["price"] * o["qty"] for o in self.__items)
        total_cost  = sum(o["cost"]  * o["qty"] for o in self.__items)
        profit      = total_sales - total_cost
        return (total_sales, total_cost, profit)  # Tuple return

    # ── No Parameters, No Return Value ──
    def save(self):
        """Persist order and its items to the database."""
        if not self.__items:
            print(f"  {ICON_WARN} No items to save.")
            return
        total_sales, total_cost, profit = self.calculate_totals()
        self.__timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        order_id = self._execute_query(
            "INSERT INTO orders (customer, total_sales, total_cost, profit, created_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (self.__customer, total_sales, total_cost, profit, self.__timestamp)
        )
        if order_id is None:
            print(f"  {ICON_ERR} Failed to save order.")
            return
        self.__order_id = order_id

        rows = [
            (order_id, o["item"], o["qty"], o["price"], o["cost"])
            for o in self.__items
        ]
        self._execute_query(
            "INSERT INTO order_items (order_id, item_name, quantity, price, cost) "
            "VALUES (%s, %s, %s, %s, %s)",
            rows, many=True
        )
        print(f"\n  {ICON_SAVE} Order #{self.__order_id} saved to database.")

    # ── No Parameters, No Return Value ──
    def print_receipt(self):
        """Print formatted receipt to console."""
        if self.__order_id is None:
            print(f"  {ICON_WARN} Order not saved yet.")
            return
        total_sales, total_cost, profit = self.calculate_totals()
        W = 46
        print(f"\n  +{'=' * W}+")
        print(f"  |{'OFFICIAL RECEIPT':^{W}}|")
        print(f"  |{"Koring's Karinderia":^{W}}|")
        print(f"  +{'=' * W}+")
        print(f"  | {ICON_RECEIPT} Order No. : #{self.__order_id:<{W - 17}}|")
        print(f"  | Customer  : {self.__customer:<{W - 13}}|")
        print(f"  | Date/Time : {self.__timestamp:<{W - 13}}|")
        print(f"  +{'-' * W}+")
        print(f"  | {'QTY':<5} {'ITEM':<24} {'SUBTOTAL':>12} |")
        print(f"  +{'-' * W}+")
        for o in self.__items:                    # For loop over list
            subtotal = o['qty'] * o['price']
            print(f"  | {o['qty']:<5} {o['item']:<24} P{subtotal:>11.2f} |")
        print(f"  +{'=' * W}+")
        print(f"  | {'TOTAL SALES':<30} P{total_sales:>11.2f} |")
        print(f"  | {'Ingredient Cost':<30} P{total_cost:>11.2f} |")
        print(f"  | {'Gross Profit':<30} P{profit:>11.2f} |")
        print(f"  +{'=' * W}+")
        print(f"  |{'Salamat!  Thank you for dining with us!':^{W}}|")
        print(f"  +{'=' * W}+")

    # ── Recursive Function ──
    def count_total_items(self, index=0, total=0):
        """Recursively count total quantity of all order items."""
        if index >= len(self.__items):            # Base case
            return total
        return self.count_total_items(index + 1, total + self.__items[index]["qty"])


# ══════════════════════════════════════════════
#  ORDER RECORDER -- Polymorphism via record()
# ══════════════════════════════════════════════

class OrderRecorder(DatabaseEntity):
    """Handles the interactive order-taking flow."""

    # Constructor
    def __init__(self, menu: Menu):
        self.__menu = menu

    # ── No Parameters, No Return Value ── (Polymorphic entry point)
    def record(self):
        """Main order recording workflow."""
        items = self.__menu.load()
        if not items:
            print(f"  {ICON_WARN} Menu is empty. Please add items first.")
            return

        print()
        self._print_section("RECORD CUSTOMER ORDER")

        raw_name = input("  Customer name (or Enter to skip): ").strip()
        customer = raw_name if raw_name else "Walk-in Customer"

        order      = Order(customer)
        items_list = list(items.keys())

        print()
        self._print_divider()
        print(f"  | {'#':<5} {'ITEM':<28} {'PRICE':>10}     |")
        self._print_divider()
        for idx, name in enumerate(items_list, 1):   # For loop with enumerate
            print(f"  | [{idx:<3}] {name:<28} P{items[name]['price']:>9.2f}     |")
        self._print_divider()

        print(f"\n  Enter item number & quantity  (type 0 to finish)")
        print(f"  {'.' * 58}")

        # Set to track added item indices
        added_indices = set()

        while True:                               # While loop
            try:
                raw = input("  Item no. (0 to finish): ").strip()
                if raw == "0":
                    break
                item_no = int(raw)
                if item_no < 1 or item_no > len(items_list):
                    print(f"  {ICON_ERR} Invalid item number.")
                    continue                       # Continue to next iteration
                qty = int(input("  Quantity           : ").strip())
                if qty <= 0:
                    print(f"  {ICON_ERR} Quantity must be at least 1.")
                    continue
                selected = items_list[item_no - 1]
                order.add_item(selected, qty, items[selected]["price"], items[selected]["cost"])
                added_indices.add(item_no)        # Set tracking added items
                subtotal = items[selected]["price"] * qty
                print(f"  {ICON_OK} {qty}x {selected} = P{subtotal:.2f}  (added)")
            except ValueError:
                print(f"  {ICON_ERR} Please enter a valid number.")

        totals = order.calculate_totals()
        if totals[0] == 0:
            print(f"  {ICON_WARN} No items ordered. Cancelled.")
            return

        total_qty = order.count_total_items()     # Recursive call
        print(f"\n  {ICON_BOX} Total items ordered : {total_qty} pcs")

        order.save()
        order.print_receipt()


# ══════════════════════════════════════════════
#  REPORT CLASS -- inherits DatabaseEntity
#  (Inheritance + Polymorphism via generate())
# ══════════════════════════════════════════════

class Report(DatabaseEntity):
    """Base class for all report types."""

    # Constructor
    def __init__(self, date_filter=None):
        if date_filter:
            self._date_filter = date_filter
        else:
            self._date_filter = datetime.date.today().isoformat()
        self._date_str = datetime.datetime.strptime(
            self._date_filter, "%Y-%m-%d"
        ).strftime("%B %d, %Y")

    # ── No Parameters, No Return Value ── (Polymorphic -- overridden in subclass)
    def generate(self):
        raise NotImplementedError("Subclasses must implement generate()")


class DailyReport(Report):
    """End-of-day financial report. Inherits from Report."""

    # Constructor (calls parent)
    def __init__(self, date_filter=None):
        super().__init__(date_filter)
        self.__summary   = None       # Encapsulated
        self.__item_rows = []

    # ── No Parameters, With Return Value ──
    def _fetch_summary(self):
        rows = self._execute_query("""
            SELECT COUNT(*) AS total_orders, SUM(total_sales) AS total_sales,
                   SUM(total_cost) AS total_cost, SUM(profit) AS total_profit
            FROM orders WHERE DATE(created_at) = %s
        """, (self._date_filter,), fetch=True)
        return rows[0] if rows else None

    # ── No Parameters, With Return Value ──
    def _fetch_best_seller(self):
        rows = self._execute_query("""
            SELECT oi.item_name, SUM(oi.quantity) AS total_qty
            FROM order_items oi JOIN orders o ON oi.order_id = o.id
            WHERE DATE(o.created_at) = %s
            GROUP BY oi.item_name ORDER BY total_qty DESC LIMIT 1
        """, (self._date_filter,), fetch=True)
        if rows:
            best = rows[0]
            return f"{best['item_name']} ({best['total_qty']} pcs)"
        return "N/A"

    # ── No Parameters, With Return Value ──
    def _fetch_item_breakdown(self):
        return self._execute_query("""
            SELECT oi.item_name, SUM(oi.quantity) AS total_qty,
                   SUM(oi.quantity * oi.price) AS item_sales
            FROM order_items oi JOIN orders o ON oi.order_id = o.id
            WHERE DATE(o.created_at) = %s
            GROUP BY oi.item_name ORDER BY total_qty DESC
        """, (self._date_filter,), fetch=True) or []

    # ── Recursive Function ──
    def _sum_item_sales(self, rows, index=0, total=0.0):
        """Recursively compute total sales from item breakdown rows."""
        if index >= len(rows):                    # Base case
            return total
        return self._sum_item_sales(rows, index + 1, total + float(rows[index]["item_sales"]))

    # ── No Parameters, No Return Value ── (Polymorphic override)
    def generate(self):
        """Generate and display the daily financial report."""
        print()
        self._print_section("END-OF-DAY FINANCIAL REPORT")

        summary = self._fetch_summary()
        if not summary or not summary["total_orders"]:
            print(f"  {ICON_WARN} No transactions found for {self._date_filter}.")
            return

        self.__summary   = summary
        self.__item_rows = self._fetch_item_breakdown()

        total_sales  = float(summary["total_sales"]  or 0)
        total_cost   = float(summary["total_cost"]   or 0)
        total_profit = float(summary["total_profit"] or 0)
        num_orders   = summary["total_orders"]
        best_seller  = self._fetch_best_seller()

        # Verify totals recursively
        recursive_total = self._sum_item_sales(self.__item_rows)

        W = 56
        print(f"  +{'=' * W}+")
        print(f"  | {ICON_DATE}  Date           : {self._date_str:<{W - 22}}|")
        print(f"  | [#]  Total Orders   : {str(num_orders):<{W - 22}}|")
        print(f"  +{'-' * W}+")
        print(f"  | [+]  Total Sales    : P{total_sales:>{W - 25},.2f}  |")
        print(f"  | [-]  Total Cost     : P{total_cost:>{W - 25},.2f}  |")
        print(f"  | [=]  Gross Profit   : P{total_profit:>{W - 25},.2f}  |")
        if total_sales > 0:
            pct = (total_profit / total_sales) * 100
            print(f"  | [%]  Profit Margin  : {pct:>{W - 24}.1f}%  |")
        print(f"  | {ICON_BEST}  Best Seller    : {best_seller:<{W - 22}}|")
        print(f"  | {ICON_OK}  Sales Verified : P{recursive_total:>{W - 25},.2f}  |")
        print(f"  +{'=' * W}+")

        print(f"\n  ITEM SALES BREAKDOWN:")
        self._print_divider()
        print(f"  | {'ITEM':<24} {'QTY':>6}  {'SALES':>12}      |")
        self._print_divider()
        for row in self.__item_rows:              # For loop
            print(f"  | {row['item_name']:<24} {int(row['total_qty']):>6}  "
                  f"P{float(row['item_sales']):>11.2f}      |")
        self._print_divider()

        self._save_to_file(total_sales, total_cost, total_profit, num_orders,
                           best_seller, self.__item_rows)

    # ── With Parameters, No Return Value ──
    def _save_to_file(self, total_sales, total_cost, total_profit,
                      num_orders, best_seller, item_rows):
        filename = f"karinderia_report_{self._date_filter.replace('-','')}.txt"
        lines = [
            "=" * 60,
            "   KORING'S KARINDERIA -- END-OF-DAY FINANCIAL REPORT",
            "=" * 60,
            f"  Date          : {self._date_str}",
            f"  Total Orders  : {num_orders}",
            f"  Total Sales   : P{total_sales:,.2f}",
            f"  Total Cost    : P{total_cost:,.2f}",
            f"  Gross Profit  : P{total_profit:,.2f}",
        ]
        if total_sales > 0:
            lines.append(f"  Profit Margin : {(total_profit/total_sales)*100:.1f}%")
        lines.append(f"  Best Seller   : {best_seller}")
        lines.append("")
        lines.append("  ITEM SALES BREAKDOWN:")
        lines.append("  " + "-" * 48)
        for row in item_rows:                     # Nested for loop (inside method)
            lines.append(
                f"    {row['item_name']:<22} {int(row['total_qty']):>4} pcs  "
                f"P{float(row['item_sales']):>9.2f}"
            )
        lines.append("=" * 60)
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"\n  {ICON_SAVE} Report saved to: {filename}")


# ══════════════════════════════════════════════
#  TRANSACTION HISTORY CLASS -- inherits Report
#  (Inheritance + Polymorphism)
# ══════════════════════════════════════════════

class TransactionHistory(Report):
    """View historical orders by date. Inherits from Report."""

    def __init__(self, date_filter=None):
        super().__init__(date_filter)

    # ── No Parameters, No Return Value ── (Polymorphic override)
    def generate(self):
        """Fetch and display orders for the selected date."""
        print()
        self._print_section("TRANSACTION HISTORY")
        print(f"  Showing records for: {self._date_str}")
        self._print_divider()

        orders = self._execute_query(
            "SELECT * FROM orders WHERE DATE(created_at) = %s ORDER BY created_at",
            (self._date_filter,), fetch=True
        )
        if not orders:
            print(f"  {ICON_WARN} No transactions found for {self._date_filter}.")
            return

        for order in orders:                      # Outer for loop (nested)
            print(f"\n  +-- Order #{order['id']:03d} "
                  f"| {order['created_at']} "
                  f"| {order['customer']}")
            items = self._execute_query(
                "SELECT * FROM order_items WHERE order_id = %s",
                (order["id"],), fetch=True
            ) or []
            for item in items:                    # Inner for loop (nested loop)
                subtotal = float(item["quantity"]) * float(item["price"])
                print(f"  |    > {item['quantity']}x {item['item_name']:<24} P{subtotal:>8.2f}")
            print(f"  |   " + "-" * 48)
            print(f"  |   Sales  : P{float(order['total_sales']):>9.2f}  "
                  f"Cost  : P{float(order['total_cost']):>9.2f}  "
                  f"Profit: P{float(order['profit']):>9.2f}")
            print(f"  +" + "." * 55)

        self._print_double_divider()
        print(f"  {ICON_BOX} Total orders on {self._date_filter}: {len(orders)}")


# ══════════════════════════════════════════════
#  KARINDERIA APP -- main controller class
# ══════════════════════════════════════════════

class KarinderiaApp(DatabaseEntity):
    """Main application controller."""

    # Constructor
    def __init__(self):
        self.__menu     = Menu()              # Composition
        self.__recorder = OrderRecorder(self.__menu)

    # ── No Parameters, No Return Value ──
    def _banner(self):
        print()
        print("  +====================================================+")
        print("  |                                                    |")
        print("  |       KORING'S KARINDERIA ORDER SYSTEM             |")
        print("  |             Daily Profit Analysis                  |")
        print("  |                                                    |")
        print("  +====================================================+")

    # ── No Parameters, With Return Value ──
    def _check_connection(self):
        print(f"  {ICON_CONN} Connecting to database...")
        conn = self._get_connection()
        if conn:
            print(f"  {ICON_OK} Connected to '{DB_CONFIG['database']}' on {DB_CONFIG['host']}")
            conn.close()
            return True
        return False

    # ── With Parameters, With Return Value ──
    def _get_date_input(self, prompt="  Date (YYYY-MM-DD) or Enter for today: "):
        """Prompt user for a date string. Returns today if blank."""
        raw = input(prompt).strip()
        return raw if raw else datetime.date.today().isoformat()

    # ── No Parameters, No Return Value ──
    def run(self):
        """Main application loop."""
        os.system("cls" if os.name == "nt" else "clear")
        self._banner()
        if not self._check_connection():
            print(f"\n  {ICON_WARN} Could not connect to the database. Exiting.")
            return

        # Tuple of main menu options (immutable)
        main_options = (
            ("1", ICON_MENU,   "Menu Management"),
            ("2", ICON_ORDER,  "Record Customer Order"),
            ("3", ICON_HIST,   "View Transaction History"),
            ("4", ICON_REPORT, "Generate Daily Financial Report"),
            ("0", ICON_EXIT,   "Exit"),
        )

        while True:                               # Main while loop
            os.system("cls" if os.name == "nt" else "clear")
            self._banner()
            now = datetime.datetime.now()
            print(f"\n  Today    : {now.strftime('%A, %B %d, %Y')}")
            print(f"  Time     : {now.strftime('%I:%M %p')}")
            print(f"  Database : {DB_CONFIG['database']}@{DB_CONFIG['host']}")
            print()
            print("  +====================================================+")
            print("  |                    MAIN MENU                       |")
            print("  +----------------------------------------------------+")

            for key, icon, label in main_options: # For loop over tuple
                print(f"  |   [{key}]  {icon}  {label:<36}  |")

            print("  +====================================================+")

            choice = input("  Choose an option: ").strip()

            if choice == "1":
                self.__menu.manage()

            elif choice == "2":
                self.__recorder.record()
                input("\n  Press Enter to continue...")

            elif choice == "3":
                date    = self._get_date_input("  Filter by date (YYYY-MM-DD) or Enter for today: ")
                history = TransactionHistory(date)  # Polymorphism: Report subclass
                history.generate()
                input("\n  Press Enter to continue...")

            elif choice == "4":
                date   = self._get_date_input("  Report date (YYYY-MM-DD) or Enter for today: ")
                report = DailyReport(date)          # Polymorphism: Report subclass
                report.generate()
                input("\n  Press Enter to continue...")

            elif choice == "0":
                print()
                print("  +====================================================+")
                print("  |   Salamat sa inyong tiwala!  Ingat lagi!           |")
                print("  +====================================================+")
                print()
                break                             # Break out of main loop

            else:
                print(f"  {ICON_ERR} Invalid choice.")
                input("  Press Enter to continue...")


# ══════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════

if __name__ == "__main__":
    app = KarinderiaApp()
    app.run()
