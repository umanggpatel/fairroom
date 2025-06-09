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
root.configure(bg="#f0f0f0")

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
        dashboard_greeting.config(text=f"Welcome, {full_name} 👋")
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

# Frames
register_frame = tk.Frame(root,bg="#f0f0f0")
login_frame = tk.Frame(root,bg="#f0f0f0")
dashboard_frame = tk.Frame(root,bg="#f0f0f0")


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
btn_frame = tk.Frame(dashboard_frame)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Add New Expense", width=18,bg="#cfe2f3").grid(row=0, column=0, padx=5, pady=5)
tk.Button(btn_frame, text="View My Groups", width=18,bg="#cfe2f3").grid(row=0, column=1, padx=5, pady=5)
tk.Button(btn_frame, text="Monthly Summary", width=18,bg="#cfe2f3").grid(row=1, column=0, padx=5, pady=5)
tk.Button(btn_frame, text="Settings", width=18,bg="#cfe2f3").grid(row=1, column=1, padx=5, pady=5)

# Recent Activity Feed
tk.Label(dashboard_frame, text="Recent Activity", font=("Arial", 14)).pack(pady=10)

activity_text = tk.Text(dashboard_frame, height=5, width=45)
activity_text.pack()
activity_text.insert(tk.END, "• You added: $440 - Rent \n")
activity_text.insert(tk.END, "• Rhiya paid: $20 - Toilet Paper\n")
activity_text.insert(tk.END, "• You owe: $15 to Ayush for Dinner\n")

#Logout Button
tk.Button(dashboard_frame, text="Log Out", command=lambda: show_frame(login_frame),bg="#f4cccc").pack(pady=10)



for frame in (register_frame, login_frame, dashboard_frame):
    frame.grid(row=0, column=0, sticky='nsew')

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
tk.Label(login_frame, text="Login", font=("Arial", 18)).pack(pady=10)

tk.Label(login_frame, text="Email").pack()
entry_email_login = tk.Entry(login_frame, width=30)
entry_email_login.pack()

tk.Label(login_frame, text="Password",bg="#f0f0f0").pack()
entry_pass_login = tk.Entry(login_frame, show="*", width=30)
entry_pass_login.pack()

tk.Button(login_frame, text="Login", command=login_user,bg="#d9ead3").pack(pady=10)

text = tk.Label(login_frame, text="Don't have an account?")

register_link = tk.Label(login_frame, text=" Register Here", fg="green", cursor="hand2", font=('Arial', 10, 'underline'))
text.pack()
register_link.pack()


register_link.bind("<Button-1>", lambda e: show_frame(register_frame))

# Start on register page for first use
#show_frame(register_frame)
show_frame(login_frame)
root.mainloop()
