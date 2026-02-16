import sqlite3
from pathlib import Path
from milestone_3.models import hash_password

DB_PATH = Path(__file__).parent / "users.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Recreate table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    users = [
        ("hr", "1234", "HR"),
        ("finance", "1234", "Finance"),
        ("eng", "1234", "Engineering"),
        ("marketing", "1234", "Marketing"),
        ("emp", "1234", "Employees"),
        ("ceo", "1234", "C-Level")
    ]

    hashed_users = [
        (u, hash_password(p), r) for (u, p, r) in users
    ]

    cursor.executemany(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        hashed_users
    )

    conn.commit()
    conn.close()

    print("Database re-initialized with HASHED passwords.")
    print("DB path:", DB_PATH)

if __name__ == "__main__":
    main()
