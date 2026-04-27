import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import Calendar
import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from linkedin_bot import post_linkedin

# =====================================================
# APP CONFIG
# =====================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DB = "posts.db"

# =====================================================
# DATABASE
# =====================================================
conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS posts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caption TEXT,
    image TEXT,
    time TEXT,
    status TEXT DEFAULT 'Pending',
    retries INTEGER DEFAULT 0
)
""")
conn.commit()

selected_image = ""

# =====================================================
# HELPERS
# =====================================================
def log(msg):
    now = datetime.now().strftime("%H:%M:%S")
    logs.insert("end", f"[{now}] {msg}\n")
    logs.see("end")


# =====================================================
# IMAGE PICKER
# =====================================================
def choose_image():
    global selected_image

    path = filedialog.askopenfilename(
        filetypes=[("Images", "*.png *.jpg *.jpeg")]
    )

    if path:
        selected_image = path
        image_lbl.configure(text="🖼 " + path.split("/")[-1])


# =====================================================
# EXACT CURRENT TIME
# =====================================================
def set_current_time():
    now = datetime.now()

    current_hour = f"{now.hour:02d}"
    current_min = f"{now.minute:02d}"

    hour_var.set(current_hour)

    fixed_minutes = ["00", "10", "15", "20", "30", "45"]
    minute_values = fixed_minutes.copy()

    if current_min not in minute_values:
        minute_values.append(current_min)
        minute_values.sort(key=lambda x: int(x))
        minute_menu.configure(values=minute_values)

    minute_var.set(current_min)

    log(f"🕒 Exact current time loaded: {current_hour}:{current_min}")


# =====================================================
# SCHEDULE POST
# =====================================================
def schedule_post():
    global selected_image

    caption = txt.get("1.0", "end-1c")

    if not caption.strip():
        messagebox.showerror("Error", "Caption required")
        return

    selected_date = cal.get_date()

    dt = datetime.strptime(
        selected_date,
        "%m/%d/%y"
    ).strftime("%Y-%m-%d")

    tm = f"{hour_var.get()}:{minute_var.get()}"

    full = f"{dt} {tm}"

    try:
        datetime.strptime(full, "%Y-%m-%d %H:%M")
    except:
        messagebox.showerror("Error", "Invalid date or time")
        return

    cursor.execute("""
    INSERT INTO posts(caption,image,time)
    VALUES(?,?,?)
    """, (caption, selected_image, full))
    conn.commit()

    txt.delete("1.0", "end")
    selected_image = ""
    image_lbl.configure(text="No image selected")

    load_posts()
    log("✅ Post Scheduled")


# =====================================================
# LOAD POSTS
# =====================================================
def load_posts():
    for item in tree.get_children():
        tree.delete(item)

    cursor.execute("""
    SELECT id,time,status
    FROM posts
    ORDER BY time
    """)

    rows = cursor.fetchall()

    for row in rows:
        tree.insert("", "end", values=row)

    refresh_stats()


# =====================================================
# STATS
# =====================================================
def refresh_stats():
    cursor.execute("SELECT COUNT(*) FROM posts WHERE status='Pending'")
    p = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM posts WHERE status='Posted'")
    d = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM posts WHERE status='Failed'")
    f = cursor.fetchone()[0]

    card1.configure(text=f"📌 Scheduled\n{p}")
    card2.configure(text=f"✅ Posted\n{d}")
    card3.configure(text=f"❌ Failed\n{f}")


# =====================================================
# DELETE
# =====================================================
def delete_selected():
    selected = tree.selection()

    if not selected:
        return

    item = tree.item(selected[0])
    pid = item["values"][0]

    cursor.execute("DELETE FROM posts WHERE id=?", (pid,))
    conn.commit()

    load_posts()
    log("🗑 Deleted Post")


# =====================================================
# LINKEDIN POST
# =====================================================
def run_post(post_id, caption, image):
    try:
        log("🚀 Posting to LinkedIn...")

        post_linkedin(caption, image)

        cursor.execute("""
        UPDATE posts
        SET status='Posted'
        WHERE id=?
        """, (post_id,))
        conn.commit()

        log("✅ Posted Successfully")

    except Exception as e:
        cursor.execute("""
        UPDATE posts
        SET status='Failed',
        retries=retries+1
        WHERE id=?
        """, (post_id,))
        conn.commit()

        log("❌ Failed: " + str(e))


# =====================================================
# AUTO CHECKER
# =====================================================
def scheduler_check():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor.execute("""
    SELECT id,caption,image
    FROM posts
    WHERE time=? AND status='Pending'
    LIMIT 1
    """, (now,))

    rows = cursor.fetchall()

    for row in rows:
        run_post(*row)

    load_posts()


# =====================================================
# UI
# =====================================================
app = ctk.CTk()
app.geometry("1360x920")
app.title("LinkedIn Scheduler Final")

app.grid_columnconfigure((0, 1), weight=1)
app.grid_rowconfigure(0, weight=1)

# =====================================================
# LEFT PANEL
# =====================================================
left = ctk.CTkFrame(app)
left.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

title = ctk.CTkLabel(
    left,
    text="🚀 LinkedIn Scheduler",
    font=("Segoe UI", 28, "bold")
)
title.pack(pady=20)

txt = ctk.CTkTextbox(
    left,
    height=340,
    font=("Segoe UI", 15),
    wrap="word"
)
txt.pack(fill="x", padx=20, pady=10)

img_btn = ctk.CTkButton(
    left,
    text="📸 Upload Image",
    command=choose_image
)
img_btn.pack(fill="x", padx=20, pady=6)

image_lbl = ctk.CTkLabel(left, text="No image selected")
image_lbl.pack()

# =====================================================
# CALENDAR
# =====================================================
calendar_lbl = ctk.CTkLabel(
    left,
    text="📅 Select Date",
    font=("Segoe UI", 16, "bold")
)
calendar_lbl.pack(pady=(10, 5))

cal = Calendar(
    left,
    selectmode="day",
    date_pattern="mm/dd/yy"
)
cal.pack(padx=20, pady=10)

# =====================================================
# TIME PICKER
# =====================================================
time_lbl = ctk.CTkLabel(
    left,
    text="⏰ Select Time",
    font=("Segoe UI", 16, "bold")
)
time_lbl.pack(pady=(10, 5))

time_frame = ctk.CTkFrame(left, fg_color="transparent")
time_frame.pack(pady=8)

# Hour Dropdown
hour_var = tk.StringVar(value="08")

hour_menu = ctk.CTkOptionMenu(
    time_frame,
    values=[f"{i:02d}" for i in range(24)],
    variable=hour_var,
    width=100
)
hour_menu.pack(side="left", padx=5)

colon = ctk.CTkLabel(
    time_frame,
    text=":",
    font=("Segoe UI", 24, "bold")
)
colon.pack(side="left", padx=2)

# Minute Dropdown
minute_var = tk.StringVar(value="15")

minute_menu = ctk.CTkOptionMenu(
    time_frame,
    values=["00", "10", "15", "20", "30", "45"],
    variable=minute_var,
    width=100
)
minute_menu.pack(side="left", padx=5)

# Exact Current Time
now_btn = ctk.CTkButton(
    left,
    text="🕒 Use Current Time",
    command=set_current_time
)
now_btn.pack(fill="x", padx=20, pady=8)

# Schedule Button
btn = ctk.CTkButton(
    left,
    text="✅ Schedule Post",
    height=48,
    command=schedule_post
)
btn.pack(fill="x", padx=20, pady=12)

# =====================================================
# RIGHT PANEL
# =====================================================
right = ctk.CTkFrame(app)
right.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

stats = ctk.CTkFrame(right, fg_color="transparent")
stats.pack(fill="x", padx=20, pady=20)

card1 = ctk.CTkLabel(stats, text="", width=180, height=70, fg_color="#1f6aa5")
card2 = ctk.CTkLabel(stats, text="", width=180, height=70, fg_color="#0d7a4b")
card3 = ctk.CTkLabel(stats, text="", width=180, height=70, fg_color="#9c2d2d")

card1.pack(side="left", padx=6)
card2.pack(side="left", padx=6)
card3.pack(side="left", padx=6)

# Queue Table
tree = ttk.Treeview(
    right,
    columns=("ID", "Time", "Status"),
    show="headings",
    height=14
)

for c in ("ID", "Time", "Status"):
    tree.heading(c, text=c)

tree.column("ID", width=80)
tree.column("Time", width=220)
tree.column("Status", width=120)

tree.pack(fill="x", padx=20, pady=10)

del_btn = ctk.CTkButton(
    right,
    text="🗑 Delete Selected",
    command=delete_selected
)
del_btn.pack(padx=20, pady=8)

# Logs
logs = tk.Text(
    right,
    height=20,
    bg="black",
    fg="#00ff7f",
    font=("Consolas", 11)
)
logs.pack(fill="both", expand=True, padx=20, pady=10)

# =====================================================
# START
# =====================================================
load_posts()

scheduler = BackgroundScheduler()
scheduler.add_job(scheduler_check, "interval", seconds=10)
scheduler.start()

def close():
    scheduler.shutdown()
    conn.close()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", close)
app.mainloop()