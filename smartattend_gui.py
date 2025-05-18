import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import sqlite3
import cv2
import face_recognition
import pickle
from PIL import Image, ImageTk
import numpy as np
import datetime
import mediapipe as mp
import time
from tkcalendar import DateEntry

BASE_PATH = r"C:\\Users\\krem_\\OneDrive\\Desktop\\Bitirme Projesi"
DB_PATH = os.path.join(BASE_PATH, "attendance.db")
ENCODING_DIR = os.path.join(BASE_PATH, "encodings")

cap = None
running = False

def open_add_student():
    os.system("python \"C:\\Users\\krem_\\OneDrive\\Desktop\\Bitirme Projesi\\add_student.py\"")

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

def save_encoding(student_id, encoding):
    os.makedirs(ENCODING_DIR, exist_ok=True)
    save_path = os.path.join(ENCODING_DIR, f"{student_id}.pkl")
    with open(save_path, 'wb') as f:
        pickle.dump(encoding, f)

def open_register_gui():
    def start_camera():
        global cap, running
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            status_label.config(text="Kamera açılamadı.", fg="red")
            return
        for _ in range(5):
            cap.read()
        running = True
        update_frame()

    def update_frame():
        global cap, running
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
        global cap
        selected = student_combo.get()
        student_id = student_ids.get(selected)
        if not student_id:
            status_label.config(text="Öğrenci seçilmedi.", fg="red")
            return
        ret, frame = cap.read()
        if not ret:
            status_label.config(text="Kamera görüntüsü alınamadı.", fg="red")
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb)
        if len(faces) != 1:
            status_label.config(text="Lütfen yalnızca 1 yüz gösterin.", fg="orange")
            return
        encoding = face_recognition.face_encodings(rgb, faces)[0]
        save_encoding(student_id, encoding)
        status_label.config(text="Kayıt başarılı.", fg="green")

    def upload_photo():
        selected = student_combo.get()
        student_id = student_ids.get(selected)
        if not student_id:
            status_label.config(text="Öğrenci seçilmedi.", fg="red")
            return
        file_path = filedialog.askopenfilename(filetypes=[("Görseller", "*.jpg *.jpeg *.png")])
        if not file_path:
            return
        image = face_recognition.load_image_file(file_path)
        face_locations = face_recognition.face_locations(image)
        if len(face_locations) != 1:
            status_label.config(text="Görselde tam olarak bir yüz olmalı!", fg="orange")
            return
        encoding = face_recognition.face_encodings(image, face_locations)[0]
        save_encoding(student_id, encoding)
        status_label.config(text="Kayıt başarılı (fotoğraf).", fg="green")

    def on_class_selected(event):
        selected_class = class_combo.get()
        students = get_students_by_class(selected_class)
        student_combo['values'] = [s[1] for s in students]
        student_ids.clear()
        for sid, label in students:
            student_ids[label] = sid
        student_combo.set("")

    def on_close():
        global cap, running
        running = False
        if cap:
            cap.release()
        window.destroy()

    window = tk.Toplevel()
    window.title("Yüz Kaydı")
    window.geometry("750x600")

    tk.Label(window, text="Sınıf Seçin:").pack()
    class_combo = ttk.Combobox(window, state="readonly", values=get_classes())
    class_combo.pack()
    class_combo.bind("<<ComboboxSelected>>", on_class_selected)

    tk.Label(window, text="Öğrenci Seçin:").pack()
    student_combo = ttk.Combobox(window, state="readonly")
    student_combo.pack()
    student_ids = {}

    video_canvas = tk.Label(window, width=640, height=360, bg="black")
    video_canvas.pack(pady=10)

    tk.Button(window, text="Kamerayla Kaydet", command=capture_face, bg="#4caf50", fg="white").pack(pady=5)
    tk.Button(window, text="Fotoğrafla Kaydet", command=upload_photo, bg="#9c27b0", fg="white").pack(pady=5)

    status_label = tk.Label(window, text="")
    status_label.pack()

    window.protocol("WM_DELETE_WINDOW", on_close)
    start_camera()

def eye_aspect_ratio(landmarks, eye_indices):
    a = np.linalg.norm(np.array(landmarks[eye_indices[1]]) - np.array(landmarks[eye_indices[5]]))
    b = np.linalg.norm(np.array(landmarks[eye_indices[2]]) - np.array(landmarks[eye_indices[4]]))
    c = np.linalg.norm(np.array(landmarks[eye_indices[0]]) - np.array(landmarks[eye_indices[3]]))
    return (a + b) / (2.0 * c)

def open_attendance_gui():
    def load_known_faces():
        known_faces = []
        known_ids = []
        for filename in os.listdir(ENCODING_DIR):
            if filename.endswith(".pkl"):
                path = os.path.join(ENCODING_DIR, filename)
                with open(path, "rb") as f:
                    encoding = pickle.load(f)
                    known_faces.append(encoding)
                    known_ids.append(os.path.splitext(filename)[0])
        return known_faces, known_ids

    def mark_all_absent(known_ids):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for student_id in known_ids:
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
    win.title("Yoklama Tanıma")
    win.geometry("1920x1080")

    canvas = tk.Label(win, width=640, height=360, bg="black")
    canvas.pack(pady=10)

    log_box = tk.Text(win, height=15, width=80)
    log_box.pack(pady=10)

    known_faces, known_ids = load_known_faces()
    if not known_faces:
        log_box.insert(tk.END, "Hiç yüz verisi yok!\n")
        return

    video = cv2.VideoCapture(0)
    if not video.isOpened():
        log_box.insert(tk.END, "Kamera açılamadı!\n")
        return

    for _ in range(5):
        video.read()

    mark_all_absent(known_ids)
    already_marked = set()

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1,
                                      refine_landmarks=True, min_detection_confidence=0.5)
    EAR_THRESH = 0.2
    BLINK_CONSEC_FRAMES = 2
    HEAD_MOVE_THRESHOLD = 3.0
    RGB_VARIANCE_THRESHOLD = 3.5

    liveness_tracking_time = 30         # saniye
    required_liveness_time = 15         # saniye
    REQUIRED_LIVENESS_DURATION = 2.5    # arka arkaya canlılık için min süre (şart değil ama dursun)
    
    blink_counter = 0
    head_positions = []
    rgb_means = []
    liveness_start_time = None

    attendance_start_time = None
    liveness_active_time = {}  # student_id: aktif canlılık toplam süresi (saniye)
    liveness_this_frame = {}   # student_id: bu frame canlı mı

    def update():
        nonlocal blink_counter, head_positions, liveness_start_time, rgb_means, attendance_start_time
        ret, frame = video.read()
        if not ret or frame is None:
            win.after(1, update)
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
            log_box.insert(tk.END, f"Yoklama süresi ({liveness_tracking_time}s) doldu.\n")
            win.after(2000, win.destroy)
            video.release()
            return

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            image_h, image_w, _ = rgb.shape
            coords = [(int(p.x * image_w), int(p.y * image_h)) for p in landmarks.landmark]

            left_eye_idx = [362, 385, 387, 263, 373, 380]
            right_eye_idx = [33, 160, 158, 133, 153, 144]

            left_ear = eye_aspect_ratio(coords, left_eye_idx)
            right_ear = eye_aspect_ratio(coords, right_eye_idx)
            avg_ear = (left_ear + right_ear) / 2.0

            if avg_ear < EAR_THRESH:
                blink_counter += 1
            else:
                blink_counter = 0

            nose_point = coords[1]
            head_positions.append(nose_point)
            if len(head_positions) > 5:
                head_positions.pop(0)

        # --- RGB varyansı (canlılık kontrolü)
        if len(face_locations) == 1:
            (top, right, bottom, left) = face_locations[0]
            face_region = rgb[top:bottom, left:right]
            if face_region.size > 0:
                mean_rgb = np.mean(face_region, axis=(0, 1))
                rgb_means.append(mean_rgb)
                if len(rgb_means) > 20:
                    rgb_means.pop(0)
                rgb_means_arr = np.array(rgb_means)
                rgb_variance = np.mean(np.var(rgb_means_arr, axis=0))
            else:
                rgb_variance = 0
        else:
            rgb_variance = 0

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            distances = face_recognition.face_distance(known_faces, face_encoding)
            min_dist = np.min(distances)
            idx = np.argmin(distances)
            label = "Bilinmeyen"
            student_id = None

            if min_dist < 0.5:
                student_id = known_ids[idx]
                if student_id not in liveness_active_time:
                    liveness_active_time[student_id] = 0
                    liveness_this_frame[student_id] = False

                head_movement = 0
                if len(head_positions) >= 2:
                    x_positions = [p[0] for p in head_positions]
                    y_positions = [p[1] for p in head_positions]
                    head_movement = np.std(x_positions) + np.std(y_positions)

                status_text = f"Blink: {blink_counter} | Head Move: {head_movement:.2f} | RGB Var: {rgb_variance:.2f}\n"
                log_box.delete("1.0", "2.0")
                log_box.insert("1.0", status_text)

                # Bu frame'de canlılık şartı sağlanıyorsa, süreyi artır
                if (
                    blink_counter >= BLINK_CONSEC_FRAMES
                    and head_movement > HEAD_MOVE_THRESHOLD
                    and rgb_variance > RGB_VARIANCE_THRESHOLD
                ):
                    if not liveness_this_frame[student_id]:
                        liveness_this_frame[student_id] = True
                        liveness_active_time[student_id] += 0.2  # her güncellemede 0.2 saniye kabul
                else:
                    liveness_this_frame[student_id] = False

                # Canlılık aktif süresi 15 saniyeyi geçtiyse 'var' yaz!
                if (
                    liveness_active_time[student_id] >= required_liveness_time
                    and student_id not in already_marked
                ):
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name, surname FROM students WHERE id=?", (student_id,))
                    row = cursor.fetchone()
                    conn.close()
                    if row:
                        fullname = f"{row[0]} {row[1]}"
                        log_box.insert(tk.END, f"{fullname} yoklamaya KATILDI. ({liveness_active_time[student_id]:.1f} sn aktif canlılık)\n")
                        label = fullname
                    mark_present(student_id)
                    already_marked.add(student_id)
                    # Dilersen ekrana '✓' ikonu da koyabilirsin
            else:
                rgb_variance = 0

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Kalan süreyi göster
        sure_kaldi = max(0, int(liveness_tracking_time - time_elapsed))
        canvas_txt = f"Kalan Süre: {sure_kaldi}s"
        cv2.putText(frame, canvas_txt, (10, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 50, 50), 3)

        img = Image.fromarray(rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.imgtk = imgtk
        canvas.configure(image=imgtk)
        win.after(200, update)  # 0.2 saniye = 200 ms

    update()
    win.protocol("WM_DELETE_WINDOW", lambda: video.release())


def open_history_gui():
    def on_class_selected(event):
        selected_class = class_combo.get()
        students = get_students_by_class(selected_class)
        student_combo['values'] = [f"{s[0]} - {s[1]}" for s in students]
        student_combo.set("")

    def on_view():
        selected_date = date_entry.get()
        selected_class = class_combo.get()
        selected_student = student_combo.get()
        student_id = selected_student.split(" - ")[0] if selected_student else None

        query = """
            SELECT s.name || ' ' || s.surname AS isim, s.class_name AS sinif, a.date AS tarih, a.status AS durum
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
            result_text.insert(tk.END, "Kayıt bulunamadı.")
        else:
            for row in rows:
                isim, sinif, tarih, durum = row
                durum_tr = "VAR" if durum == "here" else "YOK"
                result_text.insert(tk.END, f"{tarih} - {sinif} - {isim}: {durum_tr}\n")

    window = tk.Toplevel()
    window.title("Yoklama Geçmişi")
    window.geometry("600x500")

    tk.Label(window, text="Tarih Seçin:").pack(pady=5)
    date_entry = DateEntry(window, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern="yyyy-mm-dd")
    date_entry.pack(pady=5)

    tk.Label(window, text="Sınıf Seçin:").pack(pady=5)
    class_combo = ttk.Combobox(window, values=get_classes(), state="readonly")
    class_combo.pack(pady=5)
    class_combo.bind("<<ComboboxSelected>>", on_class_selected)

    tk.Label(window, text="Öğrenci Seçin:").pack(pady=5)
    student_combo = ttk.Combobox(window, state="readonly")
    student_combo.pack(pady=5)

    tk.Button(window, text="Yoklamayı Göster", command=on_view, bg="#673ab7", fg="white").pack(pady=10)

    result_text = tk.Text(window, height=15, width=70)
    result_text.pack(pady=10)

def main():
    root = tk.Tk()
    root.title("SmartAttend - Yüz Tanıma Sistemi")
    root.geometry("400x400")

    tk.Button(root, text="Yüz Kaydı", command=open_register_gui, width=30, height=2, bg="#4caf50", fg="white").pack(pady=20)
    tk.Button(root, text="Yeni Öğrenci Ekle", command=open_add_student, width=30, height=2, bg="#2196f3", fg="white").pack(pady=10)
    tk.Button(root, text="Yoklama Al", command=open_attendance_gui, width=30, height=2, bg="#f44336", fg="white").pack(pady=10)
    tk.Button(root, text="Yoklama Geçmişi", command=open_history_gui, width=30, height=2, bg="#ff9800", fg="white").pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
