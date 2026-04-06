"""
main.py
-------
Command-line interface (CLI) for the Palm Vein Based Secure Payment System.

Menu options:
  1. Register a new user
  2. Make a payment
  3. View user balance & profile
  4. View transaction history
  5. View authentication logs
  6. List available dataset images
  7. Demo: auto-register sample users from dataset
  0. Exit
"""

import os
import sys

# ── Make sure sibling modules are importable ──────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

import database
import payment_processing
import palm_authentication


# ──────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
BANNER = """
╔══════════════════════════════════════════════════════╗
║   PALM VEIN BASED SECURE PAYMENT SYSTEM              ║
║   Simulation — College Software Engineering Project  ║
╚══════════════════════════════════════════════════════╝
"""


# ──────────────────────────────────────────────
# DISPLAY HELPERS
# ──────────────────────────────────────────────

def print_menu():
    print("""
┌─────────────────────────────────────────┐
│               MAIN MENU                 │
├─────────────────────────────────────────┤
│  1. Register New User                   │
│  2. Make a Payment                      │
│  3. View User Profile & Balance         │
│  4. View Transaction History            │
│  5. View Authentication Logs            │
│  6. List Dataset Images                 │
│  7. Demo: Auto-Register Sample Users    │
│  0. Exit                                │
└─────────────────────────────────────────┘""")


def divider(char="─", width=50):
    print(char * width)


# ──────────────────────────────────────────────
# MENU ACTIONS
# ──────────────────────────────────────────────

def action_register_user():
    """Prompt for user details and register via payment_processing."""
    print("\n── Register New User ──")
    user_id = input("Enter User ID       : ").strip()
    name    = input("Enter Full Name     : ").strip()

    # Show available images to help the user pick one
    images = palm_authentication.list_dataset_images(DATASET_DIR)
    if images:
        print(f"\n  {len(images)} image(s) found in dataset folder.")
        print("  Example paths:")
        for img in images[:5]:
            print(f"    {img}")
        if len(images) > 5:
            print(f"    ... and {len(images) - 5} more.")

    palm_path = input("\nEnter palm image path: ").strip()

    result = payment_processing.register_user(user_id, name, palm_path)

    if result["success"]:
        print(f"\n  ✔ {result['message']}")
    else:
        print(f"\n  ✗ {result['message']}")


def action_make_payment():
    """Prompt for payment details, run authentication, process payment."""
    print("\n── Make a Payment ──")
    user_id = input("Enter your User ID      : ").strip()

    # Show user profile first if found
    user = database.get_user(user_id)
    if user:
        print(f"  Welcome, {user['name']}!  Balance: {user['balance']:.2f}")
    else:
        print(f"  ✗ User '{user_id}' not found.")
        return

    try:
        amount = float(input("Enter payment amount    : ").strip())
    except ValueError:
        print("  ✗ Invalid amount. Please enter a number.")
        return

    # Show dataset images to pick an input palm image
    images = palm_authentication.list_dataset_images(DATASET_DIR)
    if images:
        print(f"\n  Available images for authentication ({len(images)} total):")
        for img in images[:8]:
            print(f"    {img}")
        if len(images) > 8:
            print(f"    ... (use 'List Dataset Images' to see all)")

    input_palm = input("\nEnter palm image path for authentication: ").strip()

    result = payment_processing.process_payment(user_id, amount, input_palm)

    # Print auth details summary
    if result.get("auth_details"):
        auth = result["auth_details"]
        print(f"\n  Auth details → matches: {auth['match_count']}, "
              f"threshold: {auth['threshold']}")

    print(f"\n  {'✔' if result['success'] else '✗'} {result['message']}")
    if result.get("transaction_id"):
        print(f"  Transaction ID: {result['transaction_id']}")


def action_view_profile():
    """Display user profile and current balance."""
    print("\n── User Profile ──")
    user_id = input("Enter User ID: ").strip()
    user = database.get_user(user_id)

    if user is None:
        print(f"  ✗ User '{user_id}' not found.")
        return

    print(f"\n  User ID      : {user['user_id']}")
    print(f"  Name           : {user['name']}")
    print(f"  Balance        : {user['balance']:.2f}")
    print(f"  Palm Image     : {user['palm_image_path']}")
    print(f"  Registered     : {user['created_at']}")


def action_transaction_history():
    """Display all transactions for a user."""
    print("\n── Transaction History ──")
    user_id = input("Enter User ID: ").strip()

    user = database.get_user(user_id)
    if user is None:
        print(f"  ✗ User '{user_id}' not found.")
        return

    txns = database.get_user_transactions(user_id)

    if not txns:
        print(f"  No transactions found for '{user_id}'.")
        return

    print(f"\n  Transactions for {user['name']} ({user_id}):")
    divider()
    print(f"  {'TXN ID':<20} {'AMOUNT':>10}  {'STATUS':<10}  TIMESTAMP")
    divider()
    for t in txns:
        print(f"  {t['transaction_id']:<20} {t['amount']:>10.2f}  {t['status']:<10}  {t['timestamp']}")
    divider()
    print(f"  Total records: {len(txns)}")


def action_auth_logs():
    """Display authentication logs."""
    print("\n── Authentication Logs ──")
    choice = input("Filter by User ID? (leave blank for all): ").strip()
    user_id = choice if choice else None

    logs = database.get_auth_logs(user_id)

    if not logs:
        print("  No authentication logs found.")
        return

    divider()
    print(f"  {'LOG ID':<8} {'USER ID':<12} {'RESULT':<10}  TIMESTAMP")
    divider()
    for log in logs:
        print(f"  {log['log_id']:<8} {log['user_id']:<12} {log['result']:<10}  {log['timestamp']}")
    divider()
    print(f"  Total records: {len(logs)}")


def action_list_images():
    """List all discovered images in the dataset folder."""
    print("\n── Dataset Images ──")
    images = palm_authentication.list_dataset_images(DATASET_DIR)

    if not images:
        print(f"  No images found in: {DATASET_DIR}")
        print("  → Place your dataset folder at: dataset/")
        return

    print(f"  Found {len(images)} image(s) in '{DATASET_DIR}':\n")
    for i, path in enumerate(images, 1):
        print(f"  [{i:>3}] {path}")

def action_demo_register():
    """
    Auto-register up to 5 sample users from the dataset folder.
    Uses the first image found per sub-folder as each user's palm image.

    This demonstrates how the system works end-to-end without manual path entry.
    """
    print("\n── Demo: Auto-Register Sample Users ──")

    images = palm_authentication.list_dataset_images(DATASET_DIR)
    if not images:
        print(f"  ✗ No images found in {DATASET_DIR}.")
        print("  Place the Kaggle palm dataset inside the 'dataset/' folder and try again.")
        return

    # Take up to 5 unique images
    sample_images = images[:5]
    sample_users = [
        ("U001", "Alice Johnson"),
        ("U002", "Bob Smith"),
        ("U003", "Carol White"),
        ("U004", "David Brown"),
        ("U005", "Eva Green"),
    ]

    print(f"\n  Registering {len(sample_images)} sample user(s)...\n")
    registered = 0
    for (uid, name), img_path in zip(sample_users, sample_images):
        res = payment_processing.register_user(uid, name, img_path, balance=1000.0)
        status = "✔" if res["success"] else "✗"
        print(f"  {status} [{uid}] {name} → {os.path.basename(img_path)}")
        if res["success"]:
            registered += 1

    print(f"\n  Done. {registered} user(s) registered.")
    print("\n  You can now use option [2] to make a payment.")
    print("  Tip: Use the SAME image path as the registered palm image to simulate")
    print("  a successful authentication. Use a DIFFERENT image to simulate failure.")


def action_list_all_users():
    """Show all registered users (bonus utility)."""
    print("\n── All Registered Users ──")
    users = database.get_all_users()
    if not users:
        print("  No users registered yet.")
        return

    divider()
    print(f"  {'USER ID':<10} {'NAME':<20} {'BALANCE':>10}  REGISTERED AT")
    divider()
    for u in users:
        print(f"  {u['user_id']:<10} {u['name']:<20} {u['balance']:>10.2f}  {u['created_at']}")
    divider()
    print(f"  Total: {len(users)} user(s)")


# ──────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────

def main():
    print(BANNER)

    # Ensure dataset folder exists
    os.makedirs(DATASET_DIR, exist_ok=True)

    # Initialise the database (creates tables if not present)
    database.initialize_database()

    print("  Type a menu number and press Enter.\n")

    while True:
        print_menu()
        choice = input("\nYour choice: ").strip()

        if choice == "1":
            action_register_user()
        elif choice == "2":
            action_make_payment()
        elif choice == "3":
            action_view_profile()
        elif choice == "4":
            action_transaction_history()
        elif choice == "5":
            action_auth_logs()
        elif choice == "6":
            action_list_images()
        elif choice == "7":
            action_demo_register()
        elif choice == "8":
            # Bonus: list all users (hidden from menu, but accessible)
            action_list_all_users()
        elif choice == "0":
            print("\n  Goodbye!\n")
            sys.exit(0)
        else:
            print("\n  ✗ Invalid choice. Please enter a number from the menu.")


if __name__ == "__main__":
    main()
