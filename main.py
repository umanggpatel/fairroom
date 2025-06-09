import tkinter as tk
from tkinter import messagebox
import sqlite3
import os



# === Setup SQLite DB ===
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
""")
conn.commit()

# === Main Window ===
root = tk.Tk()
root.title("Login & Register App")
root.geometry("400x400")

# === Frame Switching ===
def show_frame(frame):
    frame.tkraise()

# === Register User ===
def register_user():
    fname = entry_fname.get().strip()
    lname = entry_lname.get().strip()
    email = entry_email.get().strip().lower()
    password = entry_pass_reg.get().strip()

    if not fname or not lname or not email or not password:
        messagebox.showerror("Error", "Please fill all fields.")
        return

    try:
        cursor.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
                       (fname, lname, email, password))
        conn.commit()
        messagebox.showinfo("Success", "Registered successfully!")
        clear_fields()
        show_frame(login_frame)
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Email already exists.")

# === Login User ===
def login_user():
    email = entry_email_login.get().strip().lower()
    password = entry_pass_login.get().strip()

    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()

    if user:
        full_name = f"{user[1]} {user[2]}"
        dashboard_name_label.config(text=f"Name: {full_name}")
        dashboard_email_label.config(text=f"Email: {user[3]}")
        messagebox.showinfo("Welcome", f"Welcome, {full_name}!")
        clear_fields()
        show_frame(dashboard_frame)
    else:
        messagebox.showerror("Login Failed", "Invalid email or password.")

# === Clear All Inputs ===
def clear_fields():
    entry_fname.delete(0, tk.END)
    entry_lname.delete(0, tk.END)
    entry_email.delete(0, tk.END)
    entry_pass_reg.delete(0, tk.END)
    entry_email_login.delete(0, tk.END)
    entry_pass_login.delete(0, tk.END)

# === Frames ===
register_frame = tk.Frame(root)
login_frame = tk.Frame(root)

dashboard_frame = tk.Frame(root)

# Profile labels to update after login
dashboard_name_label = tk.Label(dashboard_frame, text="", font=("Arial", 14))
dashboard_email_label = tk.Label(dashboard_frame, text="", font=("Arial", 12))

tk.Label(dashboard_frame, text="Welcome to Your Dashboard", font=("Arial", 18)).pack(pady=10)
dashboard_name_label.pack(pady=5)
dashboard_email_label.pack(pady=5)

tk.Button(dashboard_frame, text="Log Out", command=lambda: show_frame(login_frame)).pack(pady=20)


for frame in (register_frame, login_frame, dashboard_frame):
    frame.grid(row=0, column=0, sticky='nsew')

# === Register Frame UI ===
tk.Label(register_frame, text="Register", font=("Arial", 18)).pack(pady=10)

tk.Label(register_frame, text="First Name").pack()
entry_fname = tk.Entry(register_frame, width=30)
entry_fname.pack()

tk.Label(register_frame, text="Last Name").pack()
entry_lname = tk.Entry(register_frame, width=30)
entry_lname.pack()

tk.Label(register_frame, text="Email").pack()
entry_email = tk.Entry(register_frame, width=30)
entry_email.pack()

tk.Label(register_frame, text="Password").pack()
entry_pass_reg = tk.Entry(register_frame, show="*", width=30)
entry_pass_reg.pack()

tk.Button(register_frame, text="Register", command=register_user).pack(pady=10)
tk.Button(register_frame, text="Already registered? Login", command=lambda: show_frame(login_frame)).pack()

# === Login Frame UI ===
tk.Label(login_frame, text="Login", font=("Arial", 18)).pack(pady=10)

tk.Label(login_frame, text="Email").pack()
entry_email_login = tk.Entry(login_frame, width=30)
entry_email_login.pack()

tk.Label(login_frame, text="Password").pack()
entry_pass_login = tk.Entry(login_frame, show="*", width=30)
entry_pass_login.pack()

tk.Button(login_frame, text="Login", command=login_user).pack(pady=10)

text = tk.Label(login_frame, text="Don't have an account?")

register_link = tk.Label(login_frame, text=" Register Here", fg="green", cursor="hand2", font=('Arial', 10, 'underline'))
text.pack()
register_link.pack()


register_link.bind("<Button-1>", lambda e: show_frame(register_frame))

# Start on register page for first use
#show_frame(register_frame)
show_frame(login_frame)
root.mainloop()
