import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3
import os
import hashlib
import csv

# === Setup SQLite DB ===
if os.path.exists("users.db"):
    os.remove("users.db")

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        active INTEGER DEFAULT 1,
        notifications_enabled INTEGER DEFAULT 1
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        activity TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        date DATE DEFAULT CURRENT_DATE
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT NOT NULL,
        owner_email TEXT NOT NULL
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS group_members (
        group_id INTEGER,
        member_email TEXT,
        FOREIGN KEY(group_id) REFERENCES groups(id)
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS expense_splits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_id INTEGER,
        member_email TEXT,
        amount REAL,
        FOREIGN KEY(expense_id) REFERENCES expenses(id)
    )
""")
conn.commit()

root = tk.Tk()
root.title("Expense & Group Manager")
root.geometry("400x850")
root.configure(bg="#f0f0f0")

style = ttk.Style()
style.theme_use("clam")
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

logged_in_email = None

# === Frames ===
login_frame = tk.Frame(root, bg="#87d188")
register_frame = tk.Frame(root, bg="#ffccbc")
dashboard_frame = tk.Frame(root, bg="#a5d6a7")
expense_frame = tk.Frame(root, bg="#fff3e0")
group_frame = tk.Frame(root, bg="#ede7f6")
settings_frame = tk.Frame(root, bg="#d7ccc8")

history_frame = tk.Frame(root, bg="#ffe0b2")


for frame in (login_frame,register_frame, dashboard_frame, expense_frame, group_frame, settings_frame, history_frame):
    frame.grid(row=0, column=0, sticky='nsew')

def show_frame(frame):
    frame.tkraise()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Remember Me setup ---
remember_var = tk.IntVar(value=0)

def save_remember_email(email):
    with open("remember_me.txt", "w") as f:
        f.write(email)

def clear_remember_email():
    if os.path.exists("remember_me.txt"):
        os.remove("remember_me.txt")

def get_remember_email():
    if os.path.exists("remember_me.txt"):
        with open("remember_me.txt", "r") as f:
            return f.read().strip()
    return ""

# Login and Registration
def login_user():
    global logged_in_email
    email = login_email.get().strip().lower()
    password = hash_password(login_password.get().strip())
    cursor.execute("SELECT * FROM users WHERE email=? AND password=? AND active=1", (email, password))
    user = cursor.fetchone()
    if user:
        logged_in_email = email
        if remember_var.get():
            save_remember_email(email)
        else:
            clear_remember_email()
        dashboard_greeting.config(text=f"Welcome, {user[1]} {user[2]} 👋")
        update_activity_feed()
        update_groups_in_expense_combo()
        view_groups()
        show_frame(dashboard_frame)
    else:
        messagebox.showerror("Login Failed", "Invalid email/password or account deactivated.")

def register_user():
    fname = reg_fname.get().strip()
    lname = reg_lname.get().strip()
    email = reg_email.get().strip().lower()
    password = hash_password(reg_password.get().strip())
    if not fname or not lname or not email or not password:
        messagebox.showerror("Error", "Please fill all fields.")
        return
    try:
        cursor.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
                       (fname, lname, email, password))
        conn.commit()
        messagebox.showinfo("Success", "Registered successfully!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Email already exists.")

def update_activity_feed():
    activity_text.delete(1.0, tk.END)
    cursor.execute("SELECT activity, timestamp FROM activities WHERE user_email=? ORDER BY timestamp DESC LIMIT 10", (logged_in_email,))
    rows = cursor.fetchall()
    for activity, timestamp in rows:
        activity_text.insert(tk.END, f"• {activity} ({timestamp})\n")

def export_expenses():
    groups = expense_group_combo['values']
    filter_group = None
    if groups:
        res = messagebox.askyesno("Export Expenses", "Export expenses for selected group only?")
        if res:
            filter_group = expense_group_combo.get()

    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return

    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["User Email", "Amount", "Description", "Date", "Group"])
        if filter_group:
            cursor.execute("SELECT id FROM groups WHERE group_name=? AND owner_email=?", (filter_group, logged_in_email))
            gid = cursor.fetchone()
            if not gid:
                messagebox.showerror("Error", "Group not found.")
                return
            gid = gid[0]
            cursor.execute("SELECT member_email FROM group_members WHERE group_id=?", (gid,))
            members = [row[0] for row in cursor.fetchall()]
            if not members:
                messagebox.showinfo("Export", "No members in this group.")
                return
            query = f"""
                SELECT user_email, amount, description, date FROM expenses
                WHERE user_email IN ({','.join('?'*len(members))})
            """
            cursor.execute(query, members)
        else:
            cursor.execute("SELECT user_email, amount, description, date FROM expenses WHERE user_email=?", (logged_in_email,))
        rows = cursor.fetchall()
        for row in rows:
            writer.writerow([row[0], row[1], row[2] if row[2] else "", row[3], filter_group if filter_group else "All"])
    messagebox.showinfo("Export", f"Expenses exported successfully to:\n{file_path}")

def view_monthly_summary():
    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount)
        FROM expenses
        WHERE user_email=?
        GROUP BY month
        ORDER BY month
    """, (logged_in_email,))
    data = cursor.fetchall()
    if data:
        summary_lines = [f"{month}: ${total:.2f}" for month, total in data]
        summary_text = "\n".join(summary_lines)
        messagebox.showinfo("Monthly Expenses Summary", summary_text)
    else:
        messagebox.showinfo("Summary", "No expenses to show.")

def show_expense_history():
    history_text.delete(1.0, tk.END)
    cursor.execute("""
        SELECT e.date, e.amount, e.description, g.group_name
        FROM expenses e
        LEFT JOIN groups g ON g.owner_email = e.user_email
        WHERE e.user_email=?
        ORDER BY e.date DESC
    """, (logged_in_email,))
    rows = cursor.fetchall()
    if not rows:
        history_text.insert(tk.END, "No expenses to show.\n")
        return

    for date, amount, desc, group in rows:
        history_text.insert(tk.END, f"{date} | ${amount:.2f} | {desc or 'No description'} | Group: {group or 'N/A'}\n")

    show_frame(history_frame)


def add_group():
    name = group_name_entry.get().strip()
    if name:
        cursor.execute("INSERT INTO groups (group_name, owner_email) VALUES (?, ?)", (name, logged_in_email))
        group_id = cursor.lastrowid
        cursor.execute("INSERT INTO group_members (group_id, member_email) VALUES (?, ?)", (group_id, logged_in_email))
        conn.commit()
        messagebox.showinfo("Success", "Group created and you have been added.")
        group_name_entry.delete(0, tk.END)
        view_groups()
        update_groups_in_expense_combo()
    else:
        messagebox.showerror("Error", "Please enter a group name.")

def add_member_to_group():
    try:
        selection = group_list.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a group from the list.")
            return
        group = group_list.get(selection[0])
        new_member = member_email_entry.get().strip().lower()
        if not new_member:
            messagebox.showerror("Error", "Enter member email to add.")
            return
        cursor.execute("SELECT id FROM groups WHERE group_name=? AND owner_email=?", (group, logged_in_email))
        gid = cursor.fetchone()
        if gid:
            cursor.execute("SELECT * FROM group_members WHERE group_id=? AND member_email=?", (gid[0], new_member))
            if cursor.fetchone():
                messagebox.showinfo("Info", f"{new_member} is already a member of {group}.")
                return
            cursor.execute("INSERT INTO group_members (group_id, member_email) VALUES (?, ?)", (gid[0], new_member))
            conn.commit()
            messagebox.showinfo("Success", f"{new_member} added to {group}.")
            member_email_entry.delete(0, tk.END)
            update_groups_in_expense_combo()
        else:
            messagebox.showerror("Error", "Group not found or you are not the owner.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def view_groups():
    group_list.delete(0, tk.END)
    cursor.execute("""
        SELECT g.group_name FROM groups g
        JOIN group_members m ON g.id = m.group_id
        WHERE m.member_email=?
    """, (logged_in_email,))
    for row in cursor.fetchall():
        group_list.insert(tk.END, row[0])
    show_frame(group_frame)

def open_settings():
    load_notification_setting()
    show_frame(settings_frame)

def change_password():
    current = hash_password(current_password_entry.get())
    new = hash_password(new_password_entry.get())
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (logged_in_email, current))
    if cursor.fetchone():
        if not new_password_entry.get():
            messagebox.showerror("Error", "New password cannot be empty.")
            return
        cursor.execute("UPDATE users SET password=? WHERE email=?", (new, logged_in_email))
        conn.commit()
        messagebox.showinfo("Success", "Password updated.")
        current_password_entry.delete(0, tk.END)
        new_password_entry.delete(0, tk.END)
    else:
        messagebox.showerror("Error", "Current password is incorrect.")

def view_group_members():
    selection = group_list.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a group from the list.")
        return
    group_name = group_list.get(selection[0])
    
    cursor.execute("SELECT id FROM groups WHERE group_name=? AND owner_email=?", (group_name, logged_in_email))
    gid_res = cursor.fetchone()
    if not gid_res:
        messagebox.showerror("Error", "Group not found or you are not the owner.")
        return
    gid = gid_res[0]
    
    cursor.execute("SELECT member_email FROM group_members WHERE group_id=?", (gid,))
    members = [row[0] for row in cursor.fetchall()]
    if not members:
        messagebox.showinfo("Group Members", "No members in this group.")
        return
    
    lines = []
    for member in members:
        cursor.execute("SELECT IFNULL(SUM(amount),0) FROM expenses WHERE user_email=?", (member,))
        total_paid = cursor.fetchone()[0]

        cursor.execute("""
            SELECT IFNULL(SUM(amount),0) FROM expense_splits
            WHERE member_email=? AND expense_id IN (
                SELECT id FROM expenses WHERE user_email IN (
                    SELECT member_email FROM group_members WHERE group_id=?
                )
            )
        """, (member, gid))
        total_owed = cursor.fetchone()[0]

        net_balance = total_paid - total_owed
        lines.append(f"{member}\n  Paid: ${total_paid:.2f}\n  Owes: ${total_owed:.2f}\n  Net: ${net_balance:.2f}\n")

    info_text = f"Group '{group_name}' financials:\n\n" + "\n".join(lines)
    messagebox.showinfo(f"Group Members & Balances - {group_name}", info_text)

# --- Expense Split UI additions ---
split_type_var = tk.StringVar(value="equal")  # default split type

custom_split_frame = tk.Frame(expense_frame)
custom_entries = {}

def load_group_members_for_split():
    global custom_entries
    custom_entries.clear()
    for widget in custom_split_frame.winfo_children():
        widget.destroy()
    selected_group = expense_group_combo.get()
    if not selected_group:
        return
    cursor.execute("SELECT id FROM groups WHERE group_name=? AND owner_email=?", (selected_group, logged_in_email))
    gid = cursor.fetchone()
    if not gid:
        return
    cursor.execute("SELECT member_email FROM group_members WHERE group_id=?", (gid[0],))
    members = cursor.fetchall()
    for (member_email,) in members:
        lbl = tk.Label(custom_split_frame, text=member_email)
        lbl.pack(side="left", padx=5)
        ent = tk.Entry(custom_split_frame, width=8)
        ent.pack(side="left", padx=5)
        custom_entries[member_email] = ent

def toggle_custom_split():
    if split_type_var.get() == "custom":
        load_group_members_for_split()
        custom_split_frame.pack(pady=5, fill="x")
    else:
        for widget in custom_split_frame.winfo_children():
            widget.destroy()
        custom_split_frame.pack_forget()

def update_groups_in_expense_combo():
    cursor.execute("""
        SELECT g.group_name FROM groups g
        JOIN group_members m ON g.id = m.group_id
        WHERE m.member_email=?
    """, (logged_in_email,))
    groups = [row[0] for row in cursor.fetchall()]
    expense_group_combo['values'] = groups
    if groups:
        expense_group_combo.current(0)
        toggle_custom_split()
    else:
        expense_group_combo.set("")
        toggle_custom_split()

def add_expense():
    try:
        amount = float(expense_amount.get())
        desc = expense_desc.get()
        group_name = expense_group_combo.get()
        if not group_name:
            messagebox.showerror("Error", "Please select a group.")
            return

        cursor.execute("INSERT INTO expenses (user_email, amount, description) VALUES (?, ?, ?)",
                       (logged_in_email, amount, desc))
        expense_id = cursor.lastrowid

        cursor.execute("SELECT id FROM groups WHERE group_name=? AND owner_email=?", (group_name, logged_in_email))
        gid = cursor.fetchone()
        if not gid:
            messagebox.showerror("Error", "Group not found or you are not the owner.")
            return
        gid = gid[0]

        cursor.execute("SELECT member_email FROM group_members WHERE group_id=?", (gid,))
        members = [row[0] for row in cursor.fetchall()]
        if not members:
            messagebox.showerror("Error", "No members in selected group.")
            return

        split_type = split_type_var.get()

        if split_type == "equal":
            split_amount = round(amount / len(members), 2)
            total_assigned = split_amount * (len(members) - 1)
            last_amount = round(amount - total_assigned, 2)
            for i, member in enumerate(members):
                amt = split_amount if i < len(members) - 1 else last_amount
                cursor.execute("INSERT INTO expense_splits (expense_id, member_email, amount) VALUES (?, ?, ?)",
                               (expense_id, member, amt))

        elif split_type == "custom":
            total_entered = 0
            for member in members:
                ent = custom_entries.get(member)
                if not ent:
                    messagebox.showerror("Error", "Missing custom amounts.")
                    return
                try:
                    val = float(ent.get())
                except:
                    messagebox.showerror("Error", f"Invalid amount for {member}")
                    return
                total_entered += val

            if round(total_entered, 2) != round(amount, 2):
                messagebox.showerror("Error", f"Custom split amounts (${total_entered:.2f}) do not sum to total amount (${amount:.2f})")
                return

            for member in members:
                val = float(custom_entries[member].get())
                cursor.execute("INSERT INTO expense_splits (expense_id, member_email, amount) VALUES (?, ?, ?)",
                               (expense_id, member, val))
        else:
            messagebox.showerror("Error", "Invalid split type selected.")
            return

        cursor.execute("INSERT INTO activities (user_email, activity) VALUES (?, ?)",
                       (logged_in_email, f"Added expense: ${amount:.2f} - {desc} in group '{group_name}' split {split_type}"))
        conn.commit()

        messagebox.showinfo("Success", "Expense recorded with split.")
        expense_amount.delete(0, tk.END)
        expense_desc.delete(0, tk.END)
        toggle_custom_split()
        update_activity_feed()

    except ValueError:
        messagebox.showerror("Error", "Invalid amount")

# === Settings additions ===

notif_var = tk.IntVar()

def logout_user():
    global logged_in_email
    logged_in_email = None
    show_frame(login_frame)

def deactivate_account():
    if messagebox.askyesno("Confirm", "Deactivate your account? You won't be able to login until reactivated."):
        cursor.execute("UPDATE users SET active=0 WHERE email=?", (logged_in_email,))
        conn.commit()
        messagebox.showinfo("Account Deactivated", "Your account has been deactivated.")
        logout_user()

def delete_account():
    if messagebox.askyesno("Confirm", "Delete your account and all associated data? This cannot be undone."):
        cursor.execute("DELETE FROM expense_splits WHERE member_email=?", (logged_in_email,))
        cursor.execute("DELETE FROM expenses WHERE user_email=?", (logged_in_email,))
        cursor.execute("DELETE FROM group_members WHERE member_email=?", (logged_in_email,))
        cursor.execute("SELECT id FROM groups WHERE owner_email=?", (logged_in_email,))
        groups_owned = cursor.fetchall()
        for (gid,) in groups_owned:
            cursor.execute("DELETE FROM group_members WHERE group_id=?", (gid,))
        cursor.execute("DELETE FROM groups WHERE owner_email=?", (logged_in_email,))
        cursor.execute("DELETE FROM activities WHERE user_email=?", (logged_in_email,))
        cursor.execute("DELETE FROM users WHERE email=?", (logged_in_email,))
        conn.commit()
        messagebox.showinfo("Account Deleted", "Your account and all data have been deleted.")
        logout_user()

def toggle_notifications():
    val = 1 if notif_var.get() else 0
    cursor.execute("UPDATE users SET notifications_enabled=? WHERE email=?", (val, logged_in_email))
    conn.commit()
    messagebox.showinfo("Settings", f"Notifications {'enabled' if val else 'disabled'}.")

def load_notification_setting():
    cursor.execute("SELECT notifications_enabled FROM users WHERE email=?", (logged_in_email,))
    res = cursor.fetchone()
    if res:
        notif_var.set(res[0])



# === UI Code ===


# --- History Frame ---
history_text = tk.Text(history_frame, height=30, width=50)
history_text.pack(pady=10)
tk.Button(history_frame, text="Back to Dashboard", command=lambda: show_frame(dashboard_frame)).pack(pady=5)

# --- Login Frame ---
tk.Label(login_frame, text="Login", font=("Arial", 18)).pack(pady=10)

tk.Label(login_frame, text="Email").pack(pady=5)
login_email = tk.Entry(login_frame)
login_email.pack(pady=5)

tk.Label(login_frame, text="Password").pack(pady=5)
login_password = tk.Entry(login_frame, show="*")
login_password.pack(pady=5)

remember_checkbox = tk.Checkbutton(login_frame, text="Remember Me", variable=remember_var)
remember_checkbox.pack()

tk.Button(login_frame, text="Login", command=login_user).pack(pady=10)

tk.Label(login_frame, text="Don't have an account?").pack()
tk.Button(login_frame, text="Register Here", command=lambda: show_frame(register_frame)).pack()

# --- Registration Frame ---
tk.Label(register_frame, text="Register", font=("Arial", 18)).pack(pady=10)

tk.Label(register_frame, text="First Name").pack()
reg_fname = tk.Entry(register_frame)
reg_fname.pack()

tk.Label(register_frame, text="Last Name").pack()
reg_lname = tk.Entry(register_frame)
reg_lname.pack()

tk.Label(register_frame, text="Email").pack()
reg_email = tk.Entry(register_frame)
reg_email.pack()

tk.Label(register_frame, text="Password").pack()
reg_password = tk.Entry(register_frame, show="*")
reg_password.pack()

tk.Label(register_frame, text="Confirm Password").pack()
reg_confirm = tk.Entry(register_frame, show="*")
reg_confirm.pack()

tk.Button(register_frame, text="Register", command=register_user).pack(pady=10)
tk.Button(register_frame, text="Back to Login", command=lambda: show_frame(login_frame)).pack()

# --- Dashboard Frame ---
dashboard_greeting = tk.Label(dashboard_frame, text="Welcome!", font=("Arial", 16))
dashboard_greeting.pack(pady=10)

activity_text = tk.Text(dashboard_frame, height=10, width=45)
activity_text.pack(pady=5)

tk.Button(dashboard_frame, text="Manage Groups (Create/Add Members)", command=view_groups).pack(pady=5)
tk.Button(dashboard_frame, text="Add Expense", command=lambda: [update_groups_in_expense_combo(), show_frame(expense_frame)]).pack(pady=5)
tk.Button(dashboard_frame, text="Export My Expenses (CSV)", command=export_expenses).pack(pady=5)
tk.Button(dashboard_frame, text="View Monthly Expense Summary", command=view_monthly_summary).pack(pady=5)
tk.Button(dashboard_frame, text="Settings", command=open_settings).pack(pady=5)
tk.Button(dashboard_frame, text="Logout", command=logout_user).pack(pady=5)

# --- Expense Frame ---
tk.Label(expense_frame, text="Add Expense", font=("Arial", 16)).pack(pady=10)
tk.Label(expense_frame, text="Amount").pack()
expense_amount = tk.Entry(expense_frame)
expense_amount.pack(pady=5)
tk.Label(expense_frame, text="Description").pack()
expense_desc = tk.Entry(expense_frame)
expense_desc.pack(pady=5)

tk.Label(expense_frame, text="Select Group").pack(pady=5)
expense_group_combo = ttk.Combobox(expense_frame, state="readonly")
expense_group_combo.pack(pady=5)

tk.Label(expense_frame, text="Split Type").pack(pady=5)
split_equal_rb = tk.Radiobutton(expense_frame, text="Equal Split", variable=split_type_var, value="equal", command=toggle_custom_split)
split_equal_rb.pack()
split_custom_rb = tk.Radiobutton(expense_frame, text="Custom Split", variable=split_type_var, value="custom", command=toggle_custom_split)
split_custom_rb.pack()

custom_split_frame.pack_forget()

tk.Button(expense_frame, text="Add Expense with Split", command=add_expense).pack(pady=10)
tk.Button(expense_frame, text="Back to Dashboard", command=lambda: show_frame(dashboard_frame)).pack(pady=5)

# --- Group Frame ---
tk.Label(group_frame, text="Create New Group", font=("Arial", 16)).pack(pady=10)
group_name_entry = tk.Entry(group_frame)
group_name_entry.pack(pady=5)
tk.Button(group_frame, text="Add Group", command=add_group).pack(pady=5)

tk.Label(group_frame, text="Your Groups", font=("Arial", 14)).pack(pady=10)
group_list = tk.Listbox(group_frame, height=8)
group_list.pack(pady=5, fill="x")

tk.Label(group_frame, text="Add Member Email").pack(pady=5)
member_email_entry = tk.Entry(group_frame)
member_email_entry.pack(pady=5)
tk.Button(group_frame, text="Add Member to Selected Group", command=add_member_to_group).pack(pady=5)

tk.Button(group_frame, text="View Group Members & Balances", command=view_group_members).pack(pady=10)
tk.Button(group_frame, text="Back to Dashboard", command=lambda: show_frame(dashboard_frame)).pack(pady=5)

# --- Settings Frame ---
tk.Label(settings_frame, text="Change Password", font=("Arial", 14)).pack(pady=10)
tk.Label(settings_frame, text="Current Password").pack()
current_password_entry = tk.Entry(settings_frame, show="*")
current_password_entry.pack(pady=5)
tk.Label(settings_frame, text="New Password").pack()
new_password_entry = tk.Entry(settings_frame, show="*")
new_password_entry.pack(pady=5)
tk.Button(settings_frame, text="Update Password", command=change_password).pack(pady=10)

tk.Checkbutton(settings_frame, text="Enable Notifications", variable=notif_var, command=toggle_notifications).pack(pady=5)

tk.Button(settings_frame, text="Logout", command=logout_user).pack(pady=5)
tk.Button(settings_frame, text="Deactivate Account", command=deactivate_account).pack(pady=5)
tk.Button(settings_frame, text="Delete Account", command=delete_account).pack(pady=5)
tk.Button(settings_frame, text="Back to Dashboard", command=lambda: [load_notification_setting(), show_frame(dashboard_frame)]).pack(pady=5)
tk.Button(dashboard_frame, text="View Expense History", command=show_expense_history).pack(pady=5)


#Auto-Fill Login Email if Remember Me was Used
saved_email = get_remember_email()
if saved_email:
    login_email.insert(0, saved_email)
    remember_var.set(1)

show_frame(login_frame)
root.mainloop()



