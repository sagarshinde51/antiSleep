import streamlit as st
import mysql.connector
import subprocess
import os
import sys
import time
import pandas as pd
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ---------- CONFIG ----------
DB_HOST = '82.180.143.66'
DB_USER = 'u263681140_studentsD'
DB_PASSWORD = 'testStudents@123'
DB_NAME = 'drowsiness_system'

FIXED_CAR_NAME = "Car-Alpha"
FIXED_CAR_ID = "CAR12345"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURE_DIR = os.path.join(PROJECT_DIR, 'static', 'captures')
os.makedirs(CAPTURE_DIR, exist_ok=True)

# ---------- DB HELPER ----------
def get_db_conn():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def init_db():
    try:
        con = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
        cur = con.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        con.close()
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return

    con = get_db_conn()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        phone VARCHAR(20)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INT AUTO_INCREMENT PRIMARY KEY,
        driver VARCHAR(255),
        car_name VARCHAR(255),
        car_id VARCHAR(255),
        image_path TEXT,
        video_path TEXT,
        timestamp VARCHAR(100)
    )
    """)
    con.commit()
    con.close()

# ---------- PAGE SETUP ----------
# ... imports remain the same ...

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="Driver Safety", layout="wide", page_icon="🚗")

# Styling - Advanced CSS with Glassmorphism
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: url("https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1920&q=80") no-repeat center center fixed;
        background-size: cover;
    }
    
    /* Overlay for readability */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(8px);
        z-index: -1;
    }

    /* Container Card Styling */
    .css-1r6slb0, .css-12oz5g7 {  /* Targeting streamlit containers if possible, but generic classes change. */
        /* We rely on creating explicit containers */
    }
    
    /* Custom Card Class for wrapping forms */
    .form-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 40px;
        border-radius: 20px;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        text-align: center;
    }

    /* Input Fields */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        height: 45px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #00eaff;
        box-shadow: 0 0 10px rgba(0, 234, 255, 0.5);
    }
    .stTextInput label {
        color: #e0e0e0 !important;
        font-weight: 500;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00f260 0%, #0575e6 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 600;
        letter-spacing: 1px;
        transition: 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 242, 96, 0.4);
        color: white;
        border-color: transparent;
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #ffffff !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        font-family: 'Segoe UI', sans-serif;
    }
    
    hr {
        border-color: rgba(255, 255, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state['page'] = 'home'
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'user' not in st.session_state:
    st.session_state['user'] = {}

# ---------- NAVIGATION ----------
def go_to(page):
    st.session_state['page'] = page
    st.rerun()

def logout():
    # Stop detector if running
    if 'detector_proc' in st.session_state and st.session_state['detector_proc']:
        st.session_state['detector_proc'].terminate()
        st.session_state['detector_proc'] = None
    
    st.session_state['role'] = None
    st.session_state['user'] = {}
    go_to('home')

# ---------- PAGES ----------

def home_page():
    # Centered Layout
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div style='text-align: center; margin-top: 50px;'><h1 style='font-size: 60px;'>🚗</h1></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>Driver Safety Monitoring</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 18px; color: #ccc; margin-bottom: 50px;'>Real-time Drowsiness Detection System to Prevent Road Accidents</p>", unsafe_allow_html=True)
        
        # Two big cards for roles
        colA, colB = st.columns(2)
        with colA:
            st.markdown("""
            <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; text-align: center; border: 1px solid rgba(255,255,255,0.1);">
                <h3>Drivers</h3>
                <p style="font-size: 40px;">👤</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("User Login / Register"):
                go_to('login')
                
        with colB:
            st.markdown("""
            <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; text-align: center; border: 1px solid rgba(255,255,255,0.1);">
                <h3>Admins</h3>
                <p style="font-size: 40px;">🛡️</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Admin Panel"):
                go_to('admin_login')

def login_page():
    c1, c2, c3 = st.columns([1.5, 2, 1.5])
    with c2:
        st.markdown("<div class='form-card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>Driver Login</h2>", unsafe_allow_html=True)
        
        email = st.text_input("Enter Email", placeholder="user@example.com")
        password = st.text_input("Enter Password", type="password", placeholder="••••••")
        
        st.write("")
        if st.button("Unlock Dashboard", use_container_width=True):
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, name, email, password, phone FROM user WHERE email=%s", (email,))
            row = cur.fetchone()
            conn.close()
            
            if row and check_password_hash(row[3], password):
                st.session_state['role'] = 'user'
                st.session_state['user'] = {'id': row[0], 'name': row[1], 'email': row[2], 'phone': row[4]}
                st.success("Access Granted")
                time.sleep(0.5)
                go_to('dashboard')
            else:
                st.error("Invalid credentials")
        
        st.markdown("<p style='text-align: center; margin-top: 20px;'>New here?</p>", unsafe_allow_html=True)
        if st.button("Create Account", use_container_width=True):
            go_to('register')
            
        st.write("")
        if st.button("← Back Home"):
            go_to('home')
        st.markdown("</div>", unsafe_allow_html=True)

def register_page():
    c1, c2, c3 = st.columns([1.5, 2, 1.5])
    with c2:
        st.markdown("<div class='form-card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>Create Account</h2>", unsafe_allow_html=True)
        
        name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email Address", placeholder="john@example.com")
        phone = st.text_input("Phone Number", placeholder="9876543210")
        password = st.text_input("Password", type="password", placeholder="Min 6 chars")
        confirm = st.text_input("Confirm Password", type="password")
        
        st.write("")
        if st.button("Register & Login", use_container_width=True):
            if not name or not email or not phone or not password:
                st.error("All fields required")
            elif password != confirm:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password too short")
            else:
                try:
                    hashed = generate_password_hash(password)
                    conn = get_db_conn()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO user (name, email, password, phone) VALUES (%s, %s, %s, %s)",
                                (name, email, hashed, phone))
                    conn.commit()
                    conn.close()
                    st.success("Registration successful!")
                    time.sleep(1)
                    go_to('login')
                except Exception as e:
                    st.error(f"Error: {e}")

        st.write("")
        if st.button("Already have an account? Login"):
            go_to('login')
        st.markdown("</div>", unsafe_allow_html=True)

def admin_login_page():
    c1, c2, c3 = st.columns([1.5, 2, 1.5])
    with c2:
        st.markdown("<div class='form-card' style='border-color: rgba(255, 0, 0, 0.3); box-shadow: 0 8px 32px 0 rgba(255, 0, 0, 0.15);'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #ff6b6b !important;'>Admin Access</h2>", unsafe_allow_html=True)
        
        email = st.text_input("Admin ID", placeholder="admin")
        password = st.text_input("Secure Key", type="password", placeholder="••••••")
        
        st.write("")
        if st.button("Authenticate", use_container_width=True):
            if email == 'admin' and password == 'admin123':
                st.session_state['role'] = 'admin'
                st.session_state['user'] = {'name': 'Administrator'}
                st.success("Welcome, Commander")
                time.sleep(0.5)
                go_to('admin_dashboard')
            else:
                st.error("Unauthorized Access")
                
        st.write("")
        if st.button("← Cancel"):
            go_to('home')
        st.markdown("</div>", unsafe_allow_html=True)

def user_dashboard():
    # ... logic remains ...
    if st.session_state['role'] != 'user':
        go_to('login')
        return

    st.markdown("<h1>👋 Dashboard <span style='font-size: 20px; color: #aaa; float: right;'>User: " + st.session_state['user']['name'] + "</span></h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Detector Control
    if 'detector_proc' not in st.session_state:
        st.session_state['detector_proc'] = None
        
    is_running = st.session_state['detector_proc'] is not None and st.session_state['detector_proc'].poll() is None
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div style="padding: 20px; background: rgba(0,0,0,0.2); border-radius: 10px; border-left: 5px solid #00f260;">
            <h3 style="margin:0;">Target Vehicle: {FIXED_CAR_NAME}</h3>
            <p style="margin:0; color:#ccc;">License ID: {FIXED_CAR_ID}</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        if st.button("Logout", key="logout_btn"):
            logout()
            
    st.write("")
    
    cA, cB = st.columns(2)
    with cA:
        if not is_running:
            st.error("Status: 🔴 Stopped")
            if st.button("🚀 Start Monitoring System", type="primary", use_container_width=True):
                # Start process
                py = sys.executable or "python"
                cmd = [py, os.path.join(PROJECT_DIR, 'drowsiness_detector.py'),
                       "--driver", st.session_state['user']['name'], 
                       "--car", FIXED_CAR_NAME, 
                       "--carid", FIXED_CAR_ID,
                       "--db_mode"] 
                
                proc = subprocess.Popen(cmd)
                st.session_state['detector_proc'] = proc
                st.success("System Activated")
                st.rerun()
        else:
            st.success("Status: 🟢 Active & Monitoring")
            if st.button("🛑 Stop Monitoring", type="primary", use_container_width=True):
                st.session_state['detector_proc'].terminate()
                st.session_state['detector_proc'] = None
                st.warning("System Deactivated")
                st.rerun()

    st.write("")
    st.subheader("📢 Recent Alerts")
    
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT timestamp, car_name FROM events WHERE driver=%s ORDER BY id DESC LIMIT 5", (st.session_state['user']['name'],))
    alerts = cur.fetchall()
    conn.close()
    
    if alerts:
        for a in alerts:
            st.warning(f"⚠️ Drowsiness Detected · {a[0]} · {a[1]}")
    else:
        st.info("No recent alerts recorded. Clean driving record! 👍")

def admin_dashboard():
    # ... logic remains ...
    if st.session_state['role'] != 'admin':
        go_to('admin_login')
        return

    # Sidebar Styling
    with st.sidebar:
        st.markdown("## 🛡️ Admin Panel")
        st.markdown("---")
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state['admin_tab'] = 'dash'
        if st.button("👥 Registered Users", use_container_width=True):
            st.session_state['admin_tab'] = 'users'
        if st.button("🔔 Alert History", use_container_width=True):
            st.session_state['admin_tab'] = 'history'
        
        st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
        if st.button("Logout", type="primary", use_container_width=True):
            logout()
            return

    if 'admin_tab' not in st.session_state:
        st.session_state['admin_tab'] = 'dash'
        
    tab = st.session_state['admin_tab']
    
    conn = get_db_conn()
    cur = conn.cursor()
    
    if tab == 'dash':
        st.title("Admin Dashboard")
        cur.execute("SELECT COUNT(*) FROM user")
        u_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM events")
        e_count = cur.fetchone()[0]
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div style="background: rgba(0, 242, 96, 0.1); padding: 30px; border-radius: 15px; text-align: center; border: 1px solid #00f260;">
                <h2 style="color: #00f260 !important;">{u_count}</h2>
                <p>Registered Users</p>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="background: rgba(5, 117, 230, 0.1); padding: 30px; border-radius: 15px; text-align: center; border: 1px solid #0575e6;">
                <h2 style="color: #0575e6 !important;">{e_count}</h2>
                <p>Total Alert Events</p>
            </div>
            """, unsafe_allow_html=True)
        
    elif tab == 'users':
        st.title("👥 Registered Users")
        cur.execute("SELECT id, name, email, phone FROM user")
        users = cur.fetchall()
        df = pd.DataFrame(users, columns=['User ID', 'Full Name', 'Email Address', 'Phone Number'])
        st.dataframe(df, use_container_width=True)
        
    elif tab == 'history':
        st.title("🔔 Alert History")
        cur.execute("SELECT id, driver, car_name, car_id, image_path, video_path, timestamp FROM events ORDER BY id DESC")
        events = cur.fetchall()
        
        for e in events:
            with st.container():
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                    <h4 style="margin:0;">{e[1]} <span style="font-size:14px; font-weight:normal; color:#aaa;">({e[6]})</span></h4>
                    <p style="margin:0; color:#888;">Car: {e[2]} | ID: {e[3]}</p>
                </div>
                """, unsafe_allow_html=True)
                
                colA, colB = st.columns(2)
                
                img_p = e[4]
                vid_p = e[5]
                
                if img_p:
                    full_img = os.path.join(PROJECT_DIR, img_p)
                    if os.path.exists(full_img):
                        colA.image(full_img, caption="Snapshot", use_column_width=True)
                    else:
                        colA.warning("Image missing")
                
                if vid_p:
                    full_vid = os.path.join(PROJECT_DIR, vid_p)
                    if os.path.exists(full_vid):
                        colB.video(full_vid)
                    else:
                        colB.warning("Video missing")

    conn.close()



# ---------- ROUTER ----------
init_db()

if st.session_state['page'] == 'home':
    home_page()
elif st.session_state['page'] == 'login':
    login_page()
elif st.session_state['page'] == 'register':
    register_page()
elif st.session_state['page'] == 'admin_login':
    admin_login_page()
elif st.session_state['page'] == 'dashboard':
    user_dashboard()
elif st.session_state['page'] == 'admin_dashboard':
    admin_dashboard()
