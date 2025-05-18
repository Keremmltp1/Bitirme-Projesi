# SmartAttend - Face Recognition Attendance System

SmartAttend is an advanced, user-friendly classroom attendance automation system that uses face recognition and liveness detection to prevent spoofing and ensure secure check-ins.

## Features

- Fast and secure face recognition for attendance
- Advanced liveness detection: blink (eye aspect ratio), head movement, and RGB variance analysis
- Resistant to photo/video spoofing via phone or printed images
- Student registration, face registration, attendance, and history viewing – all via a simple GUI
- SQLite database backend
- Designed for use in real classroom environments

## Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/Keremmltp1/Bitirme-Projesi.git
    cd Bitirme-Projesi
    ```

2. **Install the required Python packages:**
    ```sh
    pip install -r requirements.txt
    ```

3. **Initialize the database:**
    ```sh
    python init_db.py
    ```

4. **Start the main GUI:**
    ```sh
    python smartattend_gui.py
    ```

> **Note:**  
> - The files `attendance.db` and the `encodings/` folder are ignored in version control for privacy and security.  
> - On a new setup, you need to register students and their face data before using attendance features.

## Author

- [Keremmltp1](https://github.com/Keremmltp1)

## License

MIT License
