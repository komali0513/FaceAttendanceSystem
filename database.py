import sqlite3
import os

def init_db():
    if not os.path.exists('data'):
        os.makedirs('data')

    conn = sqlite3.connect('data/attendance.db')
    cursor = conn.cursor()
    
    # 1. Enable Foreign Key support in SQLite (required for Cascade)
    cursor.execute("PRAGMA foreign_keys = ON")

    # 2. Employee Table (Primary Table)
    cursor.execute('''CREATE TABLE IF NOT EXISTS employees 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
         name TEXT UNIQUE, 
         email TEXT UNIQUE, 
         phone TEXT UNIQUE, 
         designation TEXT, 
         encoding BLOB, 
         image BLOB)''')
    
    # 3. Attendance Table (Child Table)
    # References employees(name). If name is deleted in employees, it's deleted here too.
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
         name TEXT, 
         email TEXT, 
         designation TEXT, 
         date TEXT, 
         time_in TEXT, 
         time_out TEXT,
         FOREIGN KEY(name) REFERENCES employees(name) ON DELETE CASCADE)''')
    
    conn.commit()
    conn.close()
    print("Database Initialized with Cascading Delete support.")

if __name__ == "__main__":
    init_db()