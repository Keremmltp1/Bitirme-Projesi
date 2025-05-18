import tkinter as tk
from tkinter import messagebox
import sqlite3
import os

DB_PATH = r"C:\\Users\\krem_\\OneDrive\\Desktop\\Bitirme Projesi\\attendance.db"

def add_student_to_db(name, surname, student_number, class_name):
    # Insert a new student record into the database
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
        # Student number already exists
        return False
    finally:
        conn.close()

def open_add_student_window():
    # GUI for adding a new student
    window = tk.Tk()
    window.title("Add New Student")
    window.geometry("400x350")

    tk.Label(window, text="First Name:").pack(pady=5)
    entry_name = tk.Entry(window)
    entry_name.pack(pady=5)

    tk.Label(window, text="Last Name:").pack(pady=5)
    entry_surname = tk.Entry(window)
    entry_surname.pack(pady=5)

    tk.Label(window, text="Class:").pack(pady=5)
    entry_class = tk.Entry(window)
    entry_class.pack(pady=5)

    tk.Label(window, text="Student Number:").pack(pady=5)
    entry_number = tk.Entry(window)
    entry_number.pack(pady=5)

    def on_submit():
        # Handler for the "Add" button
        name = entry_name.get().strip()
        surname = entry_surname.get().strip()
        class_name = entry_class.get().strip()
        student_number = entry_number.get().strip()

        if not all([name, surname, class_name, student_number]):
            messagebox.showerror("Error", "Please fill all fields.")
            return

        success = add_student_to_db(name, surname, student_number, class_name)
        if success:
            messagebox.showinfo("Success", "Student added successfully.")
            window.destroy()
        else:
            messagebox.showerror("Error", "This student number is already registered.")

    tk.Button(window, text="Add", command=on_submit, bg="#4caf50", fg="white").pack(pady=20)

    window.mainloop()

if __name__ == "__main__":
    open_add_student_window()
