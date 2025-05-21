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


BASE_PATH = r"C:\\Users\\krem_\\OneDrive\\Desktop\\Bitirme Projesi"
DB_PATH = os.path.join(BASE_PATH, "attendance.db")
ENCODING_DIR = os.path.join(BASE_PATH, "encodings")
LOGO_PATH = os.path.join(BASE_PATH, "logo.png")

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

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

def login_window():
    win = tk.Tk()
    win.title("SmartAttend Teacher Login")
    win.geometry("400x420")
    win.resizable(False, False)

    # Logo üstte
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
            main_menu_window(user[1])  # user[1]: teacher name
        else:
            messagebox.showerror("Error", "Incorrect email or password.", parent=win)

    tk.Button(win, text="Login", width=18, command=try_login, bg="#2196f3", fg="white").pack(pady=12)
    tk.Button(win, text="Register New Teacher", width=18, command=lambda: register_teacher_window(win), bg="#4caf50", fg="white").pack(pady=2)
    win.mainloop()

# --- ESKİ FONKSİYONLAR ve MENÜ ---
def open_add_student():
    os.system(f"python \"{os.path.join(BASE_PATH, 'add_student.py')}\"")

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

def open_register_gui():
    def start_camera():
        nonlocal cap, running
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            status_label.config(text="Camera could not be opened.", fg="red")
            return
        for _ in range(5):
            cap.read()
        running = True
        update_frame()

    def update_frame():
        nonlocal cap, running
        if not running or cap is None:
            return
        ret, frame = cap.read()
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            video_canvas.imgtk = imgtk
            video_canvas.image = imgtk
            video_canvas.configure(image=imgtk)
        video_canvas.after(30, update_frame)

    def capture_face():
        nonlocal cap
        selected = student_combo.get()
        student_id = student_ids.get(selected)
        if not student_id:
            status_label.config(text="No student selected.", fg="red")
            return
        ret, frame = cap.read()
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

    def on_close():
        nonlocal cap, running
        running = False
        if cap:
            cap.release()
        window.destroy()

    cap = None
    running = False
    window = tk.Toplevel()
    window.title("Face Registration")
    window.geometry("750x600")
    tk.Label(window, text="Select Class:").pack()
    class_combo = ttk.Combobox(window, state="readonly", values=get_classes())
    class_combo.pack()
    class_combo.bind("<<ComboboxSelected>>", on_class_selected)
    tk.Label(window, text="Select Student:").pack()
    student_combo = ttk.Combobox(window, state="readonly")
    student_combo.pack()
    student_ids = {}
    video_canvas = tk.Label(window, width=640, height=360, bg="black")
    video_canvas.pack(pady=10)
    tk.Button(window, text="Register by Camera", command=capture_face, bg="#4caf50", fg="white").pack(pady=5)
    tk.Button(window, text="Register by Photo", command=upload_photo, bg="#9c27b0", fg="white").pack(pady=5)
    status_label = tk.Label(window, text="")
    status_label.pack()
    window.protocol("WM_DELETE_WINDOW", on_close)
    start_camera()

def open_attendance_gui():
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
        return
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
    win.protocol("WM_DELETE_WINDOW", lambda: video.release())

def open_history_gui():
    def on_class_selected(event):
        selected_class = class_combo.get()
        students = get_students_by_class(selected_class)
        student_combo['values'] = [f"{s[0]} - {s[1]}" for s in students]
        student_combo.set("")

    def on_view():
        selected_date = date_combo.get()
        selected_class = class_combo.get()
        selected_student = student_combo.get()
        student_id = selected_student.split(" - ")[0] if selected_student else None

        query = """
            SELECT s.name || ' ' || s.surname AS name, s.class_name AS class, a.date AS date, a.status AS status
            FROM attendance_logs a
            JOIN students s ON s.id = a.student_id
            WHERE 1=1
        """
        params = []
        if selected_date:
            query += " AND a.date = ?"
            params.append(selected_date)
        if selected_class:
            query += " AND s.class_name = ?"
            params.append(selected_class)
        if student_id:
            query += " AND s.id = ?"
            params.append(student_id)
        query += " ORDER BY s.class_name, s.name"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        rows = cursor.execute(query, params).fetchall()
        conn.close()

        result_text.delete("1.0", tk.END)
        if not rows:
            result_text.insert(tk.END, "No records found.")
        else:
            for row in rows:
                name, class_name, date, status = row
                status_str = "PRESENT" if status == "here" else "ABSENT"
                result_text.insert(tk.END, f"{date} - {class_name} - {name}: {status_str}\n")

    window = tk.Toplevel()
    window.title("Attendance History")
    window.geometry("600x500")

    frame = tk.Frame(window)
    frame.pack(pady=10, fill="x")

    tk.Label(frame, text="Select Date:").pack(pady=5)
    date_combo = ttk.Combobox(frame, values=get_all_dates(), state="readonly")
    date_combo.pack(pady=5)

    tk.Label(frame, text="Select Class:").pack(pady=5)
    class_combo = ttk.Combobox(frame, values=get_classes(), state="readonly")
    class_combo.pack(pady=5)
    class_combo.bind("<<ComboboxSelected>>", on_class_selected)

    tk.Label(frame, text="Select Student:").pack(pady=5)
    student_combo = ttk.Combobox(frame, state="readonly")
    student_combo.pack(pady=5)

    tk.Button(frame, text="Show Attendance", command=on_view, bg="#673ab7", fg="white").pack(pady=10)

    result_text = tk.Text(window, height=15, width=70)
    result_text.pack(pady=10)



def main_menu_window(teacher_name):
    root = tb.Window(themename="darkly")
    root.title(f"SmartAttend - Welcome {teacher_name}")
    root.geometry("1920x1080")
    root.resizable(False, False)
    root.configure(bg="#191a22")

    # Sidebar - modern, siyah ve gölgeli
    sidebar = tk.Frame(root, bg="#21222c", width=92, bd=0, highlightthickness=0)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(0)
    # Shadow efekti için
    shadow = tk.Frame(root, bg="#22232b", width=8)
    shadow.place(x=92, y=0, relheight=1.0)

    # Logo üstte ufak
    try:
        img = Image.open(LOGO_PATH).resize((64, 64))
        photo = ImageTk.PhotoImage(img)
        logo_label = tk.Label(sidebar, image=photo, bg="#21222c")
        logo_label.image = photo
        logo_label.pack(pady=(36, 16))
    except Exception:
        tk.Label(sidebar, text="SA", font=("Segoe UI", 24, "bold"), bg="#21222c", fg="#00bcf0").pack(pady=(36, 16))

    # Navigation butonları (ikon+metin)
    menu_specs = [
        ("\u263A", "Face Registration", open_register_gui),
        ("\u2795", "Add Student", open_add_student),
        ("\U0001F4C5", "Attendance", open_attendance_gui),
        ("\U0001F5D3", "History", open_history_gui)
    ]
    for icon, text, cmd in menu_specs:
        btn = tk.Button(
            sidebar,
            text=f"{icon}\n{text}",
            font=("Segoe UI", 12, "bold"),
            bg="#23232e", fg="#e3e7ef", activebackground="#2e2e3a", activeforeground="#44d6ff",
            relief="flat", bd=0, cursor="hand2",
            command=cmd,
            justify="center",
            wraplength=90,
            padx=4, pady=12
        )
        btn.pack(pady=15, fill="x")

    # Ana içerik alanı (beyaz kart, yumuşak gölge)
    main_bg = tk.Frame(root, bg="#191a22")
    main_bg.pack(side="left", fill="both", expand=True)

    card = tk.Frame(main_bg, bg="#f8f9fa", bd=0, relief="flat", highlightbackground="#ededed", highlightthickness=2)
    card.place(relx=0.14, rely=0.10, relwidth=0.81, relheight=0.80)

    # Hoşgeldin
    tk.Label(card, text="Welcome to SmartAttend!", font=("Segoe UI", 28, "bold"), fg="#23232e", bg="#f8f9fa").pack(pady=(38,10))
    tk.Label(card, text="Manage attendance easily and securely.", font=("Segoe UI", 15), fg="#4d515a", bg="#f8f9fa").pack(pady=(0,24))



    # Alt imza
    tk.Label(card, text="Keremmltp1 © 2025", font=("Segoe UI", 10), fg="#aaaaaa", bg="#f8f9fa").pack(side="bottom", pady=(0,12))

    root.mainloop()



if __name__ == "__main__":
    login_window()