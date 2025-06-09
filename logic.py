import sqlite3
import csv

class ExpenseManager:
    def __init__(self): 
        self.conn = sqlite3.connect("db/roommates.db")
        self.c = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        self.c.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        self.c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                split_type TEXT,
                FOREIGN KEY(group_id) REFERENCES groups(id)
            )
        """)
        self.conn.commit()

    def register_user(self, username, password):
        try:
            self.c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def login_user(self, username, password):
        self.c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = self.c.fetchone()
        return user[0] if user else None

    def create_group(self, group_name):
        try:
            self.c.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
            self.conn.commit()
            return self.c.lastrowid
        except sqlite3.IntegrityError:
            self.c.execute("SELECT id FROM groups WHERE name=?", (group_name,))
            group = self.c.fetchone()
            return group[0] if group else None

    def add_expense(self, group_id, title, amount, split_type="Equal"):
        self.c.execute("INSERT INTO expenses (group_id, title, amount, split_type) VALUES (?, ?, ?, ?)",
                       (group_id, title, amount, split_type))
        self.conn.commit()

    def fetch_expenses(self, group_id):
        self.c.execute("SELECT id, title, amount, split_type FROM expenses WHERE group_id=?", (group_id,))
        return self.c.fetchall()

    def delete_expense(self, expense_id):
        self.c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        self.conn.commit()

    def export_to_csv(self, group_id, filename="expenses_export.csv"):
        self.c.execute("SELECT title, amount, split_type FROM expenses WHERE group_id=?", (group_id,))
        data = self.c.fetchall()
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Amount", "Split Type"])
            writer.writerows(data)

    def calculate_total(self, group_id):
        self.c.execute("SELECT SUM(amount) FROM expenses WHERE group_id=?", (group_id,))
        total = self.c.fetchone()[0]
        return total if total else 0
