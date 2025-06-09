import tkinter as tk
from tkinter import messagebox
import sqlite3

# Connect to SQLite DB (creates if not exists)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')
conn.commit()

# Define functions
def register():
    username = entry_user.get()
    password = entry_pass.get()
    if not username or not password:
        messagebox.showwarning("Input Error", "All fields are required.")
        return
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        messagebox.showinfo("Success", "User registered successfully!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists.")

def login():
    username = entry_user.get()
    password = entry_pass.get()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    if result:
        messagebox.showinfo("Success", f"Welcome, {username}!")
    else:
        messagebox.showerror("Error", "Invalid credentials.")

# Setup main window
root = tk.Tk()
root.title("Login/Register App")
root.geometry("300x200")

# Username label & entry
tk.Label(root, text="Username").pack(pady=(10, 0))
entry_user = tk.Entry(root, width=30)
entry_user.pack()

# Password label & entry
tk.Label(root, text="Password").pack(pady=(10, 0))
entry_pass = tk.Entry(root, width=30, show="*")
entry_pass.pack()

# Login & Register buttons
tk.Button(root, text="Login", command=login, width=20).pack(pady=10)
tk.Button(root, text="Register", command=register, width=20).pack()

# Start GUI
root.mainloop()
