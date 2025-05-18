import cv2
import face_recognition
import pickle
import os
import sqlite3
import time

# Paths for encodings and database
ENCODING_DIR = r"C:\Users\krem_\OneDrive\Desktop\Bitirme Projesi\encodings"
DB_PATH = r"C:\Users\krem_\OneDrive\Desktop\Bitirme Projesi\attendance.db"

def save_to_database(name):
    # Save new student name to database if not exists
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO students (name) VALUES (?)", (name,))
        conn.commit()
    except Exception as e:
        print("Database error:", e)
    conn.close()

def save_encoding(name, encoding):
    # Save face encoding as .pkl file and add to database
    os.makedirs(ENCODING_DIR, exist_ok=True)
    save_path = os.path.join(ENCODING_DIR, f"{name}.pkl")
    with open(save_path, 'wb') as f:
        pickle.dump(encoding, f)
    save_to_database(name)

def register_from_image(image_path, name):
    # Register face from an image file
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)

    if len(face_locations) != 1:
        print("Error: The image must contain exactly one face.")
        return

    encoding = face_recognition.face_encodings(image, face_locations)[0]
    save_encoding(name, encoding)
    print(f"{name} registered successfully (from image).")

def register_from_camera(name):
    # Register face from camera
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

        # Draw rectangles around detected faces
        for top, right, bottom, left in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Save encoding if one face is detected and not already saved
        if len(face_locations) == 1 and not encoding_saved:
            encoding = face_recognition.face_encodings(rgb, face_locations)[0]
            save_encoding(name, encoding)
            encoding_saved = True
            saved_frame = frame.copy()

        if encoding_saved:
            # Show animation for saving
            for _ in range(30):
                anim_frame = saved_frame.copy()
                cv2.putText(anim_frame, "SAVING...", (80, 240),
                            cv2.FONT_HERSHEY_DUPLEX, 1.4, (0, 0, 255), 4)
                cv2.imshow("Face Registration", anim_frame)
                cv2.waitKey(30)
            break
        else:
            cv2.putText(frame, "Look at the camera to detect your face...",
                        (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 255), 2)

        cv2.imshow("Face Registration", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Registration cancelled.")
            break

    cam.release()
    cv2.destroyAllWindows()

def main():
    print("Select face registration source:\n1) Camera\n2) Image file")
    choice = input("Choice (1/2): ").strip()

    name = input("Enter the student name: ").strip()
    if not name:
        print("No name entered, cancelled.")
        return

    if choice == "1":
        register_from_camera(name)
    elif choice == "2":
        image_path = input("Image file path: ").strip().strip('"')
        if not os.path.exists(image_path):
            print("File not found.")
            return
        register_from_image(image_path, name)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
