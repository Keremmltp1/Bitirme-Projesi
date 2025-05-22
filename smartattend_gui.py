import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3
import hashlib
import os
from PIL import Image, ImageTk
import datetime
import cv2
import numpy as np
import pickle
import face_recognition
import mediapipe as mp
from tkcalendar import DateEntry
import time
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import pandas as pd
import re
import threading

BASE_PATH = r"C:\\Users\\krem_\\OneDrive\\Desktop\\Bitirme Projesi"
DB_PATH = os.path.join(BASE_PATH, "attendance.db")
ENCODING_DIR = os.path.join(BASE_PATH, "encodings")
LOGO_PATH = os.path.join(BASE_PATH, "logo.png")

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_student_password(name, student_number):
    clean_name = name.strip().replace(" ", "")
    clean_number = re.sub(r"\D", "", student_number)
    if len(clean_name) < 3 or len(clean_number) < 3:
        return "000000"
    return (clean_name[:3] + clean_number[:3]).lower()

def upgrade_student_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(students)")
    columns = [row[1] for row in cursor.fetchall()]
    if "password_hash" not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN password_hash TEXT")
    conn.commit()
    conn.close()
upgrade_student_table()

def create_teacher_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
    )""")
    conn.commit()
    conn.close()
create_teacher_table()

def register_teacher_window(parent):
    reg_win = tk.Toplevel(parent)
    reg_win.title("Register Teacher")
    reg_win.geometry("350x330")
    reg_win.resizable(False, False)

    tk.Label(reg_win, text="Name:").pack(pady=5)
    name_entry = tk.Entry(reg_win)
    name_entry.pack()
    tk.Label(reg_win, text="Email:").pack(pady=5)
    email_entry = tk.Entry(reg_win)
    email_entry.pack()
    tk.Label(reg_win, text="Password:").pack(pady=5)
    password_entry = tk.Entry(reg_win, show="*")
    password_entry.pack()
    tk.Label(reg_win, text="Confirm Password:").pack(pady=5)
    confirm_entry = tk.Entry(reg_win, show="*")
    confirm_entry.pack()

    def on_register():
        name = name_entry.get().strip()
        email = email_entry.get().strip()
        password = password_entry.get().strip()
        confirm = confirm_entry.get().strip()
        if not name or not email or not password or not confirm:
            messagebox.showerror("Error", "All fields are required.", parent=reg_win)
            return
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.", parent=reg_win)
            return
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO teachers (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, hash_password(password))
            )
            conn.commit()
            messagebox.showinfo("Success", "Teacher registered successfully.", parent=reg_win)
            reg_win.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Email already registered.", parent=reg_win)
        finally:
            conn.close()

    tk.Button(reg_win, text="Register", command=on_register, bg="#4caf50", fg="white", width=15).pack(pady=15)

def student_login_window():
    win = tk.Tk()
    win.title("SmartAttend Öğrenci Girişi")
    win.geometry("400x330")
    win.configure(bg="white")
    tk.Label(win, text="Öğrenci Girişi", font=("Segoe UI", 18, "bold"), bg="white").pack(pady=(35, 15))

    tk.Label(win, text="Öğrenci Numarası:", bg="white", font=("Segoe UI", 12)).pack()
    number_entry = tk.Entry(win, font=("Segoe UI", 12))
    number_entry.pack(pady=4)

    tk.Label(win, text="Şifre:", bg="white", font=("Segoe UI", 12)).pack()
    password_entry = tk.Entry(win, show="*", font=("Segoe UI", 12))
    password_entry.pack(pady=4)

    def try_student_login():
        number = number_entry.get().strip()
        password = password_entry.get().strip()
        if not number or not password:
            messagebox.showerror("Hata", "Tüm alanları doldurun.", parent=win)
            return
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, surname, password_hash FROM students WHERE student_number = ?", (number,))
        user = cursor.fetchone()
        conn.close()
        if user and hash_password(password) == user[3]:
            win.destroy()
            student_dashboard(user[0], user[1], user[2], number)
        else:
            messagebox.showerror("Hata", "Numara veya şifre yanlış.", parent=win)

    tk.Button(win, text="Giriş Yap", command=try_student_login, font=("Segoe UI", 12), width=12, bg="#2196f3", fg="white").pack(pady=18)
    win.mainloop()

def student_dashboard(student_id, name, surname, student_number):
    win = tk.Tk()
    win.title("SmartAttend Öğrenci Paneli")
    win.geometry("600x400")
    win.configure(bg="white")
    tk.Label(win, text=f"Hoş geldin {name} {surname}!", font=("Segoe UI", 18, "bold"), bg="white").pack(pady=24)

    frame = tk.Frame(win, bg="white")
    frame.pack(pady=8)
    tk.Label(frame, text=f"Numaran: {student_number}", font=("Segoe UI", 12), bg="white").pack(pady=2)
    result_text = tk.Text(win, height=14, width=65, font=("Consolas", 11))
    result_text.pack(pady=12)

    def load_attendance():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.date, a.status FROM attendance_logs a
            WHERE a.student_id = ?
            ORDER BY a.date DESC
        """, (student_id,))
        rows = cursor.fetchall()
        conn.close()
        result_text.delete("1.0", tk.END)
        if not rows:
            result_text.insert(tk.END, "Yoklama kaydı bulunamadı.")
        else:
            for row in rows:
                tarih, status = row
                durum = "HERE" if status == "here" else "ABSENT"
                result_text.insert(tk.END, f"{tarih}: {durum}\n")
    load_attendance()
    win.bind("<FocusIn>", lambda e: load_attendance())
    win.mainloop()

def open_add_student():
    os.system(f"python \"{os.path.join(BASE_PATH, 'add_student.py')}\"")

def import_students_from_excel():
    file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls")])
    if not file_path:
        return

    try:
        df = pd.read_excel(file_path, header=10)
    except Exception as e:
        messagebox.showerror("Error", f"Could not read Excel file:\n{e}")
        return

    def normalize(col):
        col = col.lower()
        col = col.replace("ö", "o").replace("ç", "c").replace("ü", "u").replace("ş", "s").replace("ı", "i").replace("ğ", "g")
        return col

    name_col = None
    number_col = None
    class_col = None
    for col in df.columns:
        ncol = normalize(col)
        if "adi soyadi" in ncol or ("ad" in ncol and "soyad" in ncol):
            name_col = col
        if "ogrenci no" in ncol or ("no" in ncol and "ogrenci" in ncol):
            number_col = col
        if "sinif" in ncol:
            class_col = col
    if not name_col or not number_col or not class_col:
        messagebox.showerror("Error", "Gerekli sütunlar bulunamadı! (Adı Soyadı, Öğrenci No, Sınıfı). Excel başlıklarını kontrol et.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    added = 0
    skipped = 0
    for idx, row in df.iterrows():
        full_name = str(row[name_col]).strip()
        student_number_raw = str(row[number_col]).strip()
        class_value = str(row[class_col]).strip()
        if not full_name or not student_number_raw or not class_value or "nan" in full_name.lower():
            skipped += 1
            continue
        name_parts = full_name.split()
        name = []
        surname = []
        for part in name_parts:
            if part.isupper() and len(part) > 1:
                surname.append(part)
            else:
                name.append(part.capitalize())
        name_str = " ".join(name)
        surname_str = " ".join(surname)
        student_number = re.sub(r'\s+', '', student_number_raw)
        try:
            class_int = int(float(class_value))
            class_name = f"{class_int}. Sınıf"
        except Exception:
            class_name = "Bilinmeyen Sınıf"
        password = generate_student_password(name_str, student_number)
        password_hash = hash_password(password)
        if not name_str or not surname_str or not student_number or not class_name:
            skipped += 1
            continue
        try:
            cursor.execute("""
                INSERT INTO students (name, surname, student_number, class_name, password_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (name_str, surname_str, student_number, class_name, password_hash))
            added += 1
        except sqlite3.IntegrityError:
            skipped += 1
            continue
    conn.commit()
    conn.close()
    messagebox.showinfo("Import Result", f"Added: {added} student(s)\nSkipped: {skipped} (empty or duplicate)")

def get_classes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT class_name FROM students ORDER BY class_name")
    classes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return classes

def get_students_by_class(class_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name || ' ' || surname || ' (' || student_number || ')'
        FROM students WHERE class_name = ?
        ORDER BY name, surname
    """, (class_name,))
    students = cursor.fetchall()
    conn.close()
    return students

def get_all_dates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT date FROM attendance_logs ORDER BY date DESC")
    dates = [row[0] for row in cursor.fetchall()]
    conn.close()
    return dates

def save_encoding(student_id, encoding):
    os.makedirs(ENCODING_DIR, exist_ok=True)
    save_path = os.path.join(ENCODING_DIR, f"{student_id}.pkl")
    with open(save_path, 'wb') as f:
        pickle.dump(encoding, f)

def open_register_gui(reset_btn_color):
    window = tk.Toplevel()
    window.title("Face Registration")
    window.geometry("750x600")
    tk.Label(window, text="Select Class:").pack()
    class_combo = ttk.Combobox(window, state="readonly", values=get_classes())
    class_combo.pack()
    tk.Label(window, text="Select Student:").pack()
    student_combo = ttk.Combobox(window, state="readonly")
    student_combo.pack()
    student_ids = {}
    video_canvas = tk.Label(window, width=640, height=360, bg="black")
    video_canvas.pack(pady=10)
    status_label = tk.Label(window, text="")
    status_label.pack()
    cap = [None]
    running = [False]

    def start_camera():
        cap[0] = cv2.VideoCapture(0)
        if not cap[0].isOpened():
            status_label.config(text="Camera could not be opened.", fg="red")
            return
        for _ in range(5):
            cap[0].read()
        running[0] = True
        update_frame()

    def update_frame():
        if not running[0] or cap[0] is None:
            return
        ret, frame = cap[0].read()
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            video_canvas.imgtk = imgtk
            video_canvas.image = imgtk
            video_canvas.configure(image=imgtk)
        video_canvas.after(30, update_frame)

    def capture_face():
        selected = student_combo.get()
        student_id = student_ids.get(selected)
        if not student_id:
            status_label.config(text="No student selected.", fg="red")
            return
        ret, frame = cap[0].read()
        if not ret:
            status_label.config(text="Camera frame could not be captured.", fg="red")
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb)
        if len(faces) != 1:
            status_label.config(text="Please show only one face.", fg="orange")
            return
        encoding = face_recognition.face_encodings(rgb, faces)[0]
        save_encoding(student_id, encoding)
        status_label.config(text="Registration successful.", fg="green")

    def upload_photo():
        selected = student_combo.get()
        student_id = student_ids.get(selected)
        if not student_id:
            status_label.config(text="No student selected.", fg="red")
            return
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if not file_path:
            return
        image = face_recognition.load_image_file(file_path)
        face_locations = face_recognition.face_locations(image)
        if len(face_locations) != 1:
            status_label.config(text="The photo must contain exactly one face!", fg="orange")
            return
        encoding = face_recognition.face_encodings(image, face_locations)[0]
        save_encoding(student_id, encoding)
        status_label.config(text="Registration successful (photo).", fg="green")

    def on_class_selected(event):
        selected_class = class_combo.get()
        students = get_students_by_class(selected_class)
        student_combo['values'] = [s[1] for s in students]
        student_ids.clear()
        for sid, label in students:
            student_ids[label] = sid
        student_combo.set("")

    class_combo.bind("<<ComboboxSelected>>", on_class_selected)
    tk.Button(window, text="Register by Camera", command=capture_face, bg="#4caf50", fg="white").pack(pady=5)
    tk.Button(window, text="Register by Photo", command=upload_photo, bg="#9c27b0", fg="white").pack(pady=5)

    def on_close():
        running[0] = False
        if cap[0]:
            cap[0].release()
        window.destroy()
        reset_btn_color()

    window.protocol("WM_DELETE_WINDOW", on_close)
    start_camera()
    return window

def open_attendance_gui(reset_btn_color):
    win = tk.Toplevel()
    win.title("Attendance Recognition")
    win.geometry("1024x700")
    tk.Label(win, text="Select Class:").pack(pady=5)
    class_list = get_classes()
    class_combo = ttk.Combobox(win, values=class_list, state="readonly")
    class_combo.pack(pady=5)
    canvas = tk.Label(win, width=640, height=360, bg="black")
    canvas.pack(pady=10)
    log_box = tk.Text(win, height=15, width=80)
    log_box.pack(pady=10)
    start_button = tk.Button(win, text="Start Attendance", bg="#4caf50", fg="white", state="disabled")
    start_button.pack(pady=10)
    video = cv2.VideoCapture(0)
    if not video.isOpened():
        log_box.insert(tk.END, "Camera could not be opened!\n")
        return win
    attendance_running = {'value': False}
    attendance_start_time = None
    selected_class = {'value': None}
    known_faces = []
    known_ids = []
    id_name_map = {}
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1,
                                      refine_landmarks=True, min_detection_confidence=0.5)
    HEAD_MOVE_THRESHOLD = 0.2
    liveness_tracking_time = 30
    required_visible_time = 2
    head_positions = []
    already_marked = set()
    visible_time = {}
    frame_for_attendance = {'frame': None}

    def load_known_faces(class_name):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM students WHERE class_name = ?", (class_name,))
        id_name_map = {str(row[0]): row[1] for row in cursor.fetchall()}
        known_faces = []
        known_ids = []
        for filename in os.listdir(ENCODING_DIR):
            if filename.endswith(".pkl"):
                student_id = os.path.splitext(filename)[0]
                if student_id in id_name_map:
                    path = os.path.join(ENCODING_DIR, filename)
                    with open(path, "rb") as f:
                        encoding = pickle.load(f)
                        known_faces.append(encoding)
                        known_ids.append(student_id)
        conn.close()
        return known_faces, known_ids, id_name_map

    def mark_all_absent(class_student_ids):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for student_id in class_student_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO attendance_logs (student_id, date, status)
                VALUES (?, ?, 'absent')
            """, (student_id, today))
        conn.commit()
        conn.close()

    def mark_present(student_id):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE attendance_logs SET status='here' WHERE student_id=? AND date=?
        """, (student_id, today))
        conn.commit()
        conn.close()

    def on_class_selected(event):
        selected_class['value'] = class_combo.get()
        start_button.config(state="normal")
        log_box.insert(tk.END, f"Selected class: {selected_class['value']}\n")
        nonlocal known_faces, known_ids, id_name_map
        known_faces, known_ids, id_name_map = load_known_faces(selected_class['value'])

    class_combo.bind("<<ComboboxSelected>>", on_class_selected)

    def update_camera_frame():
        ret, frame = video.read()
        if ret:
            frame_for_attendance['frame'] = frame.copy()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            canvas.imgtk = imgtk
            canvas.configure(image=imgtk)
        win.after(30, update_camera_frame)

    def update_attendance():
        nonlocal head_positions, attendance_start_time
        if not attendance_running['value']:
            win.after(200, update_attendance)
            return
        frame = frame_for_attendance['frame']
        if frame is None:
            win.after(200, update_attendance)
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations)
        results = face_mesh.process(rgb)
        now = time.time()
        if attendance_start_time is None:
            attendance_start_time = now
        time_elapsed = now - attendance_start_time
        if time_elapsed >= liveness_tracking_time:
            log_box.insert(tk.END, f"Attendance session ended after {liveness_tracking_time} seconds.\n")
            show_attendance_report()
            win.after(4000, win.destroy)
            video.release()
            reset_btn_color()
            return
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            distances = face_recognition.face_distance(known_faces, face_encoding)
            min_dist = np.min(distances) if len(distances) else 1.0
            idx = np.argmin(distances) if len(distances) else None
            label = "Unknown"
            student_id = None
            if idx is not None and min_dist < 0.5:
                student_id = known_ids[idx]
                head_movement = 0
                if results.multi_face_landmarks:
                    landmarks = results.multi_face_landmarks[0]
                    image_h, image_w, _ = rgb.shape
                    coords = [(int(p.x * image_w), int(p.y * image_h)) for p in landmarks.landmark]
                    nose_point = coords[1]
                    head_positions.append(nose_point)
                    if len(head_positions) > 10:
                        head_positions.pop(0)
                    if len(head_positions) >= 2:
                        x_positions = [p[0] for p in head_positions]
                        y_positions = [p[1] for p in head_positions]
                        head_movement = np.std(x_positions) + np.std(y_positions)
                if student_id not in visible_time:
                    visible_time[student_id] = 0
                if head_movement > HEAD_MOVE_THRESHOLD:
                    visible_time[student_id] += 0.2
                log_box.insert(tk.END, f"[{id_name_map.get(student_id, student_id)}] Score: {min_dist:.2f}, "
                                      f"Visible: {visible_time[student_id]:.1f}s, HeadMove: {head_movement:.2f}\n")
                log_box.see(tk.END)
                if (
                    visible_time[student_id] >= required_visible_time
                    and student_id not in already_marked
                ):
                    name = id_name_map.get(student_id, "")
                    log_box.insert(tk.END, f"{name} marked as PRESENT ({visible_time[student_id]:.1f} s visible)\n")
                    label = name
                    mark_present(student_id)
                    already_marked.add(student_id)
            else:
                pass
        win.after(200, update_attendance)

    def start_attendance():
        if not selected_class['value']:
            messagebox.showerror("Error", "Please select a class first.")
            return
        nonlocal known_faces, known_ids, id_name_map, already_marked, visible_time
        known_faces, known_ids, id_name_map = load_known_faces(selected_class['value'])
        if not known_faces:
            log_box.insert(tk.END, "No face data found for this class!\n")
            return
        already_marked.clear()
        visible_time.clear()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM students WHERE class_name = ?", (selected_class['value'],))
        class_student_ids = [str(row[0]) for row in cursor.fetchall()]
        conn.close()
        mark_all_absent(class_student_ids)
        attendance_running['value'] = True
        start_button.config(state="disabled")
        log_box.insert(tk.END, "Attendance started! Please show your face to the camera.\n")

    def show_attendance_report():
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT students.name, students.surname, attendance_logs.status
            FROM students
            LEFT JOIN attendance_logs ON students.id = attendance_logs.student_id AND attendance_logs.date = ?
            WHERE students.class_name = ?
            ORDER BY students.name, students.surname
        """, (today, selected_class['value']))
        rows = cursor.fetchall()
        conn.close()
        present_list = [f"{name} {surname}" for name, surname, status in rows if status == "here"]
        absent_list = [f"{name} {surname}" for name, surname, status in rows if status != "here"]
        log_box.insert(tk.END, "\n--- Attendance Report ---\n")
        log_box.insert(tk.END, f"Present:\n" + "\n".join(present_list) + "\n")
        log_box.insert(tk.END, f"Absent:\n" + "\n".join(absent_list) + "\n")
        log_box.see(tk.END)

    start_button.config(command=start_attendance)
    update_camera_frame()
    update_attendance()
    def on_close_attendance():
        video.release()
        win.destroy()
        reset_btn_color()
    win.protocol("WM_DELETE_WINDOW", on_close_attendance)
    return win

def open_history_gui(reset_btn_color):
    window = tk.Toplevel()
    window.title("Attendance History")
    window.geometry("500x500")
    frame = tk.Frame(window)
    frame.pack(pady=10, fill="x")
    tk.Label(frame, text="Select Date:").pack(pady=5)
    date_combo = ttk.Combobox(frame, values=get_all_dates(), state="readonly")
    date_combo.pack(pady=5)
    tk.Label(frame, text="Select Class:").pack(pady=5)
    class_combo = ttk.Combobox(frame, values=get_classes(), state="readonly")
    class_combo.pack(pady=5)
    result_text = tk.Text(window, height=20, width=60)
    result_text.pack(pady=10)

    def on_view():
        selected_date = date_combo.get()
        selected_class = class_combo.get()
        if not selected_date or not selected_class:
            messagebox.showerror("Error", "Lütfen hem tarih hem de sınıf seçin.")
            return

        query = """
            SELECT s.name || ' ' || s.surname AS name, a.status
            FROM students s
            LEFT JOIN attendance_logs a
                ON s.id = a.student_id AND a.date = ?
            WHERE s.class_name = ?
            ORDER BY s.name, s.surname
        """
        params = [selected_date, selected_class]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        rows = cursor.execute(query, params).fetchall()
        conn.close()

        result_text.delete("1.0", tk.END)
        if not rows:
            result_text.insert(tk.END, "No records found.")
        else:
            for row in rows:
                name, status = row
                status_str = "HERE" if status == "here" else "ABSENT"
                result_text.insert(tk.END, f"{name}: {status_str}\n")

    tk.Button(frame, text="Show Attendance", command=on_view, bg="#673ab7", fg="white").pack(pady=10)

    def on_close():
        window.destroy()
        reset_btn_color()
    window.protocol("WM_DELETE_WINDOW", on_close)
    return window

def open_students_panel(reset_btn_color):
    window = tk.Toplevel()
    window.title("All Students")
    window.geometry("650x500")
    window.configure(bg="white")
    tk.Label(window, text="Kayıtlı Öğrenciler", font=("Segoe UI", 18, "bold"), bg="white").pack(pady=12)
    cols = ("ID", "Adı", "Soyadı", "Numarası", "Sınıfı")
    tree = ttk.Treeview(window, columns=cols, show="headings", height=18)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, minwidth=0, width=120 if col != "ID" else 50, stretch=tk.NO)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, surname, student_number, class_name FROM students ORDER BY class_name, name, surname")
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)
    conn.close()
    tree.pack(fill="both", expand=True, padx=20, pady=5)

    def on_close():
        window.destroy()
        reset_btn_color()
    window.protocol("WM_DELETE_WINDOW", on_close)
    return window

def get_total_students():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM students")
    count = c.fetchone()
    conn.close()
    return count[0] if count and count[0] is not None else 0

def get_present_count():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM attendance_logs WHERE date=? AND status='here'", (today,))
    count = c.fetchone()
    conn.close()
    return count[0] if count and count[0] is not None else 0

def get_absent_count():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM attendance_logs WHERE date=? AND status='absent'", (today,))
    count = c.fetchone()
    conn.close()
    return count[0] if count and count[0] is not None else 0

def main_menu_window(teacher_name):
    root = tk.Tk()
    root.title(f"SmartAttend - Welcome {teacher_name}")
    root.geometry("1200x700")
    root.resizable(False, False)
    root.configure(bg="white")

    sidebar = tk.Frame(root, width=200, bg="#f6f6f6", height=700)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(0)

    try:
        img = Image.open(LOGO_PATH).resize((54, 54))
        photo = ImageTk.PhotoImage(img)
        logo_label = tk.Label(sidebar, image=photo, bg="#f6f6f6")
        logo_label.image = photo
        logo_label.pack(pady=(32, 10))
    except Exception:
        tk.Label(sidebar, text="SA", font=("Segoe UI", 24, "bold"), bg="#f6f6f6", fg="#3a3a3a").pack(pady=(36, 18))

    tk.Label(sidebar, text="SMARTATTEND", font=("Segoe UI", 16, "bold"), bg="#f6f6f6", fg="#262626").pack(pady=(0, 25))

    buttons = []
    active_btn = [None]
    total_label_var = tk.StringVar()
    present_label_var = tk.StringVar()
    absent_label_var = tk.StringVar()

    def update_stats():
        total_label_var.set(str(get_total_students()))
        present_label_var.set(str(get_present_count()))
        absent_label_var.set(str(get_absent_count()))

    def add_student_and_refresh(reset_btn_color):
        open_add_student()
        update_stats()
        return None

    def import_students_and_refresh(reset_btn_color):
        import_students_from_excel()
        update_stats()
        return None

    menu_items = [
        ("🙂  Face Registration", open_register_gui),
        ("➕  Add Student", add_student_and_refresh),
        ("📥  Import Students (Excel)", import_students_and_refresh),
        ("👨‍🎓  Students", open_students_panel),
        ("📅  Attendance", open_attendance_gui),
        ("🗓️  History", open_history_gui),
    ]

    def on_enter(e, btn):
        if active_btn[0] != btn:
            btn.configure(bg="#e6f0fa", fg="#005bb5")
    def on_leave(e, btn):
        if active_btn[0] != btn:
            btn.configure(bg="#f6f6f6", fg="#262626")

    def create_button(text, cmd):
        btn = tk.Button(
            sidebar,
            text=text,
            font=("Segoe UI", 13),
            bg="#f6f6f6", fg="#262626",
            activebackground="#e6f0fa", activeforeground="#005bb5",
            borderwidth=0, anchor="w", padx=30, height=2, cursor="hand2"
        )
        btn.pack(fill="x")

        def reset_btn_color():
            btn.configure(bg="#f6f6f6", fg="#262626")
            active_btn[0] = None

        def button_cmd_wrapper():
            root.focus_set()
            for b in buttons :
                b.configure(bg="#f6f6f6", fg="#262626")
            btn.configure(bg="#478aff", fg="white")
            active_btn[0] = btn
            panel = cmd(reset_btn_color)
            if panel is not None:
                try:
                    panel.protocol("WM_DELETE_WINDOW", lambda: [panel.destroy(), reset_btn_color()])
                except Exception:
                    pass
            update_stats()
        btn.configure(command=button_cmd_wrapper)
        btn.bind("<Enter>", lambda e, b=btn: on_enter(e, b))
        btn.bind("<Leave>", lambda e, b=btn: on_leave(e, b))
        buttons.append(btn)

    for text, cmd in menu_items:
        create_button(text, cmd)

    content = tk.Frame(root, bg="white")
    content.pack(side="left", fill="both", expand=True)
    content.pack_propagate(0)

    topbar = tk.Frame(content, bg="white", height=60)
    topbar.pack(side="top", fill="x")
    tk.Label(topbar, text="Dashboard", font=("Segoe UI", 18, "bold"), bg="white", fg="#222").pack(side="left", padx=28, pady=12)
    tk.Label(topbar, text=f"Teacher: {teacher_name}", font=("Segoe UI", 12), bg="white", fg="#777").pack(side="right", padx=38)

    dashboard_card = tk.Frame(content, bg="white", highlightbackground="#e4e4e4", highlightthickness=2)
    dashboard_card.place(relx=0.06, rely=0.17, relwidth=0.88, relheight=0.78)

    tk.Label(dashboard_card, text="Welcome to SmartAttend!", font=("Segoe UI", 27, "bold"), bg="white", fg="#101010").pack(pady=(28, 8))
    tk.Label(dashboard_card, text="Your secure, easy and stylish attendance system.", font=("Segoe UI", 14), bg="white", fg="#444").pack(pady=(0, 18))

    stats_frame = tk.Frame(dashboard_card, bg="white", width=700, height=160)
    stats_frame.pack(pady=(12, 0))

    def stat_card(title, icon, color, var):
        card = tk.Frame(stats_frame, bg="white", width=210, height=120, highlightbackground="#dedede", highlightthickness=1)
        card.grid_propagate(0)
        card.pack_propagate(1)
        tk.Label(card, text=icon, font=("Segoe UI", 38), bg="white", fg=color).pack(side="top", pady=(10, 0), expand=True)
        tk.Label(card, text=title, font=("Segoe UI", 15, "bold"), bg="white", fg="#111").pack(expand=True)
        tk.Label(card, textvariable=var, font=("Segoe UI", 26, "bold"), bg="white", fg=color).pack(pady=(4, 10), expand=True)
        return card

    cards = [
        ("Total Students", "👥", "#2196f3", total_label_var),
        ("Today Present", "✔️", "#4caf50", present_label_var),
        ("Today Absent", "❌", "#f44336", absent_label_var),
    ]
    for i, (title, icon, color, var) in enumerate(cards):
        card = stat_card(title, icon, color, var)
        card.grid(row=0, column=i, padx=32, pady=0, sticky="nsew")
        stats_frame.grid_columnconfigure(i, weight=1)

    update_stats()
    root.mainloop()

def open_main_selector():
    win = tk.Tk()
    win.title("SmartAttend")
    win.geometry("400x420")
    win.configure(bg="white")
    tk.Label(win, text="SmartAttend", font=("Segoe UI", 24, "bold"), bg="white").pack(pady=(45, 15))
    tk.Button(win, text="Öğretmen Girişi", font=("Segoe UI", 16), bg="#2196f3", fg="white", width=18,
              command=lambda: [win.destroy(), login_window()]).pack(pady=12)
    tk.Button(win, text="Öğrenci Girişi", font=("Segoe UI", 16), bg="#4caf50", fg="white", width=18,
              command=lambda: [win.destroy(), student_login_window()]).pack(pady=12)
    tk.Button(win, text="Her İki Paneli Aç (Test)", font=("Segoe UI", 13), bg="#673ab7", fg="white", width=22,
              command=lambda: [win.destroy(), run_teacher_and_student_parallel()]).pack(pady=24)
    win.mainloop()

def run_teacher_and_student_parallel():
    t1 = threading.Thread(target=login_window)
    t2 = threading.Thread(target=student_login_window)
    t1.start()
    t2.start()

def login_window():
    win = tk.Tk()
    win.title("SmartAttend Teacher Login")
    win.geometry("400x420")
    win.resizable(False, False)
    if os.path.exists(LOGO_PATH):
        img = Image.open(LOGO_PATH)
        img = img.resize((130, 130))
        photo = ImageTk.PhotoImage(img)
        logo_label = tk.Label(win, image=photo)
        logo_label.image = photo
        logo_label.pack(pady=8)
    else:
        tk.Label(win, text="SmartAttend", font=("Arial", 22, "bold")).pack(pady=12)

    tk.Label(win, text="Teacher Login", font=("Arial", 14)).pack(pady=8)
    tk.Label(win, text="Email:").pack()
    email_entry = tk.Entry(win)
    email_entry.pack()
    tk.Label(win, text="Password:").pack()
    password_entry = tk.Entry(win, show="*")
    password_entry.pack()

    def try_login():
        email = email_entry.get().strip()
        password = password_entry.get().strip()
        if not email or not password:
            messagebox.showerror("Error", "Please fill both fields.", parent=win)
            return
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, password_hash FROM teachers WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        if user and hash_password(password) == user[2]:
            win.destroy()
            main_menu_window(user[1])
        else:
            messagebox.showerror("Error", "Incorrect email or password.", parent=win)

    tk.Button(win, text="Login", width=18, command=try_login, bg="#2196f3", fg="white").pack(pady=12)
    tk.Button(win, text="Register New Teacher", width=18, command=lambda: register_teacher_window(win), bg="#4caf50", fg="white").pack(pady=2)
    win.mainloop()

if __name__ == "__main__":
    open_main_selector()
