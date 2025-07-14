import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime

def show_monthly_summary(frame, cursor, logged_in_email, show_dashboard_callback):
    # Clear the frame first
    for widget in frame.winfo_children():
        widget.destroy()

    # Top header row with Back button and Title
    header_frame = tk.Frame(frame, bg="white")
    header_frame.pack(fill="x", pady=10, padx=10)

    back_button = tk.Button(
        header_frame,
        text="⬅ Back to DB",
        font=("Arial", 10, "bold"),
        bg="#e0e0e0",
        fg="black",
        relief="raised",
        command=show_dashboard_callback
    )
    back_button.pack(side="left")

    title_label = tk.Label(
        frame,
        text="📊 Monthly Summary",
        font=("Arial", 16, "bold"),
        bg="white",
        fg="#333"
    )
    title_label.pack(pady=10, anchor="n")

    # Scrollable area setup
    canvas = tk.Canvas(frame, bg="white")
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Query monthly totals
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

    # Convert YYYY-MM to month abbreviation like "Jul"
    months = [datetime.strptime(row[0], "%Y-%m").strftime("%B %Y") for row in data]
    totals = [row[1] for row in data]

    # Plot bar chart
    fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
    bars = ax.bar(months, totals, color="#119764")

    # Hide Y-axis ticks and left spine
    ax.yaxis.set_ticks([])
    ax.spines['left'].set_visible(False)

    # Add value labels on top of bars
    for bar, amount in zip(bars, totals):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 5,
            f"${int(amount):,}",
            ha='center',
            va='bottom',
            fontsize=9,
            fontweight='bold'
        )

    # Customize X-axis
    ax.set_xlabel("Month", fontsize=10)
    ax.set_ylabel("")  # Remove Y-axis label
    ax.set_title("Monthly Expense Overview", fontsize=13)
    ax.tick_params(axis='x', rotation=0)

    # Embed chart into Tkinter
    chart = FigureCanvasTkAgg(fig, master=scrollable_frame)
    chart.draw()
    chart.get_tk_widget().pack(pady=10, padx=20, fill="both", expand=True)
