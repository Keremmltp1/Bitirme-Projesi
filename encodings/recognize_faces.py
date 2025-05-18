import cv2
import face_recognition
import pickle
import os
import sqlite3
import numpy as np
from datetime import datetime

# Paths for encodings and database
ENCODING_DIR = r"C:\Users\krem_\OneDrive\Desktop\Bitirme Projesi\encodings"
DB_PATH = r"C:\Users\krem_\OneDrive\Desktop\Bitirme Projesi\attendance.db"
THRESHOLD = 0.5  # Face recognition distance threshold

def warmup_camera(cam):
    # Capture a few frames to allow the camera to adjust
    for _ in range(3): cam.read()

def load_known_faces():
    # Load all known face encodings and names from .pkl files
    known_faces = []
    known_names = []
    for filename in os.listdir(ENCODING_DIR):
        if filename.endswith(".pkl"):
            path = os.path.join(ENCODING_DIR, filename)
            with open(path, "rb") as f:
                encoding = pickle.load(f)
                known_faces.append(encoding)
                known_names.append(os.path.splitext(filename)[0])
    return known_faces, known_names

def mark_all_absent(known_names):
    # Mark all students as 'absent' at the beginning
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for name in known_names:
        cursor.execute("SELECT id FROM students WHERE name = ?", (name,))
        result = cursor.fetchone()
        if result:
            student_id = result[0]
            cursor.execute("""
                INSERT OR IGNORE INTO attendance_logs (student_id, date, status)
                VALUES (?, ?, 'absent')
            """, (student_id, today))
    conn.commit()
    conn.close()

def save_attendance_to_db(name):
    # Update attendance status to 'here' for recognized student
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM students WHERE name = ?", (name,))
    result = cursor.fetchone()
    if result:
        student_id = result[0]
        cursor.execute("""
            UPDATE attendance_logs
            SET status = 'here'
            WHERE student_id = ? AND date = ?
        """, (student_id, today))
    conn.commit()
    conn.close()

def main():
    # Load known faces
    known_faces, known_names = load_known_faces()
    if not known_faces:
        print("No face data found.")
        return

    mark_all_absent(known_names)

    already_marked = set()
    video = cv2.VideoCapture(0)
    video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not video.isOpened():
        print("Could not open camera.")
        return

    warmup_camera(video)
    print("Recognition started. Press 'q' to exit.")

    while True:
        ret, frame = video.read()
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations)

        label_shown = False
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            distances = face_recognition.face_distance(known_faces, face_encoding)
            min_distance = np.min(distances)
            match_index = np.argmin(distances)

            if min_distance < THRESHOLD:
                name = known_names[match_index]
                if name not in already_marked:
                    save_attendance_to_db(name)
                    already_marked.add(name)
                label = f"{name} ({min_distance:.2f})"
            else:
                label = "Unknown"

            label_shown = True
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if not label_shown:
            cv2.putText(frame, "Searching for face...", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 255), 2)

        cv2.imshow("SmartAttend - Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
