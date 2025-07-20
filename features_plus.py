from tkinter import messagebox

def settle_up(group_id, user_email, cursor, conn):
    cursor.execute("""
        SELECT to_user, SUM(amount) FROM balances
        WHERE from_user = ? AND group_id = ?
        GROUP BY to_user
    """, (user_email, group_id))
    rows = cursor.fetchall()

    if not rows:
        messagebox.showinfo("Nothing to Settle", "You don't owe anything in this group.")
        return

    msg = "\n".join([f"You owe {to_user}: ${amt:.2f}" for to_user, amt in rows])
    msg += "\n\nAre you sure you want to settle all balances?"

    if not messagebox.askyesno("Confirm Settle Up", msg):
        return

    # Delete only balances where user owes someone
    cursor.execute("""
        DELETE FROM balances WHERE from_user = ? AND group_id = ?
    """, (user_email, group_id))
    conn.commit()

     log activity
    cursor.execute("""
        INSERT INTO activities (user_email, activity)
        VALUES (?, ?)
    """, (user_email, f"Settled all balances in group {group_id}"))
    conn.commit()

    messagebox.showinfo("Settled!", "All your owed balances are now cleared.")
