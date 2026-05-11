import sqlite3
from pathlib import Path
from datetime import datetime
import bcrypt


# ---------------- DATABASE CONFIG ----------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "users.db"


# ---------------- CONNECTION ----------------
def get_connection():
    """
    Creates and returns a SQLite database connection.
    The users.db file will be created automatically if it does not exist.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- INITIALIZE DATABASE ----------------
def init_user_db():
    """
    Creates the users table if it does not already exist.

    This function automatically creates:
        users.db
    in your project folder.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


# ---------------- PASSWORD HASHING ----------------
def hash_password(password: str) -> str:
    """
    Converts a plain password into a secure bcrypt hash.
    Plain passwords should never be stored in the database.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Checks whether the entered password matches the stored password hash.
    """
    try:
        password_bytes = password.encode("utf-8")
        hash_bytes = password_hash.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


# ---------------- USER CHECKS ----------------
def username_exists(username: str) -> bool:
    """
    Checks whether a username already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        (username.strip(),)
    )

    user = cursor.fetchone()
    conn.close()

    return user is not None


def email_exists(email: str) -> bool:
    """
    Checks whether an email already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        (email.strip().lower(),)
    )

    user = cursor.fetchone()
    conn.close()

    return user is not None


# ---------------- CREATE USER ----------------
def create_user(full_name: str, email: str, username: str, password: str):
    """
    Creates a new user account.

    Returns:
        True, message
        False, error message
    """
    init_user_db()

    full_name = full_name.strip()
    email = email.strip().lower()
    username = username.strip()

    if not full_name:
        return False, "Full name is required."

    if not email:
        return False, "Email is required."

    if not username:
        return False, "Username is required."

    if not password:
        return False, "Password is required."

    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    if username_exists(username):
        return False, "Username already exists."

    if email_exists(email):
        return False, "Email already exists."

    password_hash = hash_password(password)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users (
                full_name,
                email,
                username,
                password_hash,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                full_name,
                email,
                username,
                password_hash,
                created_at,
            )
        )

        conn.commit()
        conn.close()

        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "Username or email already exists."

    except Exception as e:
        return False, f"Account creation failed: {str(e)}"


# ---------------- LOGIN USER ----------------
def authenticate_user(username_or_email: str, password: str):
    """
    Authenticates user login using username/email and password.

    Returns:
        True, user_data
        False, error message
    """
    init_user_db()

    username_or_email = username_or_email.strip()

    if not username_or_email:
        return False, "Username or email is required."

    if not password:
        return False, "Password is required."

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, full_name, email, username, password_hash, created_at
        FROM users
        WHERE username = ? OR email = ?
        """,
        (
            username_or_email,
            username_or_email.lower(),
        )
    )

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return False, "User not found."

    if not verify_password(password, user["password_hash"]):
        return False, "Incorrect password."

    user_data = {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "username": user["username"],
        "created_at": user["created_at"],
    }

    return True, user_data


# ---------------- GET USER DETAILS ----------------
def get_user_by_username(username: str):
    """
    Returns user details by username.
    """
    init_user_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, full_name, email, username, created_at
        FROM users
        WHERE username = ?
        """,
        (username.strip(),)
    )

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return None

    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "username": user["username"],
        "created_at": user["created_at"],
    }


def get_all_users():
    """
    Returns all registered users.
    Useful only for testing/admin checking.
    Do not show password hashes.
    """
    init_user_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, full_name, email, username, created_at
        FROM users
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()
    conn.close()

    users = []

    for row in rows:
        users.append(
            {
                "id": row["id"],
                "full_name": row["full_name"],
                "email": row["email"],
                "username": row["username"],
                "created_at": row["created_at"],
            }
        )

    return users


# ---------------- DIRECT RUN TEST ----------------
if __name__ == "__main__":
    init_user_db()
    print(f"Database created successfully at: {DB_PATH}")