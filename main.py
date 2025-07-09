import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
import sqlite3
import os
from datetime import datetime, timedelta
import hashlib
import random
import string
import csv


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
cursor.execute("""
    CREATE TABLE IF NOT EXISTS balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        other_party TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT CHECK(type IN ('owes_you', 'you_owe')) NOT NULL
    )
""")
conn.commit()

# === Main Window ===


root = tk.Tk()
root.title("Login & Register")
root.geometry("400x500")
root.configure(bg="#f0f0f0")

style = ttk.Style()
style.theme_use("clam")  



# Define a custom button style
style.configure("Custom.TButton",
    background="#4caf50",
    foreground="white",
    font=("Arial", 11, "bold"),
    padding=10
)
style.map("Custom.TButton",
    background=[("active", "#45a049")],
    foreground=[("active", "white")]
)

style.configure("RoundedEntry.TEntry", relief="flat", padding=6, borderwidth=1, font=("Arial", 12))
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)


# Style Configuration 
#style = ttk.Style()
#style.theme_use("clam")  # Use a flat modern theme
#style.configure("RoundedEntry.TEntry", relief="flat", padding=6, borderwidth=1, font=("Arial", 12))


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
    global logged_in_email
    email = entry_email_login.get().strip().lower()
    password = entry_pass_login.get().strip()

    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()

    if user:
        full_name = f"{user[1]} {user[2]}"
        dashboard_greeting.config(text=f"Welcome, {full_name} 👋")
        logged_in_email=email
        messagebox.showinfo("Welcome", f"Welcome, {full_name}!")
        clear_fields()
        show_frame(dashboard_frame)
    else:
        messagebox.showerror("Login Failed", "Invalid email or password.")
        
#  Clear All Inputs
def clear_fields():
    entry_fname.delete(0, tk.END)
    entry_lname.delete(0, tk.END)
    entry_email.delete(0, tk.END)
    entry_pass_reg.delete(0, tk.END)
    entry_email_login.delete(0, tk.END)
    entry_pass_login.delete(0, tk.END)

#View Balance
def update_balances_view():
    balances_list.delete(1.0, tk.END)
    cursor.execute("SELECT other_party, amount, type FROM balances WHERE user_email=?", (logged_in_email,))
    rows = cursor.fetchall()

    if not rows:
        balances_list.insert(tk.END, "No balances found.\n")
    else:
        for party, amt, typ in rows:
            if typ == "you_owe":
                balances_list.insert(tk.END, f"You owe {party}: ${amt:.2f}\n")
            else:
                balances_list.insert(tk.END, f"{party} owes you: ${amt:.2f}\n")

    show_frame(view_balances_frame)

# Frames
register_frame = tk.Frame(root,bg="#519b71")
login_frame = tk.Frame(root,bg="#49A475")
dashboard_frame = tk.Frame(root,bg="#547a33")
view_balances_frame = tk.Frame(root, bg="#f0f0f0")

# personalized greeting
dashboard_greeting = tk.Label(dashboard_frame, text="", font=("Arial", 14))
dashboard_greeting.pack(pady=5)

# Summary Panel
summary_frame = tk.Frame(dashboard_frame)
summary_frame.pack(pady=10)

label_total_paid = tk.Label(summary_frame, text="Total expenses paid: $0")
label_total_paid.pack(anchor='w')

label_total_owed_to_you = tk.Label(summary_frame, text="Total owed by others: $0")
label_total_owed_to_you.pack(anchor='w')

label_you_owe = tk.Label(summary_frame, text="You owe: $0")
label_you_owe.pack(anchor='w')

label_last_activity = tk.Label(summary_frame, text="Last activity: None")
label_last_activity.pack(anchor='w')

# Dashboard Action Buttons
#btn_frame = tk.Frame(dashboard_frame)
#btn_frame.pack(pady=10)

#tk.Button(btn_frame, text="Add New Expense", width=18,bg="#2287e0").grid(row=0, column=0, padx=5, pady=5)
#tk.Button(btn_frame, text="View My Groups", width=18,bg="#67a1d3").grid(row=0, column=1, padx=5, pady=5)
#tk.Button(btn_frame, text="Monthly Summary", width=18,bg="#cfe2f3").grid(row=1, column=0, padx=5, pady=5)
#tk.Button(btn_frame, text="Settings", width=18,bg="#cfe2f3").grid(row=1, column=1, padx=5, pady=5)

btn_frame = ttk.Frame(dashboard_frame)
btn_frame.pack(pady=20)

button_labels = [
    ("➕ Add Expense", lambda: None),
    ("👥 View Groups", lambda: None),
    ("📊 Monthly Summary", lambda: None),
    ("⚙️ Settings", lambda: None),
    ("View Balances", update_balances_view),
    ("Logout", lambda: show_frame(login_frame))
]

for idx, (text,command) in enumerate(button_labels):
    ttk.Button(
        btn_frame,
        text=text,
        command=command,
        style="Custom.TButton",
        width=22
    ).grid(row=idx // 2, column=idx % 2, padx=12, pady=12)


# Recent Activity Feed
tk.Label(dashboard_frame, text="Recent Activity", font=("Arial", 14)).pack(pady=10)

activity_text = tk.Text(dashboard_frame, height=5, width=45)
activity_text.pack()
activity_text.insert(tk.END, "• You added: $440 - Rent \n")
activity_text.insert(tk.END, "• Rhiya paid: $20 - Toilet Paper\n")
activity_text.insert(tk.END, "• You owe: $15 to Ayush for Dinner\n")
# Expense Split Section
split_section = tk.LabelFrame(dashboard_frame, text="Choose Split Method", padx=10, pady=10)
split_section.pack(pady=15)

split_type = tk.StringVar(value="Equal")

tk.Label(split_section, text="Split Type:").pack()

dropdown = tk.OptionMenu(split_section, split_type, "Equal", "Custom")
dropdown.pack()

# Frame for custom input fields (initially hidden)
custom_frame = tk.Frame(split_section)

def on_split_change(*args):
    if split_type.get() == "Custom":
        custom_frame.pack(pady=5)
    else:
        custom_frame.forget()

split_type.trace("w", on_split_change)

tk.Label(custom_frame, text="User 1 Amount ($):").pack()
tk.Entry(custom_frame).pack()

tk.Label(custom_frame, text="User 2 Amount ($):").pack()
tk.Entry(custom_frame).pack()

#Logout Button
tk.Button(dashboard_frame, text="Log Out", command=lambda: show_frame(login_frame),bg="#4f7faa").pack(pady=10)



#for frame in (register_frame, login_frame, dashboard_frame):
    #frame.grid(row=0, column=0, sticky='nsew')

    #View Balance frame
tk.Label(view_balances_frame, text="Your Balances", font=("Arial", 16)).pack(pady=10)
balances_list = tk.Text(view_balances_frame, height=10, width=45)
balances_list.pack(pady=10)
tk.Button(view_balances_frame, text="Back to Dashboard", command=lambda: show_frame(dashboard_frame)).pack(pady=10)

# Register Frame UI
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

tk.Button(register_frame, text="Register", command=register_user,bg="#d9ead3").pack(pady=10)
tk.Button(register_frame, text="Already registered? Login", command=lambda: show_frame(login_frame)).pack()

#  Login Frame UI
#  Login Frame UI (cleaned and styled)
tk.Label(login_frame, text="Login", font=("Arial", 20, "bold"), bg="#49A475", fg="white").pack(pady=(30, 15))

tk.Label(login_frame, text="Email", bg="#49A475", fg="white", font=("Arial", 12)).pack(pady=(5, 2))
entry_email_login = ttk.Entry(login_frame, width=30, style="RoundedEntry.TEntry")
entry_email_login.pack(pady=5)
#entry_email_login = tk.Entry(login_frame, width=30, font=("Arial", 12), bg="white", fg="black", relief=tk.FLAT)
#entry_email_login.pack(pady=(0, 10))

tk.Label(login_frame, text="Password", bg="#49A475", fg="white", font=("Arial", 12)).pack(pady=(5, 2))
entry_pass_login = ttk.Entry(login_frame, width=30, style="RoundedEntry.TEntry", show="*")
entry_pass_login.pack(pady=5)
#entry_pass_login = tk.Entry(login_frame, show="*", width=30, font=("Arial", 12), bg="white", fg="black", relief=tk.FLAT)
#entry_pass_login.pack(pady=(0, 15))

tk.Button(login_frame, text="Login", command=login_user, bg="white", fg="#081abd", font=("Arial", 12, "bold"), relief=tk.GROOVE, width=15).pack(pady=10)

# Account navigation
tk.Label(login_frame, text="Don't have an account?", bg="#49A475", fg="white", font=("Arial", 10)).pack(pady=(20, 5))
register_link = tk.Label(login_frame, text="Register Here", fg="yellow", bg="#49A475", cursor="hand2", font=('Arial', 10, 'underline'))
register_link.pack()
register_link.bind("<Button-1>", lambda e: show_frame(register_frame))

for frame in (register_frame, login_frame, dashboard_frame, view_balances_frame):
    frame.grid(row=0, column=0, sticky='nsew')

logged_in_email = None

# Start on register page for first use
#show_frame(register_frame)
show_frame(login_frame)
root.mainloop()
