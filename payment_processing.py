"""
payment_processing.py
---------------------
Handles the full payment lifecycle:
  1. Validate payment request (user exists, sufficient balance, positive amount).
  2. Trigger palm authentication.
  3. On success: deduct balance and record transaction.
  4. On failure: record failed transaction and authentication log.

All database side-effects are delegated to database.py.
All biometric checks are delegated to palm_authentication.py.
"""

import uuid
from datetime import datetime

import database
import palm_authentication


# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────

MAX_PAYMENT_AMOUNT = 10_000.0   # Hard cap per transaction (₹ / $ / any currency)
MIN_PAYMENT_AMOUNT = 0.01       # Minimum meaningful payment


# ──────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────

def _generate_transaction_id() -> str:
    """Generate a short, unique transaction ID."""
    return "TXN-" + str(uuid.uuid4()).replace("-", "").upper()[:12]


def _print_receipt(txn_id: str, user: dict, amount: float, status: str) -> None:
    """Print a formatted payment receipt to the console."""
    print("\n" + "=" * 50)
    print("          PAYMENT RECEIPT")
    print("=" * 50)
    print(f"  Transaction ID : {txn_id}")
    print(f"  User ID        : {user['user_id']}")
    print(f"  Name           : {user['name']}")
    print(f"  Amount         : {amount:.2f}")
    print(f"  Status         : {status}")
    print(f"  Timestamp      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if status == "SUCCESS":
        print(f"  Remaining Bal  : {user['balance'] - amount:.2f}")
    print("=" * 50 + "\n")


# ──────────────────────────────────────────────
# CORE PAYMENT FUNCTION
# ──────────────────────────────────────────────

def process_payment(user_id: str, amount: float, input_palm_image_path: str) -> dict:
    """
    Execute a complete payment transaction with palm authentication.

    Steps:
        1. Validate inputs (amount range, user existence).
        2. Check the user has sufficient balance.
        3. Run palm authentication.
        4. If authenticated → deduct balance, record SUCCESS transaction.
        5. If not authenticated → record FAILED transaction.
        6. Log the authentication attempt in every case.

    Args:
        user_id:               ID of the user initiating the payment.
        amount:                The amount to be paid.
        input_palm_image_path: Path to the palm image captured for this payment.

    Returns:
        A result dictionary:
        {
            "success":          bool,
            "transaction_id":   str | None,
            "message":          str,
            "auth_details":     dict | None
        }
    """
    result = {
        "success": False,
        "transaction_id": None,
        "message": "",
        "auth_details": None
    }

    # ── Validate amount ──────────────────────────────────
    if amount < MIN_PAYMENT_AMOUNT:
        result["message"] = f"Invalid amount. Minimum payment is {MIN_PAYMENT_AMOUNT:.2f}."
        return result

    if amount > MAX_PAYMENT_AMOUNT:
        result["message"] = f"Amount exceeds maximum limit of {MAX_PAYMENT_AMOUNT:.2f}."
        return result

    # ── Fetch user ───────────────────────────────────────
    user = database.get_user(user_id)
    if user is None:
        result["message"] = f"User '{user_id}' not found. Please register first."
        return result

    # ── Check balance ────────────────────────────────────
    if user["balance"] < amount:
        result["message"] = (
            f"Insufficient balance. "
            f"Available: {user['balance']:.2f}, Required: {amount:.2f}."
        )
        txn_id = _generate_transaction_id()
        database.record_transaction(txn_id, user_id, amount, "FAILED")
        result["transaction_id"] = txn_id
        return result

    # ── Palm Authentication ──────────────────────────────
    print(f"\n[PAYMENT] Initiating palm authentication for user '{user_id}'...")
    auth_result = palm_authentication.authenticate_palm(
        stored_image_path=user["palm_image_path"],
        input_image_path=input_palm_image_path
    )
    result["auth_details"] = auth_result

    # Log authentication attempt (success or failure)
    auth_status = "SUCCESS" if auth_result["authenticated"] else "FAILED"
    database.log_authentication(user_id, auth_status)

    # ── Process outcome ──────────────────────────────────
    txn_id = _generate_transaction_id()

    if auth_result["authenticated"]:
        # Deduct balance
        new_balance = user["balance"] - amount
        database.update_balance(user_id, new_balance)

        # Record successful transaction
        database.record_transaction(txn_id, user_id, amount, "SUCCESS")

        result["success"] = True
        result["transaction_id"] = txn_id
        result["message"] = f"Payment of {amount:.2f} processed successfully."

        # Build a mutable dict for receipt (sqlite3.Row is read-only)
        user_dict = dict(user)
        _print_receipt(txn_id, user_dict, amount, "SUCCESS")

    else:
        # Authentication failed — no balance change
        database.record_transaction(txn_id, user_id, amount, "FAILED")

        result["success"] = False
        result["transaction_id"] = txn_id
        result["message"] = (
            f"Payment rejected. {auth_result['message']}"
        )
        print(f"\n[PAYMENT] ✗ {result['message']}")

    return result


# ──────────────────────────────────────────────
# REGISTRATION HELPER
# ──────────────────────────────────────────────

def register_user(user_id: str, name: str, palm_image_path: str, balance: float = 1000.0) -> dict:
    """
    Register a new user in the system.

    Args:
        user_id:         Unique user identifier.
        name:            Full name.
        palm_image_path: Path to the user's reference palm image.
        balance:         Initial wallet balance.

    Returns:
        {"success": bool, "message": str}
    """
    import os

    # Validate image path
    if not os.path.exists(palm_image_path):
        return {
            "success": False,
            "message": f"Palm image not found at path: {palm_image_path}"
        }

    success = database.register_user(user_id, name, palm_image_path, balance)

    if success:
        return {
            "success": True,
            "message": f"User '{name}' (ID: {user_id}) registered successfully."
        }
    else:
        return {
            "success": False,
            "message": f"User ID '{user_id}' already exists."
        }
