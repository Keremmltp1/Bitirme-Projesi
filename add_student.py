import tkinter as tk
from tkinter import messagebox
import sqlite3
import os

DB_PATH = r"C:\\Users\\krem_\\OneDrive\\Desktop\\Bitirme Projesi\\attendance.db"

def add_student_to_db(name, surname, student_number, class_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO students (name, surname, student_number, class_name)
            VALUES (?, ?, ?, ?)
        """, (name, surname, student_number, class_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def open_add_student_window():
    window = tk.Tk()
    window.title("Yeni Öğrenci Ekle")
    window.geometry("400x350")

    tk.Label(window, text="İsim:").pack(pady=5)
    entry_name = tk.Entry(window)
    entry_name.pack(pady=5)

    tk.Label(window, text="Soyisim:").pack(pady=5)
    entry_surname = tk.Entry(window)
    entry_surname.pack(pady=5)

    tk.Label(window, text="Sınıf:").pack(pady=5)
    entry_class = tk.Entry(window)
    entry_class.pack(pady=5)

    tk.Label(window, text="Öğrenci No:").pack(pady=5)
    entry_number = tk.Entry(window)
    entry_number.pack(pady=5)

    def on_submit():
        name = entry_name.get().strip()
        surname = entry_surname.get().strip()
        class_name = entry_class.get().strip()
        student_number = entry_number.get().strip()

        if not all([name, surname, class_name, student_number]):
            messagebox.showerror("Hata", "Tüm alanları doldurun.")
            return

        success = add_student_to_db(name, surname, student_number, class_name)
        if success:
            messagebox.showinfo("Başarılı", "Öğrenci eklendi.")
            window.destroy()
        else:
            messagebox.showerror("Hata", "Bu öğrenci numarası zaten kayıtlı.")

    tk.Button(window, text="Ekle", command=on_submit, bg="#4caf50", fg="white").pack(pady=20)

    window.mainloop()

if __name__ == "__main__":
    open_add_student_window()
