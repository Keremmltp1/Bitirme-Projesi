import cv2
import face_recognition

def find_camera_index(max_index=5):
    # Try different camera indexes to find an available camera
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cap.release()
            return i
    return None

def main():
    cam_index = find_camera_index()
    if cam_index is None:
        print("No camera found.")
        return

    print(f"Using camera index {cam_index}.")
    video = cv2.VideoCapture(cam_index)

    while True:
        ret, frame = video.read()
        if not ret:
            break

        # Convert BGR to RGB for face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_frame)
        for top, right, bottom, left in face_locations:
            # Draw a rectangle around detected face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        cv2.imshow("SmartAttend Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
