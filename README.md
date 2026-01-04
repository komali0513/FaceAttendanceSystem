VisionGuard AI | Professional Face Recognition Attendance System
VisionGuard AI is a high-performance, contactless attendance management system built using Python. It leverages Deep Learning for face recognition to automate the process of recording "Time In" and "Time Out" for employees. The system features a modern, professional dashboard with real-time monitoring and advanced data management.

Key Features:
Automated Attendance:
Check-in: Immediate "Time In" recording as soon as a registered face is detected anywhere in the camera feed.
Centered Check-out: "Time Out" is recorded only when the user aligns their face in the center of the screen for 2 consecutive seconds.
Smart Cooldown Mechanism: Prevents accidental duplicate logs by implementing a 60-second cooldown period after a successful logout.
Modern Professional GUI: Built with CustomTkinter, offering a sleek "Glassmorphism" design with seamless Dark and Light mode switching.
Embedded Live Feed: The camera feed is integrated directly into the dashboard for a native app experience.
Comprehensive Database Management:
Stores mathematical face encodings (128D vectors) for speed and raw JPG images for records.
Unique Constraints: Prevents duplicate registrations of Names, Emails, or Phone numbers.
Staff Management: Dedicated tab to view registered staff and delete employees (using SQL Cascading Deletes to wipe associated history).
Advanced Reporting: Attendance logs can be filtered by specific dates using an integrated calendar widget.

Tech Stack:
Language: Python 3.12+
Face Recognition: face_recognition (dlib-based)
Computer Vision: OpenCV
GUI Framework: CustomTkinter, Tkinter
Database: SQLite3
Image Processing: Pillow (PIL)

How to Use:
Enrollment:
Navigate to the Registration tab.
Enter Name, Email, Phone, and Designation (All fields are required and must be unique).
Press Start Capture, look at the camera, and press 'S' to save.
Marking Attendance:
Go to the Dashboard. The camera starts automatically.
Check-in: Simply appear in the camera's view.
Check-out: Align your face within the white box in the center of the screen. Hold still for 2 seconds until the "LOGOUT SUCCESSFUL" banner appears.
Viewing Reports:
Go to History Logs.
Use the calendar to select a date and click Apply Filter to generate a daily attendance report.
Managing Staff:
Use the Manage Staff tab to view all registered employees and delete profiles of individuals who have left the company.

