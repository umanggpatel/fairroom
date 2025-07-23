import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.ticker as mtick

def show_monthly_summary(frame, cursor, logged_in_email, show_dashboard_callback):
    # Clear the frame
    for widget in frame.winfo_children():
        widget.destroy()

    # Header Frame
    header_frame = tk.Frame(frame, bg="white")
    header_frame.pack(fill="x", pady=10, padx=10)

    tk.Button(
        header_frame, text="⬅ Back to DB", font=("Arial", 10, "bold"),
        bg="#e0e0e0", fg="black", relief="raised", command=show_dashboard_callback
    ).pack(side="left")

    tk.Label(
        frame, text="📊 Monthly Summary", font=("Arial", 16, "bold"),
        bg="white", fg="#333"
    ).pack(pady=10, anchor="n")

    # Scrollable Area
    canvas = tk.Canvas(frame, bg="white")
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # ========== Monthly Bar Chart ==========
    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount)
        FROM expenses
        WHERE user_email=?
        GROUP BY month
        ORDER BY month
    """, (logged_in_email,))
    data = cursor.fetchall()

    if not data:
        tk.Label(scrollable_frame, text="No data available.", bg="white", fg="gray").pack(pady=20)
        return

    months = [datetime.strptime(row[0], "%Y-%m").strftime("%B %Y") for row in data]
    totals = [row[1] for row in data]

    fig1, ax1 = plt.subplots(figsize=(7, 4), dpi=100)
    bars = ax1.bar(months, totals, color="#119764")
    ax1.set_xlabel("Month", fontsize=10)
    ax1.set_ylabel("Total Amount($)", fontsize=10)
    ax1.set_title("Monthly Expense Overview", fontsize=13)
    ax1.tick_params(axis='x', rotation=0)
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${int(x):,}"))
    for bar, amount in zip(bars, totals):
        ax1.text(bar.get_x() + bar.get_width() / 2, amount, f"${int(amount):,}", ha='center', va='bottom', fontsize=9)

    canvas1 = FigureCanvasTkAgg(fig1, master=scrollable_frame)
    canvas1.draw()
    canvas1.get_tk_widget().pack(pady=10)

    # ========== Side-by-side Charts Frame ==========
    dual_frame = tk.Frame(scrollable_frame, bg="white")
    dual_frame.pack(fill="x", padx=20)


# Get all users who owe the logged-in user money (i.e., to_user = you)
    cursor.execute("""
        SELECT from_user, SUM(amount)
        FROM balances
        WHERE to_user=?
        GROUP BY from_user
    """, (logged_in_email,))
    owe_data = cursor.fetchall()


    parties = [row[0] for row in owe_data]
    amounts = [row[1] for row in owe_data]

    fig3, ax3 = plt.subplots(figsize=(4.5, 4), dpi=100)
    bars2 = ax3.barh(parties, amounts, color="#d9534f")
    ax3.set_xlabel("Amount ($)")
    ax3.set_title("You Owe (per Person)")

    for bar, amount in zip(bars2, amounts):
        ax3.text(amount + 0.1, bar.get_y() + bar.get_height() / 2, f"${amount:.2f}", va='center', fontsize=9)

    canvas3 = FigureCanvasTkAgg(fig3, master=dual_frame)
    canvas3.draw()
    canvas3.get_tk_widget().pack(side="left", padx=10)

