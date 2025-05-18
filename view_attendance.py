import sqlite3
import pandas as pd

DB_PATH = r"C:\Users\krem_\OneDrive\Desktop\Bitirme Projesi\attendance.db"

def show_attendance(date=None, status_filter=None):
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT students.name AS isim, attendance_logs.date AS tarih, attendance_logs.status AS durum
        FROM attendance_logs
        JOIN students ON students.id = attendance_logs.student_id
    """

    conditions = []
    params = []

    if date:
        conditions.append("attendance_logs.date = ?")
        params.append(date)

    if status_filter in ("here", "absent"):
        conditions.append("attendance_logs.status = ?")
        params.append(status_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY attendance_logs.date DESC, students.name"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if df.empty:
        print("Kayıt bulunamadı.")
    else:
        print("\n", df.to_string(index=False))

if __name__ == "__main__":
    print("Tarih girin (YYYY-MM-DD) veya boş bırakın:")
    date = input("Tarih: ").strip()

    print("Durum filtresi girin: 'here', 'absent' veya boş bırakın:")
    status = input("Durum: ").strip().lower()

    date = date if date else None
    status = status if status in ("here", "absent") else None

    show_attendance(date, status)
