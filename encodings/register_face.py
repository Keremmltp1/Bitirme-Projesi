import cv2
import face_recognition
import pickle
import os
import sqlite3

# Paths for encodings and database
ENCODING_DIR = r"C:\Users\krem_\OneDrive\Desktop\Bitirme Projesi\encodings"
DB_PATH = r"C:\Users\krem_\OneDrive\Desktop\Bitirme Projesi\attendance.db"

def get_student_by_id(student_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, surname FROM students WHERE id = ?", (student_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def save_encoding(student_id, encoding):
    os.makedirs(ENCODING_DIR, exist_ok=True)
    save_path = os.path.join(ENCODING_DIR, f"{student_id}.pkl")
    with open(save_path, 'wb') as f:
        pickle.dump(encoding, f)

def register_from_camera(student_id):
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cam.isOpened():
        print("Could not open camera.")
        return

    for _ in range(3): cam.read()

    encoding_saved = False
    saved_frame = None

    while True:
        ret, frame = cam.read()
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)

        for top, right, bottom, left in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        if len(face_locations) == 1 and not encoding_saved:
            encoding = face_recognition.face_encodings(rgb, face_locations)[0]
            save_encoding(student_id, encoding)
            encoding_saved = True
            saved_frame = frame.copy()

        if encoding_saved:
            for _ in range(30):
                anim_frame = saved_frame.copy()
                cv2.putText(anim_frame, "KAYDEDILIYOR...", (80, 240),
                            cv2.FONT_HERSHEY_DUPLEX, 1.4, (0, 0, 255), 4)
                cv2.imshow("Yüz Kaydı", anim_frame)
                cv2.waitKey(30)
            break
        else:
            cv2.putText(frame, "Kameraya bakın...", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 255), 2)

        cv2.imshow("Yüz Kaydı", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("İşlem iptal edildi.")
            break

    cam.release()
    cv2.destroyAllWindows()

def register_from_image(image_path, student_id):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)

    if len(face_locations) != 1:
        print("Fotoğrafta tam bir yüz olmalı.")
        return

    encoding = face_recognition.face_encodings(image, face_locations)[0]
    save_encoding(student_id, encoding)
    print(f"{student_id} için kayıt başarılı (fotoğraftan).")

def main():
    print("Kayıt türünü seçin:\n1) Kamera\n2) Fotoğraf dosyası")
    choice = input("Seçim (1/2): ").strip()

    student_id = input("Öğrenci ID girin: ").strip()
    if not student_id.isdigit():
        print("Geçersiz ID.")
        return

    if not get_student_by_id(student_id):
        print("Böyle bir öğrenci yok!")
        return

    if choice == "1":
        register_from_camera(student_id)
    elif choice == "2":
        image_path = input("Fotoğraf dosya yolu: ").strip().strip('"')
        if not os.path.exists(image_path):
            print("Dosya bulunamadı.")
            return
        register_from_image(image_path, student_id)
    else:
        print("Geçersiz seçim.")

if __name__ == "__main__":
    main()
