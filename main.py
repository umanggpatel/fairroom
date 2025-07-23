import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3
import os
import hashlib
import csv
from datetime import datetime, timedelta
from monthly_summary_page import show_monthly_summary
from tkcalendar import DateEntry
import re
from features_plus import settle_up









current_group_id = None  # Stores selected group for settle_up
# === Setup SQLite DB ===
if not os.path.exists("users.db"):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
else:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()


cursor.execute("DROP TABLE IF EXISTS balances")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user TEXT NOT NULL,
        to_user TEXT NOT NULL,
        amount REAL NOT NULL,
        group_id INTEGER
    )
""")
conn.commit()


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
        timestamp DATETIME 
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


cursor.execute("""
    CREATE TABLE IF NOT EXISTS balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user TEXT NOT NULL,    
        to_user TEXT NOT NULL,      
        amount REAL NOT NULL,
        group_id INTEGER
    );
""")



try:
    cursor.execute("ALTER TABLE expenses ADD COLUMN category TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass

conn.commit()


root = tk.Tk()
root.title("Expense & Group Manager")
root.geometry("400x850")
root.configure(bg="#eaf6f9")


style = ttk.Style()
style.theme_use("clam")
style.configure("Custom.TButton",
    background="#00796b",
    foreground="white",
    font=("Arial", 11, "bold"),
    padding=10
)
style.map("Custom.TButton",
    background=[("active", "#00695c")],
    foreground=[("active", "white")]
)
style.configure("RoundedEntry.TEntry", relief="flat", padding=6, borderwidth=1, font=("Arial", 12))

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

#Global Variables
logged_in_email = None
history_backup = ""


# === Frames ===
login_frame = tk.Frame(root, bg="#6babc3")
register_frame = tk.Frame(root, bg="#6babc3")
dashboard_frame = tk.Frame(root, bg="#6babc3")
expense_frame = tk.Frame(root, bg="#6babc3")
monthly_summary_frame = tk.Frame(root, bg="white")
monthly_summary_frame.place(x=0, y=0, relwidth=1, relheight=1)

group_frame = tk.Frame(root, bg="#6babc3")
settings_frame = tk.Frame(root, bg="#6babc3")

history_frame = tk.Frame(root, bg="#6babc3")


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



def valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def strong_password(password):
    if len(password)<8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password): 
        return False
    if not re.search(r"\d", password):
        return False
    return True
    
    

# Validation, Login and Registration
def login_user():
    global logged_in_email
    email = login_email.get().strip().lower()
    password = hash_password(login_password.get().strip())
    if not valid_email(email):
        messagebox.showerror("Invalid Email", "Please enter a valid email address (e.g., youremail@gmail.com).")
        return
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
    password = reg_password.get().strip()
    confirm = reg_confirm.get().strip()

    if not fname or not lname or not email or not password or not confirm:
        messagebox.showerror("Error", "Please fill in all fields.")
        return
    if not fname.isalpha() or not lname.isalpha():
        messagebox.showerror("Invalid Name", "First Name and Last Name must contain only letters (no numbers or symbols).")
        return
    
    if not valid_email(email):
        messagebox.showerror("Invalid Email", "Please enter a valid email address (e.g., youremail@gmail.com).")
        return

    if password != confirm:
        messagebox.showerror("Error", "Passwords do not match.")
        return
    if not strong_password(password):
        messagebox.showerror(
        "Weak Password",
    "Password must be at least 8 characters long and include:\n• At least one uppercase letter\n• At least one lowercase letter\n• At least one number or special character")
        return 

    hashed_password = hash_password(password)

    try:
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
            (fname, lname, email, hashed_password)
        )
        conn.commit()
        messagebox.showinfo("Success", "Registration successful! You can now log in.")
        show_frame(login_frame)
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "An account with this email already exists.")


#def update_activity_feed():
   # activity_text.delete(1.0, tk.END)
    #cursor.execute("SELECT activity, timestamp FROM activities WHERE user_email=? ORDER BY timestamp DESC LIMIT 10", (logged_in_email,))
    #rows = cursor.fetchall()
    #for activity, timestamp in rows:
       # activity_text.insert(tk.END, f"• {activity} ({timestamp})\n")
def get_relative_time(past, now=None):
    now = now or datetime.now()
    diff = now - past

    seconds = diff.total_seconds()
    minutes = seconds // 60
    hours = minutes // 60
    days = diff.days

    if seconds < 60:
        return "just now"
    elif minutes < 60:
        return f"{int(minutes)} min ago"
    elif hours < 24:
        return f"{int(hours)} hr ago"
    elif days == 1:
        return "Yesterday"
    elif days < 7:
        return past.strftime("%A")  # e.g., "Monday"
    else:
        return past.strftime("%b %d")  # e.g., "Jul 05"


def update_activity_feed():
    activity_text.config(state="normal")
    activity_text.delete(1.0, tk.END)

    cursor.execute("""
        SELECT activity, timestamp FROM activities
        WHERE user_email=?
        ORDER BY timestamp DESC
        LIMIT 100
    """, (logged_in_email,))
    rows = cursor.fetchall()

    if not rows:
        activity_text.insert("end", "No recent activity yet...\n", "default")
    else:
        now = datetime.now()

        for activity, ts in rows:
            ts_dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            relative_time = get_relative_time(ts_dt, now)
            date_str = ts_dt.strftime("%Y-%m-%d")

            # Insert date (left) and relative time
            activity_text.insert("end", f"📅 {date_str}   🕒 {relative_time}\n", "timestamp")

            # Styled activity content
            if "Added expense" in activity:
                activity_text.insert("end", activity + "\n\n", "expense")
            elif "Created group" in activity:
                activity_text.insert("end", activity + "\n\n", "group")
            elif "Added member" in activity:
                activity_text.insert("end", activity + "\n\n", "member")
            else:
                activity_text.insert("end", activity + "\n\n", "default")

    activity_text.config(state="disabled")





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



def show_expense_history():
    #history_text.delete(1.0, tk.END)
    history_text.config(state="normal")
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
    for idx, (date, amount, desc, group) in enumerate(rows, 1):
        history_text.insert("end", f"🔹 Entry #{idx}\n", "entry")
        history_text.insert("end", f"📅 Date: {date}\n", "label")
        history_text.insert("end", f"💰 Amount: ${amount:.2f}\n", "amount")
        history_text.insert("end", f"📝 Description: {desc or 'No description'}\n", "label")
        history_text.insert("end", f"👥 Group: {group or 'N/A'}\n", "label")
        history_text.insert("end", "-"*40 + "\n", "divider")
        history_text.tag_configure("entry", font=("Arial", 11, "bold"), foreground="#1a237e")
        history_text.tag_configure("label", font=("Arial", 10), foreground="#333")
        history_text.tag_configure("amount", font=("Arial", 10, "bold"), foreground="#2e7d32")
        history_text.tag_configure("divider", foreground="#ccc")

    #for date, amount, desc, group in rows:
        #history_text.insert(tk.END, f"{date} | ${amount:.2f} | {desc or 'No description'} | Group: {group or 'N/A'}\n")

    show_frame(history_frame)


def add_group():
    name = group_name_entry.get().strip()
    if name:
        cursor.execute("INSERT INTO groups (group_name, owner_email) VALUES (?, ?)", (name, logged_in_email))
        group_id = cursor.lastrowid
        cursor.execute("INSERT INTO group_members (group_id, member_email) VALUES (?, ?)", (group_id, logged_in_email))

        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO activities (user_email, activity, timestamp)
            VALUES (?, ?, ?)
        """, (logged_in_email, f"Created group '{name}'", timestamp))

        
  

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

            # INSERT ACTIVITY LOG
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO activities (user_email, activity, timestamp)
                VALUES (?, ?, ?)
            """, (logged_in_email, f"Added member '{new_member}' to group '{group}'", timestamp))
            conn.commit()

            messagebox.showinfo("Success", f"{new_member} added to {group}.")
            member_email_entry.delete(0, tk.END)
            update_groups_in_expense_combo()

            #  REFRESH ACTIVITY FEED
            update_activity_feed()
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

# Function to update the recent activity feed
def log_activity(msg):
    activity_text.config(state="normal")
    activity_text.insert("end", f"• {msg}\n")
    activity_text.see("end")  
    activity_text.config(state="disabled")

#shwo password
show_password_var = tk.IntVar()
def toggle_password_visibility():
    if show_password_var.get():
        login_password.config(show="")
    else:
        if login_password.get() != "Password":
            login_password.config(show="*")
        else:
            login_password.config(show="")


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

 #group members view       
def view_selected_group_members_popup():
    selection = group_list.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a group.")
        return

    group_name = group_list.get(selection[0])

    cursor.execute("SELECT id FROM groups WHERE group_name=?", (group_name,))
    result = cursor.fetchone()
    if not result:
        messagebox.showerror("Error", "Group not found.")
        return

    gid = result[0]
    cursor.execute("SELECT member_email FROM group_members WHERE group_id=?", (gid,))
    members = [row[0] for row in cursor.fetchall()]

    # Create popup window
    popup = tk.Toplevel(root)
    popup.title(f"{group_name} - Members")
    popup.geometry("400x400")
    popup.configure(bg="#eaf6f9")
    popup.resizable(False, False)

    tk.Label(popup, text=f"Members of '{group_name}'", font=("Arial", 14, "bold"),
             bg="#eaf6f9", fg="#0d3c61").pack(pady=(15, 5))

    member_list_frame = tk.Frame(popup, bg="#fefae0", bd=2, relief="ridge")
    member_list_frame.pack(pady=10, padx=20, fill="both", expand=True)

    selected_member = tk.StringVar()

    if members:
        for email in members:
            tk.Radiobutton(member_list_frame, text=email, variable=selected_member, value=email,
                           bg="#fefae0", fg="#333", anchor="w", font=("Arial", 11), highlightthickness=0).pack(
                fill="x", padx=10, pady=2)
    else:
        tk.Label(member_list_frame, text="No members found.", font=("Arial", 11, "italic"),
                 bg="#fefae0", fg="#777").pack(pady=10)

    # --- Remove Member Button ---
    def remove_selected_member():
        email = selected_member.get()
        if not email:
            messagebox.showwarning("Select Member", "Please select a member to remove.")
            return
        if email == logged_in_email:
            messagebox.showwarning("Invalid", "You cannot remove yourself from the group.")
            return

        confirm = messagebox.askyesno("Confirm", f"Remove {email} from {group_name}?")
        if confirm:
            cursor.execute("DELETE FROM group_members WHERE group_id=? AND member_email=?", (gid, email))
            conn.commit()
            messagebox.showinfo("Removed", f"{email} removed from the group.")
            popup.destroy()
            view_selected_group_members_popup()  # Refresh the popup

    # --- Export Members to CSV ---
    def export_members():
        if not members:
            messagebox.showinfo("Export", "No members to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")],
                                                 title="Save member list as...")
        if file_path:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Member Email"])
                for email in members:
                    writer.writerow([email])
            messagebox.showinfo("Exported", f"Members exported to:\n{file_path}")

    # --- Button Frame ---
    action_frame = tk.Frame(popup, bg="#eaf6f9")
    action_frame.pack(pady=10)

    tk.Button(action_frame, text=" Remove Member", command=remove_selected_member,
              font=("Arial", 10), bg="#ffcdd2", fg="black").pack(side="left", padx=10)

    tk.Button(action_frame, text="📤 Export to CSV", command=export_members,
              font=("Arial", 10), bg="#bbdefb", fg="black").pack(side="left", padx=10)

    tk.Button(popup, text="Close", command=popup.destroy,
              font=("Arial", 10, "bold"), bg="#cfd8dc", fg="black").pack(pady=10)

def view_group_balances():
    selection = group_list.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a group from the list.")
        return

    group_name = group_list.get(selection[0])
    cursor.execute("SELECT id FROM groups WHERE group_name=?", (group_name,))
    result = cursor.fetchone()
    if not result:
        messagebox.showerror("Error", "Group not found.")
        return

    gid = result[0]
    show_group_balances(logged_in_email, gid)


    # Show clean 'who owes whom' instead of summary
    cursor.execute("""
        SELECT from_user, to_user, SUM(amount)
        FROM balances
        WHERE group_id = ?
        GROUP BY from_user, to_user
    """, (gid,))
    rows = cursor.fetchall()

    if not rows:
        message = "No balances found."
    else:
        message = ""
        for from_user, to_user, amt in rows:
            message += f"{from_user} owes {to_user}: ${amt:.2f}\n"

    messagebox.showinfo(f"Group '{group_name}' balances", message)



    

# --- Expense Split UI
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
    gid = get_group_id(selected_group)
    if not gid:
        return
    members = get_group_members(gid)
    for member_email in members:
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

expense_category_var = tk.StringVar(value="Select")

def get_group_id(group_name):
    cursor.execute("SELECT id FROM groups WHERE group_name=? AND owner_email=?", (group_name, logged_in_email))
    row = cursor.fetchone()
    return row[0] if row else None

def get_group_members(group_id):
    cursor.execute("SELECT member_email FROM group_members WHERE group_id=?", (group_id,))
    return [row[0] for row in cursor.fetchall()]

def insert_balance(payer, split_with, group_id, split_amounts):
    for member in split_with:
        if member == payer:
            continue
        amount = split_amounts[member]

        cursor.execute("""
            SELECT amount FROM balances
            WHERE from_user = ? AND to_user = ? AND group_id = ?
        """, (member, payer, group_id))
        row = cursor.fetchone()

        if row:
            new_amount = round(row[0] + amount, 2)
            cursor.execute("""
                UPDATE balances SET amount = ?
                WHERE from_user = ? AND to_user = ? AND group_id = ?
            """, (new_amount, member, payer, group_id))
        else:
            cursor.execute("""
                INSERT INTO balances (from_user, to_user, amount, group_id)
                VALUES (?, ?, ?, ?)
            """, (member, payer, amount, group_id))

    conn.commit()

def log_activity(user, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO activities (user_email, activity, timestamp)
        VALUES (?, ?, ?)
    """, (user, message, timestamp))

def record_split(expense_id, members, split_type, amount):
    split_amounts = {}

    if split_type == "equal":
        split_amount = round(amount / len(members), 2)
        for member in members:
            if member == logged_in_email:
                continue
            cursor.execute("INSERT INTO expense_splits (expense_id, member_email, amount) VALUES (?, ?, ?)",
                           (expense_id, member, split_amount))
            split_amounts[member] = split_amount

    elif split_type == "custom":
        total = 0
        for member in members:
            val = float(custom_entries[member].get())
            total += val
            cursor.execute("INSERT INTO expense_splits (expense_id, member_email, amount) VALUES (?, ?, ?)",
                           (expense_id, member, val))
            split_amounts[member] = val
        if round(total, 2) != round(amount, 2):
            raise ValueError("Custom split amounts do not sum to total")

    return split_amounts

def add_expense():
    try:
        amount = float(expense_amount.get())
        desc = expense_desc.get()
        category = expense_category_var.get()
        group_name = expense_group_combo.get()

        if not group_name:
            messagebox.showerror("Error", "Please select a group.")
            return

        gid = get_group_id(group_name)
        if not gid:
            messagebox.showerror("Error", "Group not found.")
            return

        members = get_group_members(gid)
        if not members:
            messagebox.showerror("Error", "No members in selected group.")
            return

        cursor.execute("INSERT INTO expenses (user_email, amount, description, category) VALUES (?, ?, ?, ?)",
                       (logged_in_email, amount, desc, category))
        expense_id = cursor.lastrowid

        split_type = split_type_var.get()
        split_amounts = record_split(expense_id, members, split_type, amount)

        insert_balance(logged_in_email, members, gid, split_amounts)

        log_activity(logged_in_email, f"Added expense: ${amount:.2f} - {desc} in group '{group_name}' split {split_type}")

        conn.commit()
        messagebox.showinfo("Success", "Expense recorded successfully.")

        expense_amount.delete(0, tk.END)
        expense_desc.delete(0, tk.END)
        toggle_custom_split()
        update_activity_feed()

    except ValueError as ve:
        messagebox.showerror("Error", str(ve))

def show_group_balances(logged_in_email, group_id):
    message = ""

    cursor.execute("""
        SELECT to_user, SUM(amount) FROM balances
        WHERE from_user = ? AND group_id = ?
        GROUP BY to_user
    """, (logged_in_email, group_id))
    owes_list = cursor.fetchall()

    cursor.execute("""
        SELECT from_user, SUM(amount) FROM balances
        WHERE to_user = ? AND group_id = ?
        GROUP BY from_user
    """, (logged_in_email, group_id))
    owed_list = cursor.fetchall()

    if not owes_list and not owed_list:
        message = "You have no balances in this group."
    else:
        if owes_list:
            message += "You owe:\n"
            for to_user, amt in owes_list:
                message += f"  {to_user}: ${amt:.2f}\n"

        if owed_list:
            message += "\nPeople who owe you:\n"
            for from_user, amt in owed_list:
                message += f"  {from_user}: ${amt:.2f}\n"

    messagebox.showinfo("Group Balances", message)

def show_frame(frame):
    frame.tkraise()

def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()


#for clearing history in the history frame
def clear_history_display():
    global history_backup
    history_text.config(state="normal")
    history_backup = history_text.get("1.0", "end")
    history_text.delete("1.0", "end")
    history_text.config(state="disabled")
    undo_button.pack(anchor="w", padx=10, pady=(5, 0))

def restore_history():
    global history_backup
    history_text.config(state="normal")
    history_text.delete("1.0", "end")
    history_text.insert("end", history_backup)
    history_text.config(state="disabled")
    undo_button.pack_forget()


def show_clear_balances(group_id):
    message = ""

    # Show who owes whom in this group
    cursor.execute("""
        SELECT from_user, to_user, SUM(amount) as total
        FROM balances
        WHERE group_id = ?
        GROUP BY from_user, to_user
    """, (group_id,))
    rows = cursor.fetchall()

    if not rows:
        message = "No balances found."
    else:
        for from_user, to_user, amt in rows:
            message += f"{from_user} owes {to_user}: ${amt:.2f}\n"

    messagebox.showinfo(f"Group '{group_id}' balances", message)

'''
#View Balance
/*def update_balances_view():
    global view_balances_frame, balances_list

    view_balances_frame = tk.Frame(root, bg="#f0f0f0")
    tk.Label(view_balances_frame, text="Your Balances", font=("Arial", 16)).pack(pady=10)
    balances_list = tk.Text(view_balances_frame, height=10, width=45)
    balances_list.pack(pady=10)
    tk.Button(view_balances_frame, text="Back to Dashboard", command=lambda: show_frame(dashboard_frame)).pack(pady=10)

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
    view_balances_frame.grid(row=0, column=0, sticky='nsew')

    show_frame(view_balances_frame)

'''

# Settings additions 

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
history_frame.pack_propagate(False)

# Top-left Back button
tk.Button(history_frame, text="⬅ Back to DB", font=("Arial", 10, "bold"),
          bg="#c8e6c9", command=lambda: show_frame(dashboard_frame)).pack(anchor="nw", padx=10, pady=(10, 5))

# Container for the history display
history_display_container = tk.Frame(history_frame, bg="#6babc3")
history_display_container.pack(fill="both", expand=True, padx=10, pady=5)

history_box_wrapper = tk.Frame(history_display_container, bg="#6babc3", bd=2, relief="groove")
history_box_wrapper.pack(pady=5)

history_text = tk.Text(history_box_wrapper, height=30, width=50, wrap="word",
bg="white", fg="black", font=("Arial", 10), relief="flat", bd=0)
history_text.pack()

history_text.bind("<Key>", lambda e: "break")         # Disable typing
history_text.bind("<Control-v>", lambda e: "break")   # Disable paste
history_text.bind("<Button-3>", lambda e: "break")    # Disable right-click paste



# Bottom buttons: Clear and Undo (in horizontal row)
history_button_row = tk.Frame(history_frame, bg="#6babc3")
history_button_row.pack(pady=10)

clear_btn = tk.Button(history_button_row, text="🧹 Clear Display", font=("Arial", 10),
                      bg="#ffe0b2", command=clear_history_display)
clear_btn.pack(side="left", padx=5)

undo_button = tk.Button(history_button_row, text="↩️ Undo Clear", font=("Arial", 10),
                        bg="#ffecb3", command=restore_history)
undo_button.pack(side="left", padx=5)
undo_button.pack_forget()  # Hidden until Clear is clicked

# --- Login Frame ---
#tk.Label(login_frame, text="Login", font=("Arial", 20)).pack(pady=10)

# bordered box for neat layout
login_box = tk.Frame(login_frame, bg="#fefae0", bd=2, relief="groove", padx=20, pady=20)
login_box.pack(pady=40)

emoji_label = tk.Label(login_box, text="👤", font=("Arial", 28), fg="#4caf50", bg="white")
emoji_label.pack(pady=(25, 0))

title_label = tk.Label(login_box, text=" Fairroom Login", font=("Arial", 28, "bold"), fg="#040303", bg="white")
title_label.pack(pady=(0, 10))

#tk.Label(login_frame, text="Email").pack(pady=5)
#login_email = tk.Entry(login_frame)
#login_email.pack(pady=5)

#with email placeholder text
tk.Label(login_box, text="📧Email", font=("Arial", 14), bg="#fefae0", fg="black", anchor="w").pack(fill="x", pady=(10, 0))

login_email = tk.Entry(login_box, fg='grey', bg="#f5f7f7", insertbackground='black')
#login_email.insert(0, "youremail@gmail.com")
login_email.pack(fill="x", pady=5, ipady=5, ipadx=5)

def on_entry_click_email(event):
    if login_email.get() == "youremail@gmail.com":
        login_email.delete(0, tk.END)
        login_email.config(fg='black')

def on_focusout_email(event):
    if login_email.get() == "":
        login_email.insert(0, "youremail@gmail.com")
        login_email.config(fg='grey')

login_email.bind("<FocusIn>", on_entry_click_email)
login_email.bind("<FocusOut>", on_focusout_email)

#tk.Label(login_frame, text="Password").pack(pady=5)
#login_password = tk.Entry(login_frame, show="*")
#login_password.pack(pady=5)



# Label
tk.Label(login_box, text="🔑Password", font=("Arial", 14), bg="#fefae0", fg="black", anchor="w").pack(fill="x", pady=(10, 0))

# Frame to hold Entry + Eye icon
password_container = tk.Frame(login_box, bg="#fefae0")
password_container.pack(fill="x", pady=5)

# Entry
login_password = tk.Entry(password_container, fg='grey', bg="#f5f7f7", insertbackground='black', relief="flat")
login_password.insert(0, "Password")
login_password.pack(side="left", fill="both", expand=True, ipady=5, ipadx=5)

# Eye icon
show_icon = tk.Label(password_container, text="👁", bg="#f5f7f7", fg="black", cursor="hand2")
show_icon.pack(side="right", padx=5)

def toggle_password_visibility(event=None):
    current = login_password.cget("show")
    if current == "":
        if login_password.get() != "Password":
            login_password.config(show="*")
        show_icon.config(text="👁")
    else:
        login_password.config(show="")
        show_icon.config(text="🙈")

show_icon.bind("<Button-1>", toggle_password_visibility)




def on_entry_click_password(event):
    if login_password.get() == "Password":
        login_password.delete(0, tk.END)
        login_password.config(show="*", fg='black')

def on_focusout_password(event):
    if login_password.get() == "":
        login_password.insert(0, "Password")
        login_password.config(show="", fg='grey')

login_password.bind("<FocusIn>", on_entry_click_password)
login_password.bind("<FocusOut>", on_focusout_password)


remember_checkbox = tk.Checkbutton(login_box, text="📌 Remember Me",font=("Arial", 10), bd=1,highlightthickness=1,highlightbackground="black",selectcolor="white",
activebackground="#fefae0", indicatoron=True, variable=remember_var, bg="#fefae0", fg="black") 
remember_checkbox.pack(anchor="w", padx=0, pady=(0, 10))


#tk.Button(login_box, text="Login", command=login_user).pack(pady=10)
tk.Button(login_box,text="Login",command=login_user,font=("Arial", 11, "bold"),bg="#2196f3",fg="black",             
    activebackground="#1976d2",  
    activeforeground="black",
    relief="raised",
    bd=2
).pack(fill="x", pady=(10, 5))

tk.Label(login_box, text="Don't have an account?", bg="#fefae0",fg="black").pack()
tk.Button(login_box, text="🙋‍♂️ Register Here", command=lambda: show_frame(register_frame)).pack()




from tkinter import messagebox  # Make sure this is imported

# --- Registration Frame ---
register_frame.configure(bg="#d0e7f9")  # Light blue background

# Centered white registration box
register_box = tk.Frame(register_frame, bg="white", bd=2, relief="ridge", padx=25, pady=25)
register_box.place(relx=0.5, rely=0.5, anchor="center")  # Center on screen

tk.Label(register_box, text="📝 Register", font=("Arial", 20, "bold"), fg="#222", bg="white").pack(pady=(0, 20))

# Input: First Name
tk.Label(register_box, text="First Name", font=("Arial", 12), bg="white",fg="black", anchor="w").pack(fill="x")
reg_fname = tk.Entry(register_box, font=("Arial", 11), bg="#f2f2f2", fg="black",insertbackground="black", relief="sunken")
reg_fname.pack(fill="x", ipady=4, pady=(0, 10))

# Input: Last Name
tk.Label(register_box, text="Last Name", font=("Arial", 12), bg="white",fg="black", anchor="w").pack(fill="x")
reg_lname = tk.Entry(register_box, font=("Arial", 11), bg="#f2f2f2", fg="black",insertbackground="black", relief="sunken")
reg_lname.pack(fill="x", ipady=4, pady=(0, 10))

# Input: Email
tk.Label(register_box, text="📧 Email", font=("Arial", 12), bg="white",fg="black", anchor="w").pack(fill="x")
reg_email = tk.Entry(register_box, font=("Arial", 11), bg="#f2f2f2", fg="black",insertbackground="black",relief="sunken")
reg_email.pack(fill="x", ipady=4, pady=(0, 10))

# Input: Password
tk.Label(register_box, text="🔒 Password", font=("Arial", 12), bg="white",fg="black", anchor="w").pack(fill="x")
reg_password = tk.Entry(register_box, show="*", font=("Arial", 11), bg="#f2f2f2", fg="black",insertbackground="black", relief="sunken")
reg_password.pack(fill="x", ipady=4, pady=(0, 10))

# Input: Confirm Password
tk.Label(register_box, text="🔒 Confirm Password", font=("Arial", 12), bg="white",fg="black", anchor="w").pack(fill="x")
reg_confirm = tk.Entry(register_box, show="*", font=("Arial", 11), bg="#f2f2f2", fg="black",insertbackground="black", relief="sunken")
reg_confirm.pack(fill="x", ipady=4, pady=(0, 5))

# Real-time match label
match_label = tk.Label(register_box, text="", font=("Arial", 10, "italic"), bg="white")
match_label.pack()

def check_password_match(event=None):
    if reg_password.get() and reg_confirm.get():
        if reg_password.get() == reg_confirm.get():
            match_label.config(text="✅ Passwords match", fg="green")
        else:
            match_label.config(text="❌ Passwords do not match", fg="red")
    else:
        match_label.config(text="")

reg_password.bind("<KeyRelease>", check_password_match)
reg_confirm.bind("<KeyRelease>", check_password_match)

# Register Button
tk.Button(register_box, text="✅ Register", command=lambda: register_user(),
          font=("Arial", 11, "bold"), bg="#4CAF50", fg="black", relief="raised").pack(fill="x", pady=(10, 5))

# Back Button
tk.Button(register_box, text="🔙 Back to Login", command=lambda: show_frame(login_frame),
          font=("Arial", 10), bg="#e0e0e0", relief="raised").pack(fill="x")


# --- Dashboard Frame UI ---

# Top welcome greeting
dashboard_greeting = tk.Label(dashboard_frame, text="👋 Welcome!", font=("Arial", 18, "bold"), fg="#000000", bg="#6babc3")
dashboard_greeting.pack(fill="x", pady=10)

# Main horizontal layout
main_body = tk.Frame(dashboard_frame, bg="#e0f7fa")
main_body.pack(fill="both", expand=True)

# Left side: Quick Actions panel
action_section = tk.Frame(main_body, bg="#42d2d0", width=200, padx=10, pady=10)
action_section.pack(side="left", fill="y", padx=10, pady=10)

tk.Label(action_section, text="🔧 Quick Actions", font=("Arial", 12, "bold"), bg="#42d2d0", fg="black").pack(anchor="w", pady=(0, 10))

tk.Button(action_section, text="👥 Manage Groups", font=("Arial", 11), command=view_groups).pack(fill="x", pady=2)
tk.Button(action_section, text="➕ Add Expense", font=("Arial", 11),
          command=lambda: [update_groups_in_expense_combo(), show_frame(expense_frame)]).pack(fill="x", pady=2)
#tk.Button(action_section, text="📋 View Balances", font=("Arial", 11), command=update_balances_view).pack(fill="x", pady=2)
tk.Button(action_section, text="📜 View Expense History", font=("Arial", 11), command=show_expense_history).pack(fill="x", pady=2)
tk.Button(action_section, text="📊 Monthly Summary", font=("Arial", 11),
          command=lambda: [clear_frame(monthly_summary_frame),
                           show_frame(monthly_summary_frame),
                           show_monthly_summary(monthly_summary_frame, cursor, logged_in_email, lambda: show_frame(dashboard_frame))]).pack(fill="x", pady=2)



#tk.Button(action_section, text="📊 Monthly Summary", font=("Arial", 11), command=view_monthly_summary).pack(fill="x", pady=2)
tk.Button(action_section, text="💾 Export Expenses (CSV)", font=("Arial", 11), command=export_expenses).pack(fill="x", pady=2)
tk.Button(action_section, text="⚙️ Settings", font=("Arial", 11), command=open_settings).pack(fill="x", pady=2)

tk.Button(action_section, text="\u21AA Logout", command=logout_user).pack(side="bottom", fill="x", pady=(20, 0))



# Right side container: for activity 
right_content = tk.Frame(main_body, bg="#fefae0")
right_content.pack(side="left", fill="both", expand=True, padx=10, pady=10)

# : Recent Activity Feed -----------
recent_activity_frame = tk.LabelFrame(right_content, text="📜 Recent Activity", font=("Arial", 12, "bold"),
                                      bg="#b7ea90", fg="#333", padx=10, pady=5, height=200, labelanchor="nw")
recent_activity_frame.pack(fill="x", padx=5, pady=(0, 10))

activity_box = tk.Frame(recent_activity_frame, bg="#ffffff")
activity_box.pack(fill="x")

activity_scrollbar = tk.Scrollbar(activity_box)
activity_scrollbar.pack(side="right", fill="y")

activity_text = tk.Text(activity_box,
                        height=6,
                        width=60,
                        wrap="word",
                        bg="white",
                        fg="#222",
                        font=("Arial", 10),
                        yscrollcommand=activity_scrollbar.set,
                        relief="flat",
                        padx=8, pady=8)
# Add color + style tags for activity types
activity_text.tag_configure("timestamp", foreground="#888", font=("Arial", 9, "italic"))
activity_text.tag_configure("expense", foreground="#2e7d32", font=("Arial", 10,"italic"))
activity_text.tag_configure("group", foreground="#0d47a1", font=("Arial", 10, "italic"))
activity_text.tag_configure("member", foreground="#6a1b9a", font=("Arial", 10,"italic"))
activity_text.tag_configure("default", foreground="black", font=("Arial", 10,"italic"))
activity_text.tag_configure("section", foreground="#333", font=("Arial", 11, "bold"))


activity_text.pack(side="left", fill="both", expand=True)
activity_scrollbar.config(command=activity_text.yview)

activity_text.insert("end", "No recent activity yet...")
activity_text.config(state="disabled")

# ----------- BOTTOM: Placeholder for future graphs/visuals -----------
dashboard_widgets_frame = tk.Frame(right_content, bg="#fefae0")
dashboard_widgets_frame.pack(fill="both", expand=True)






# --- Expense Frame UI Setup ---
for widget in expense_frame.winfo_children():
    widget.destroy()

expense_frame.configure(bg="#fefae0")  # soft background

tk.Label(expense_frame, text="Add Expense", font=("Arial", 16, "bold"), fg="#333", bg="#fefae0").grid(row=0, column=0, columnspan=2, pady=(10, 10))

tk.Label(expense_frame, text="Amount:", fg="#000", bg="#fefae0").grid(row=1, column=0, sticky="e", padx=10, pady=5)
expense_amount = tk.Entry(expense_frame, bg="white", fg="black",insertbackground="black")
expense_amount.grid(row=1, column=1, padx=10, pady=5)

tk.Label(expense_frame, text="Description:", fg="#000", bg="#fefae0").grid(row=2, column=0, sticky="e", padx=10, pady=5)
expense_desc = tk.Entry(expense_frame, bg="white", fg="black",insertbackground="black")
expense_desc.grid(row=2, column=1, padx=10, pady=5)

tk.Label(expense_frame, text="Category:", fg="#000", bg="#fefae0").grid(row=3, column=0, sticky="e", padx=10, pady=5)
category_var = tk.StringVar()
category_combo = ttk.Combobox(expense_frame, textvariable=category_var, state="readonly")
category_combo['values'] = ("Groceries", "Utilities", "Travel", "Rent", "Dining Out", "Medical", "Entertainment", "Other")
category_combo.grid(row=3, column=1, padx=10, pady=5)

tk.Label(expense_frame, text="Select Group:", fg="#000", bg="#fefae0").grid(row=4, column=0, sticky="e", padx=10, pady=5)
expense_group_combo = ttk.Combobox(expense_frame, state="readonly")
expense_group_combo.grid(row=4, column=1, padx=10, pady=5)

tk.Label(expense_frame, text="Split Type:", fg="#000", bg="#fefae0").grid(row=5, column=0, sticky="ne", padx=10, pady=5)
split_equal_rb = tk.Radiobutton(expense_frame, text="Equal Split", variable=split_type_var, value="equal", bg="#fefae0",fg="black", command=toggle_custom_split)
split_equal_rb.grid(row=5, column=1, sticky="w", padx=10)
split_custom_rb = tk.Radiobutton(expense_frame, text="Customize Split", variable=split_type_var, value="custom", bg="#fefae0",fg="black", command=toggle_custom_split)
split_custom_rb.grid(row=6, column=1, sticky="w", padx=10)

# Recreate and show custom_split_frame properly
custom_split_frame = tk.Frame(expense_frame, bg="#fefae0")
custom_split_frame.grid(row=7, column=0, columnspan=2, pady=5, sticky="w")

tk.Button(expense_frame, text="Add Expense with Split", command=add_expense).grid(row=8, column=0, columnspan=2, pady=10)
tk.Button(expense_frame, text="Back to Dashboard", command=lambda: show_frame(dashboard_frame)).grid(row=9, column=0, columnspan=2, pady=5)

# --- Group Frame (Stylish Upgrade) ---
for widget in group_frame.winfo_children():
    widget.destroy()
group_frame.configure(bg="#d0f0e0")  # Light, refreshing background

tk.Label(group_frame, text="👥 Manage Groups", font=("Arial", 18, "bold"),
         bg="#d0f0e0", fg="#2e7d32").pack(pady=(15, 5))
tk.Button(group_frame, text="⬅ Back to DB", font=("Arial", 10, "bold"),
          bg="#c8e6c9", command=lambda: show_frame(dashboard_frame)).pack(anchor="nw", padx=10, pady=(10, 4))

# ===== Create Group Section =====
create_group_box = tk.Frame(group_frame, bg="#6babc3", bd=2, relief="ridge", padx=15, pady=15)
create_group_box.pack(padx=20, pady=10, fill="x")



tk.Label(create_group_box, text="➕ Create New Group", font=("Arial", 12, "bold"),
         bg="white", fg="#004d40").pack(anchor="w")
group_name_entry = tk.Entry(create_group_box, font=("Arial", 11), bg="#f7f7f7",fg="black", relief="sunken")
group_name_entry.pack(fill="x", pady=5)
tk.Button(create_group_box, text="Add Group", bg="#81c784", fg="black",
          font=("Arial", 10, "bold"), command=add_group).pack(pady=5)

# ===== Your Groups Section =====
group_list_box = tk.Frame(group_frame, bg="#6babc3", bd=2, relief="ridge", padx=15, pady=15)
group_list_box.pack(padx=20, pady=10, fill="x")

tk.Label(group_list_box, text="📋 Your Groups", font=("Arial", 12, "bold"),
         bg="white", fg="#004d40").pack(anchor="w")
group_list = tk.Listbox(group_list_box, height=8, font=("Arial", 11),
                        bg="#e8f5e9",fg="black",selectbackground="#a5d6a7", relief="flat")
group_list.pack(fill="x", pady=5)

# ===== Add Member Section =====
add_member_box = tk.Frame(group_frame, bg="#6babc3", bd=2, relief="ridge", padx=15, pady=15)
add_member_box.pack(padx=20, pady=10, fill="x")

tk.Label(add_member_box, text="📧 Add Member Email", font=("Arial", 12),
         bg="white", fg="#004d40").pack(anchor="w")
member_email_entry = tk.Entry(add_member_box, font=("Arial", 11), bg="#f7f7f7",fg="red", relief="sunken")
member_email_entry.pack(fill="x", pady=5)
tk.Button(add_member_box, text="Add Member to Selected Group", bg="#4db6ac", fg="black",
          font=("Arial", 10, "bold"), command=add_member_to_group).pack(pady=5)
tk.Button(group_frame, text="👥 View Group Members", font=("Arial", 10, "bold"),
          bg="#c5cae9", fg="black", command=view_selected_group_members_popup).pack(pady=5)
tk.Button(group_frame, text="Settle Up Balances", bg="#ffcccc",
          command=lambda: settle_up(current_group_id, logged_in_email, cursor, conn)).pack(pady=5)


# ===== Bottom Action Buttons =====
tk.Button(group_frame, text="📊 View Group Balances", font=("Arial", 11, "bold"),
          bg="#fff176", fg="black", relief="raised", command=view_group_balances).pack(pady=(15, 5))

# --- Settings Frame (Modern Style) ---
for widget in settings_frame.winfo_children():
    widget.destroy()

settings_frame.configure(bg="#f5f5f5")

# Split layout: Sidebar (left) and Content Panel (right)
sidebar = tk.Frame(settings_frame, bg="#42d2d0", width=150)
sidebar.pack(side="left", fill="y")

content_panel = tk.Frame(settings_frame, bg="#fefae0")
content_panel.pack(side="left", fill="both", expand=True)

# Sidebar Buttons
def switch_content(section):
    for widget in content_panel.winfo_children():
        widget.destroy()

    if section == "password":
        tk.Label(content_panel, text="🔐 Change Password", font=("Arial", 14, "bold"),
                bg="#fefae0", fg="black").pack(pady=10)

        tk.Label(content_panel, text="Current Password", bg="#fefae0", fg="black").pack()
        cp = tk.Entry(content_panel, show="*", bg="white", fg="black", insertbackground="black")
        cp.pack(pady=5)

        tk.Label(content_panel, text="New Password", bg="#fefae0", fg="black").pack()
        np = tk.Entry(content_panel, show="*", bg="white", fg="black", insertbackground="black")
        np.pack(pady=5)
        def submit_new_password():
            current = hash_password(cp.get())
            new = hash_password(np.get())
            cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (logged_in_email, current))
            if cursor.fetchone():
                if not np.get():
                    messagebox.showerror("Error", "New password cannot be empty.")
                    return
                cursor.execute("UPDATE users SET password=? WHERE email=?", (new, logged_in_email))
                conn.commit()
                messagebox.showinfo("Success", "Password updated.")
                cp.delete(0, tk.END)
                np.delete(0, tk.END)
            else:
                messagebox.showerror("Error", "Current password is incorrect.")
        tk.Button(content_panel, text="Update Password", command=submit_new_password, bg="#e6eee6", fg="black").pack(pady=10)

    elif section == "notifications":
        tk.Label(content_panel, text="🔔 Notification Preferences", font=("Arial", 14, "bold"), bg="white", fg="black").pack(pady=10)
        notif_check = tk.Checkbutton(content_panel, text="Enable Notifications", variable=notif_var,
                                     command=toggle_notifications, bg="white", fg="black")
        notif_check.pack(pady=10)

    elif section == "deactivate":
        tk.Label(content_panel, text="🚫 Deactivate Account", font=("Arial", 14, "bold"), bg="white",fg="black").pack(pady=10)
        tk.Label(content_panel, text="You will not be able to log in until reactivated.", bg="white",fg="black").pack()
        tk.Button(content_panel, text="Deactivate", bg="#ffb74d", command=deactivate_account).pack(pady=10)

    elif section == "delete":
        tk.Label(content_panel, text="🗑️ Delete Account", font=("Arial", 14, "bold"), bg="white",fg="black").pack(pady=10)
        tk.Label(content_panel, text="All your data will be permanently deleted.", bg="white",fg="black").pack()
        tk.Button(content_panel, text="Delete Permanently", bg="white", fg="black", command=delete_account).pack(pady=10)

    elif section == "back":
        show_frame(dashboard_frame)


# Sidebar Buttons
tk.Label(sidebar, text="⚙️ Settings", font=("Arial", 14, "bold"), bg="#42d2d0", fg="black").pack(pady=(20, 10))

buttons = [
    ("🔐 Change Password", "password"),
    ("🔔 Notifications", "notifications"),
    ("🚫 Deactivate Account", "deactivate"),
    ("🗑️ Delete Account", "delete"),
    ("⬅️ Back", "back")
]

for label, section in buttons:
    tk.Button(sidebar, text=label, command=lambda sec=section: switch_content(sec),
              font=("Arial", 10), bg="#37474f", fg="black", relief="flat", anchor="w", padx=10).pack(fill="x", pady=2)

# Load default section
switch_content("password")




#Auto-Fill Login Email if Remember Me was Used
saved_email = get_remember_email()
if saved_email:
    login_email.insert(0, saved_email)
    remember_var.set(1)

show_frame(login_frame)
root.mainloop()





