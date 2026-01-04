import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from tkcalendar import DateEntry
import cv2
import face_recognition
import sqlite3
import numpy as np
import os
import time
from datetime import datetime
from PIL import Image, ImageTk

# Import registration logic
from register_logic import register_user_gui

# --- THEME COLORS (Light Mode, Dark Mode) ---
BG_COLOR = ("#F4F7F6", "#1A1A1A")      # Main background
SIDEBAR_COLOR = ("#EBEBEB", "#111111") # Sidebar background
CARD_COLOR = ("#FFFFFF", "#252525")    # Cards and Form boxes
TEXT_COLOR = ("#000000", "#FFFFFF")    # General text
ACCENT_COLOR = "#3498db"               # Blue accent stays blue

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VisionGuardPro(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VisionGuard AI | Professional Attendance System")
        self.geometry("1280x800")
        
        # Set window background using the tuple
        self.configure(fg_color=BG_COLOR)

        self.known_names = []
        self.known_encs = []
        self.cap = None
        self.is_monitoring = False
        self.tracking = {}      
        self.cooldowns = {}     
        
        self.total_lbl = None
        self.present_lbl = None

        self.load_faces()
        self.setup_gui()
        self.show_dashboard()

    def load_faces(self):
        try:
            conn = sqlite3.connect('data/attendance.db')
            cur = conn.cursor()
            cur.execute("SELECT name, encoding FROM employees")
            rows = cur.fetchall()
            self.known_names = [r[0] for r in rows]
            self.known_encs = [np.frombuffer(r[1], dtype=np.float64) for r in rows]
            conn.close()
        except Exception as e:
            print(f"Database error: {e}")

    def setup_gui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. SIDEBAR (Uses dynamic tuple)
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=SIDEBAR_COLOR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) 

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="VisionGuard AI", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 40))

        self.dash_btn = ctk.CTkButton(self.sidebar_frame, text="📊 Dashboard", command=self.show_dashboard, height=45)
        self.dash_btn.grid(row=1, column=0, padx=20, pady=10)

        self.reg_btn = ctk.CTkButton(self.sidebar_frame, text="👤 Registration", command=self.show_registration, height=45)
        self.reg_btn.grid(row=2, column=0, padx=20, pady=10)

        self.logs_btn = ctk.CTkButton(self.sidebar_frame, text="📋 History Logs", command=self.show_logs, height=45)
        self.logs_btn.grid(row=3, column=0, padx=20, pady=10)

        self.manage_btn = ctk.CTkButton(self.sidebar_frame, text="⚙️ Manage Staff", command=self.show_manage_staff, height=45)
        self.manage_btn.grid(row=4, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light"], command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=7, column=0, padx=20, pady=(10, 20))

        # 2. MAIN CONTENT AREA (Uses dynamic tuple)
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_COLOR)
        self.main_container.grid(row=0, column=1, sticky="nsew")

    def change_appearance_mode_event(self, mode):
        ctk.set_appearance_mode(mode)
        # Standard Tkinter Treeview doesn't update automatically, so we refresh the logs view if it's active
        if hasattr(self, 'tree'):
            self.show_logs() 

    def clear_main_area(self):
        self.is_monitoring = False
        if self.cap:
            self.cap.release()
            self.cap = None
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_area()
        self.is_monitoring = True

        stats_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(20, 20), padx=20)

        total, present = self.get_daily_stats()
        self.create_stat_card(stats_frame, "Total Staff", str(total), 0)
        self.create_stat_card(stats_frame, "Present Today", str(present), 1)

        cam_frame = ctk.CTkFrame(self.main_container, border_width=2, border_color=ACCENT_COLOR, fg_color="black")
        cam_frame.pack(expand=True, fill="both", padx=40, pady=(0, 40))

        self.cam_label = tk.Label(cam_frame, bg="black")
        self.cam_label.pack(expand=True, fill="both", padx=5, pady=5)

        self.cap = cv2.VideoCapture(0)
        self.update_camera()

    def create_stat_card(self, parent, title, value, col):
        # Card background switches between White (Light) and Dark Gray (Dark)
        card = ctk.CTkFrame(parent, width=250, height=110, fg_color=CARD_COLOR)
        card.grid(row=0, column=col, padx=15)
        card.grid_propagate(False)
        
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14)).pack(pady=(20, 0))
        lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=32, weight="bold"), text_color=ACCENT_COLOR)
        lbl.pack(pady=(0, 20))
        
        if "Total" in title: self.total_lbl = lbl
        else: self.present_lbl = lbl
        return card

    def get_daily_stats(self):
        conn = sqlite3.connect('data/attendance.db')
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM employees")
        total = cur.fetchone()[0]
        today = datetime.now().strftime('%Y-%m-%d')
        cur.execute("SELECT COUNT(DISTINCT name) FROM attendance WHERE date=?", (today,))
        present = cur.fetchone()[0]
        conn.close()
        return total, present

    def refresh_stats_ui(self):
        total, present = self.get_daily_stats()
        if self.total_lbl and self.total_lbl.winfo_exists():
            self.total_lbl.configure(text=str(total))
        if self.present_lbl and self.present_lbl.winfo_exists():
            self.present_lbl.configure(text=str(present))

    def update_camera(self):
        if not self.is_monitoring or not self.cap: return
        ret, frame = self.cap.read()
        if ret:
            h, w, _ = frame.shape
            display = frame.copy()
            zw, zh = 180, 180
            cx, cy = w // 2, h // 2
            zone = (cx - zw//2, cy - zh//2, cx + zw//2, cy + zh//2)
            cv2.rectangle(display, (zone[0], zone[1]), (zone[2], zone[3]), (255, 255, 255), 1)

            small = np.ascontiguousarray(cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (0,0), fx=0.25, fy=0.25), dtype=np.uint8)
            locs = face_recognition.face_locations(small)
            encs = face_recognition.face_encodings(small, locs)

            current_names = []
            now_ts = time.time()

            for (top, right, bottom, left), enc in zip(locs, encs):
                matches = face_recognition.compare_faces(self.known_encs, enc)
                if True in matches:
                    name = self.known_names[matches.index(True)]
                    current_names.append(name)

                    if name in self.cooldowns:
                        if now_ts - self.cooldowns[name] < 60:
                            cv2.putText(display, f"{name} (Cooldown)", (left*4, top*4-10), 1, 1, (255, 165, 0), 2)
                            continue
                        else: del self.cooldowns[name]

                    self.db_action(name, "check_in")
                    t, r, b, l = top*4, right*4, bottom*4, left*4
                    fx, fy = (l+r)//2, (t+b)//2
                    if (zone[0] < fx < zone[2] and zone[1] < fy < zone[3]):
                        cv2.rectangle(display, (zone[0], zone[1]), (zone[2], zone[3]), (0, 255, 0), 3)
                        if name not in self.tracking: self.tracking[name] = now_ts
                        else:
                            if now_ts - self.tracking[name] >= 2:
                                self.db_action(name, "check_out")
                                self.cooldowns[name] = now_ts 
                                if name in self.tracking: del self.tracking[name]
                                cv2.putText(display, "LOGOUT SUCCESS", (cx-100, cy), 1, 1.5, (0, 255, 0), 2)
                    else:
                        if name in self.tracking: del self.tracking[name]
                    cv2.rectangle(display, (l, t), (r, b), (0, 255, 0), 2)
                    cv2.putText(display, name, (l, t-10), 1, 1, (0, 255, 0), 2)

            img = Image.fromarray(cv2.cvtColor(display, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            self.cam_label.imgtk = imgtk
            self.cam_label.configure(image=imgtk)
        self.after(15, self.update_camera)

    def db_action(self, name, action):
        conn = sqlite3.connect('data/attendance.db')
        cur = conn.cursor()
        date, now = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%H:%M:%S')
        cur.execute("SELECT email, designation FROM employees WHERE name=?", (name,))
        row = cur.fetchone()
        updated = False
        if row:
            cur.execute("SELECT id, time_out FROM attendance WHERE name=? AND date=? ORDER BY id DESC LIMIT 1", (name, date))
            last = cur.fetchone()
            if action == "check_in" and (not last or last[1]):
                cur.execute("INSERT INTO attendance (name, email, designation, date, time_in) VALUES (?,?,?,?,?)", (name, row[0], row[1], date, now))
                updated = True
            elif action == "check_out" and last and not last[1]:
                cur.execute("UPDATE attendance SET time_out=? WHERE id=?", (now, last[0]))
                updated = True
        conn.commit()
        conn.close()
        if updated: self.refresh_stats_ui()

    def show_registration(self):
        self.clear_main_area()
        # Enrollment box switches color based on mode
        form_frame = ctk.CTkFrame(self.main_container, width=500, corner_radius=15, fg_color=CARD_COLOR)
        form_frame.pack(pady=60, padx=40)
        ctk.CTkLabel(form_frame, text="Enroll Employee", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=30)
        self.reg_entries = []
        for l in ["Full Name", "Email", "Phone", "Designation"]:
            e = ctk.CTkEntry(form_frame, placeholder_text=l, width=350, height=45)
            e.pack(pady=12, padx=60)
            self.reg_entries.append(e)
        ctk.CTkButton(form_frame, text="Start Capture", command=self.do_registration, width=250, height=50, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=40)

    def do_registration(self):
        data = [e.get() for e in self.reg_entries]
        if register_user_gui(*data):
            for entry in self.reg_entries: entry.delete(0, tk.END)
            self.reg_entries[0].focus()
            self.load_faces()

    def show_logs(self):
        self.clear_main_area()
        filter_frame = ctk.CTkFrame(self.main_container, fg_color=CARD_COLOR)
        filter_frame.pack(fill="x", pady=(0, 20), padx=20)
        ctk.CTkLabel(filter_frame, text="Select Date:").grid(row=0, column=0, padx=15, pady=15)
        self.date_picker = DateEntry(filter_frame, width=15, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_picker.grid(row=0, column=1, padx=10)
        ctk.CTkButton(filter_frame, text="Filter Report", width=120, command=self.load_filtered_logs).grid(row=0, column=2, padx=20)
        ctk.CTkButton(filter_frame, text="Clear", width=100, fg_color="gray", command=self.load_filtered_logs_all).grid(row=0, column=3)

        # Update Treeview colors based on theme
        bg_tree = "#FFFFFF" if ctk.get_appearance_mode() == "Light" else "#2b2b2b"
        fg_tree = "#000000" if ctk.get_appearance_mode() == "Light" else "white"

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=bg_tree, foreground=fg_tree, fieldbackground=bg_tree, rowheight=35)
        style.map("Treeview", background=[('selected', '#3498db')])
        
        self.tree = ttk.Treeview(self.main_container, columns=("N", "E", "D", "Dt", "I", "O"), show="headings")
        for col, h in zip(self.tree["columns"], ["Name", "Email", "Designation", "Date", "In", "Out"]):
            self.tree.heading(col, text=h)
            self.tree.column(col, anchor="center", width=150)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.load_filtered_logs_all()

    def load_filtered_logs(self):
        self.refresh_tree("SELECT name, email, designation, date, time_in, time_out FROM attendance WHERE date=?", (self.date_picker.get(),))

    def load_filtered_logs_all(self):
        self.refresh_tree("SELECT name, email, designation, date, time_in, time_out FROM attendance ORDER BY date DESC, time_in DESC")

    def refresh_tree(self, query, params=()):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect('data/attendance.db')
        cur = conn.cursor()
        cur.execute(query, params)
        for row in cur.fetchall(): self.tree.insert("", "end", values=row)
        conn.close()

    def show_manage_staff(self):
        self.clear_main_area()
        ctk.CTkLabel(self.main_container, text="Employee Management", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)
        content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Update Treeview colors based on theme
        bg_tree = "#FFFFFF" if ctk.get_appearance_mode() == "Light" else "#2b2b2b"
        fg_tree = "#000000" if ctk.get_appearance_mode() == "Light" else "white"

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=bg_tree, foreground=fg_tree, fieldbackground=bg_tree, rowheight=35)

        self.emp_tree = ttk.Treeview(content_frame, columns=("ID", "N", "E", "P", "D"), show="headings")
        for col, h in zip(self.emp_tree["columns"], ["ID", "Name", "Email", "Phone", "Designation"]):
            self.emp_tree.heading(col, text=h); self.emp_tree.column(col, width=100, anchor="center")
        self.emp_tree.pack(fill="both", expand=True, side="left")
        
        action_frame = ctk.CTkFrame(content_frame, width=180, fg_color=CARD_COLOR)
        action_frame.pack(side="right", fill="y", padx=15)
        ctk.CTkButton(action_frame, text="Delete Selected", fg_color="#e74c3c", hover_color="#c0392b", command=self.delete_employee).pack(pady=30, padx=15)
        self.load_all_employees()

    def load_all_employees(self):
        for i in self.emp_tree.get_children(): self.emp_tree.delete(i)
        conn = sqlite3.connect('data/attendance.db')
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, phone, designation FROM employees")
        for row in cur.fetchall(): self.emp_tree.insert("", "end", values=row)
        conn.close()

    def delete_employee(self):
        selected = self.emp_tree.selection()
        if not selected: return
        emp_name = self.emp_tree.item(selected[0])['values'][1]
        if messagebox.askyesno("Confirm", f"Delete {emp_name}?"):
            conn = sqlite3.connect('data/attendance.db')
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_keys = ON")
            cur.execute("DELETE FROM employees WHERE name=?", (emp_name,))
            conn.commit(); conn.close()
            self.load_all_employees(); self.load_faces(); self.refresh_stats_ui()

if __name__ == "__main__":
    if not os.path.exists('data'): os.makedirs('data')
    app = VisionGuardPro()
    app.mainloop()