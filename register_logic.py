import cv2
import face_recognition
import sqlite3
import numpy as np
import os
from tkinter import messagebox

def register_user_gui(name, email, phone, desig):
    """
    Validates user data, checks for duplicates, and captures face encoding/image.
    Returns True if registration is successful, False otherwise.
    """
    
    # 1. Validation: Check if any fields are empty
    if not name.strip() or not email.strip() or not phone.strip() or not desig.strip():
        messagebox.showerror("Required Fields", "All fields (Name, Email, Phone, Designation) are required!")
        return False

    # 2. Database Validation: Check for duplicates
    conn = sqlite3.connect('data/attendance.db')
    cursor = conn.cursor()
    
    try:
        # Check if Name, Email, or Phone already exists
        cursor.execute("SELECT name, email, phone FROM employees WHERE name=? OR email=? OR phone=?", 
                       (name, email, phone))
        existing_user = cursor.fetchone()
        
        if existing_user:
            if existing_user[0].lower() == name.lower():
                messagebox.showerror("Duplicate Error", f"The name '{name}' is already registered.")
            elif existing_user[1].lower() == email.lower():
                messagebox.showerror("Duplicate Error", f"The email '{email}' is already in use.")
            else:
                messagebox.showerror("Duplicate Error", f"The phone number '{phone}' is already registered.")
            conn.close()
            return False
            
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
        conn.close()
        return False

    # 3. Start Camera for Face Capture
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        messagebox.showerror("Camera Error", "Could not access the webcam.")
        conn.close()
        return False

    messagebox.showinfo("Face Capture", "Data Validated!\n\n1. Look at the camera.\n2. Press 'S' to Capture & Save.\n3. Press 'Q' to Cancel.")

    registration_success = False

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Display UI feedback on the camera frame
        display_frame = frame.copy()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces for visual rectangle
        face_locations = face_recognition.face_locations(rgb_frame)
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(display_frame, "Face Detected", (left, top - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Enrollment - Press 'S' to Save", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        # Press 'S' to Save
        if key == ord('s'):
            if len(face_locations) > 0:
                # Generate face encoding (the 128D mathematical map)
                encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                if len(encodings) > 0:
                    encoding_blob = encodings[0].tobytes() # Convert numpy array to binary
                    
                    # Convert the frame to JPG format bytes (Profile Image)
                    success, buffer = cv2.imencode('.jpg', frame)
                    if success:
                        image_blob = buffer.tobytes()

                        try:
                            # Insert into Database
                            cursor.execute("""
                                INSERT INTO employees (name, email, phone, designation, encoding, image) 
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (name, email, phone, desig, encoding_blob, image_blob))
                            
                            conn.commit()
                            messagebox.showinfo("Success", f"Registration complete for {name}!")
                            registration_success = True
                            break
                        except sqlite3.IntegrityError:
                            messagebox.showerror("Error", "Database integrity error. Possible duplicate during save.")
                            break
                else:
                    messagebox.showwarning("Processing Error", "Could not process face. Please stay still and try again.")
            else:
                messagebox.showwarning("No Face", "No face detected in the frame. Please look at the camera.")

        # Press 'Q' to Quit
        elif key == ord('q'):
            print("Registration cancelled by user.")
            break

        # If window is closed manually
        if cv2.getWindowProperty("Enrollment - Press 'S' to Save", cv2.WND_PROP_VISIBLE) < 1:
            break

    # Cleanup
    cam.release()
    cv2.destroyAllWindows()
    conn.close()
    
    return registration_success