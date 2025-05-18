import sqlite3
import pandas as pd

# Path to the SQLite database
DB_PATH = r"C:\Users\krem_\OneDrive\Desktop\Bitirme Projesi\attendance.db"

def show_attendance(date=None, status_filter=None):
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)

    # Base SQL query to select attendance data
    query = """
        SELECT students.name AS name, attendance_logs.date AS date, attendance_logs.status AS status
        FROM attendance_logs
        JOIN students ON students.id = attendance_logs.student_id
    """

    conditions = []
    params = []

    # Add date filter if provided
    if date:
        conditions.append("attendance_logs.date = ?")
        params.append(date)

    # Add status filter ('here' or 'absent') if provided
    if status_filter in ("here", "absent"):
        conditions.append("attendance_logs.status = ?")
        params.append(status_filter)

    # Combine conditions in WHERE clause
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Order by date (descending) and student name
    query += " ORDER BY attendance_logs.date DESC, students.name"

    # Read results into a DataFrame
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    # Print results or show message if empty
    if df.empty:
        print("No records found.")
    else:
        print("\n", df.to_string(index=False))

if __name__ == "__main__":
    # Get date filter from user
    print("Enter date (YYYY-MM-DD) or leave blank:")
    date = input("Date: ").strip()

    # Get status filter from user
    print("Enter status filter: 'here', 'absent' or leave blank:")
    status = input("Status: ").strip().lower()

    date = date if date else None
    status = status if status in ("here", "absent") else None

    show_attendance(date, status)
