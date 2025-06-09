import tkinter as tk
from tkinter import messagebox, ttk
from logic import ExpenseManager

manager = ExpenseManager()
user_id = None
group_id = None

def launch_app():
    def attempt_login():
        global user_id
        username = login_user.get()
        password = login_pass.get()
        user = manager.login_user(username, password)
        if user:
            user_id = user
            messagebox.showinfo("Login Success", f"Welcome, {username}!")
            login_frame.pack_forget()
            group_frame.pack()
        else:
            messagebox.showerror("Login Failed", "Incorrect credentials")

    def attempt_register():
        username = reg_user.get()
        password = reg_pass.get()
        if manager.register_user(username, password):
            messagebox.showinfo("Success", "Account created.")
            register_frame.pack_forget()
            login_frame.pack()
        else:
            messagebox.showerror("Error", "Username already exists")

    def switch_to_register():
        login_frame.pack_forget()
        register_frame.pack()

    def switch_to_login():
        register_frame.pack_forget()
        login_frame.pack()

    def attempt_group():
        global group_id
        group_name = group_name_entry.get()
        if group_name:
            group_id = manager.create_group(group_name)
            messagebox.showinfo("Group Selected", f"Group: {group_name}")
            group_frame.pack_forget()
            show_dashboard()

    def add_expense():
        title = entry_name.get()
        amount = entry_amount.get()
        split_type = split_var.get()
        if title and amount:
            try:
                manager.add_expense(group_id, title, float(amount), split_type)
                messagebox.showinfo("Success", "Expense added.")
                entry_name.delete(0, tk.END)
                entry_amount.delete(0, tk.END)
                update_history()
            except ValueError:
                messagebox.showerror("Error", "Invalid amount")
        else:
            messagebox.showwarning("Missing Info", "Enter title and amount")

    def delete_selected():
        try:
            selected = history_box.curselection()[0]
            item = history_box.get(selected)
            expense_id = int(item.split(":")[0])
            manager.delete_expense(expense_id)
            update_history()
        except:
            messagebox.showerror("Error", "Select a valid expense")

    def export_data():
        manager.export_to_csv(group_id)
        messagebox.showinfo("Exported", "Data saved to expenses_export.csv")

    def view_total():
        total = manager.calculate_total(group_id)
        messagebox.showinfo("Balance", f"Total group expenses: ${total:.2f}")

    def update_history():
        history_box.delete(0, tk.END)
        for row in manager.fetch_expenses(group_id):
            history_box.insert(tk.END, f"{row[0]}: {row[1]} - ${row[2]:.2f} ({row[3]})")

    def show_dashboard():
        dashboard_frame.pack()

    # App root
    app = tk.Tk()
    app.title("Roommate Expense Splitter")

    # Login Frame
    login_frame = tk.Frame(app)
    tk.Label(login_frame, text="Username").grid(row=0, column=0)
    login_user = tk.Entry(login_frame)
    login_user.grid(row=0, column=1)

    tk.Label(login_frame, text="Password").grid(row=1, column=0)
    login_pass = tk.Entry(login_frame, show="*")
    login_pass.grid(row=1, column=1)

    tk.Button(login_frame, text="Login", command=attempt_login).grid(row=2, column=0)
    tk.Button(login_frame, text="Register", command=switch_to_register).grid(row=2, column=1)
    login_frame.pack(pady=10)

    # Register Frame
    register_frame = tk.Frame(app)
    tk.Label(register_frame, text="New Username").grid(row=0, column=0)
    reg_user = tk.Entry(register_frame)
    reg_user.grid(row=0, column=1)

    tk.Label(register_frame, text="New Password").grid(row=1, column=0)
    reg_pass = tk.Entry(register_frame, show="*")
    reg_pass.grid(row=1, column=1)

    tk.Button(register_frame, text="Submit Registration", command=attempt_register).grid(row=2, column=0, columnspan=2)
    tk.Button(register_frame, text="Back to Login", command=switch_to_login).grid(row=3, column=0, columnspan=2)

    # Group Frame
    group_frame = tk.Frame(app)
    tk.Label(group_frame, text="Enter or Select Group").grid(row=0, column=0)
    group_name_entry = tk.Entry(group_frame)
    group_name_entry.grid(row=0, column=1)
    tk.Button(group_frame, text="Join Group", command=attempt_group).grid(row=1, column=0, columnspan=2)

    # Dashboard Frame
    dashboard_frame = tk.Frame(app)

    tk.Label(dashboard_frame, text="Expense Name").grid(row=0, column=0)
    entry_name = tk.Entry(dashboard_frame)
    entry_name.grid(row=0, column=1)

    tk.Label(dashboard_frame, text="Amount").grid(row=1, column=0)
    entry_amount = tk.Entry(dashboard_frame)
    entry_amount.grid(row=1, column=1)

    tk.Label(dashboard_frame, text="Split Type").grid(row=2, column=0)
    split_var = tk.StringVar(value="Equal")
    split_dropdown = ttk.Combobox(dashboard_frame, textvariable=split_var)
    split_dropdown['values'] = ["Equal", "Custom"]
    split_dropdown.grid(row=2, column=1)

    tk.Button(dashboard_frame, text="Add Expense", command=add_expense).grid(row=3, column=0, columnspan=2, pady=4)
    tk.Label(dashboard_frame, text="History").grid(row=4, column=0, columnspan=2)
    history_box = tk.Listbox(dashboard_frame, width=50)
    history_box.grid(row=5, column=0, columnspan=2)

    tk.Button(dashboard_frame, text="Delete Selected", command=delete_selected).grid(row=6, column=0)
    tk.Button(dashboard_frame, text="View Total", command=view_total).grid(row=6, column=1)
    tk.Button(dashboard_frame, text="Export to CSV", command=export_data).grid(row=7, column=0, columnspan=2)

    app.mainloop()
