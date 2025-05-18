import sqlite3
import os

DB_PATH = r"C:\\Users\\krem_\\OneDrive\\Desktop\\Bitirme Projesi\\attendance.db"

# Mevcut veritabanı varsa sil
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Öğrenci tablosu - sınıf, numara, soyisim eklendi
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    student_number TEXT NOT NULL UNIQUE,
    class_name TEXT NOT NULL
)
""")

# Yoklama kayıt tablosu
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('here', 'absent')),
    UNIQUE(student_id, date),
    FOREIGN KEY(student_id) REFERENCES students(id)
)
""")

conn.commit()
conn.close()
print("Veritabanı başarıyla oluşturuldu:", DB_PATH)
