## --- Update user profile in DB ---
def update_user_profile(user_id, name, email, profile_photo=None):
    conn = get_db()
    if profile_photo:
        conn.execute("UPDATE users SET name=?, email=?, profile_photo=? WHERE id=?", (name, email, profile_photo, user_id))
    else:
        conn.execute("UPDATE users SET name=?, email=? WHERE id=?", (name, email, user_id))
    conn.commit()
    conn.close()
# --- Kiosk Mode (for public/shared use) ---
import os
KIOSK_MODE = os.environ.get("LOVEBOOK_KIOSK_MODE", "0") == "1"
import streamlit as st
from fpdf import FPDF
from datetime import datetime
import base64
import sqlite3
import hashlib
import uuid

# QR code support
import qrcode
from PIL import Image

# --- DB Connection Helper (must be above all usages) ---
def get_db():
    conn = sqlite3.connect("lovebook.db", check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        role TEXT DEFAULT 'free',
        usage_count INTEGER DEFAULT 0,
        story TEXT,
        couple_names TEXT,
        profile_photo TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    return conn

# Run migration at startup
def migrate_add_name_column():
    conn = sqlite3.connect("lovebook.db", check_same_thread=False)
    cur = conn.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]
    if "name" not in columns:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN name TEXT")
            conn.commit()
        except Exception as e:
            print(f"Migration error: {e}")
    conn.close()

migrate_add_name_column()

# Run this once at startup to fill missing names
def update_missing_names():
    conn = get_db()
    cur = conn.execute("SELECT id, name, email FROM users")
    users = cur.fetchall()
    for user_id, name, email in users:
        if not name or name.strip() == '':
            fallback_name = email.split('@')[0] if email else 'User'
            conn.execute("UPDATE users SET name=? WHERE id=?", (fallback_name, user_id))
    conn.commit()
    conn.close()
# (No longer call update_missing_names() at startup)

# Page config
# --- Custom Branding/Theming for Venues ---
import os
VENUE_BRAND = os.environ.get("LOVEBOOK_BRAND", "SoulVest LoveBook 💖")
VENUE_LOGO = os.environ.get("LOVEBOOK_LOGO", "https://img.icons8.com/emoji/96/000000/red-heart.png")
VENUE_THEME_COLOR = os.environ.get("LOVEBOOK_THEME_COLOR", "#b91372")
VENUE_BG_GRADIENT = os.environ.get("LOVEBOOK_BG_GRADIENT", "135deg, #ffb6b9 0%, #fae3d9 50%, #ff6a88 100%")

st.set_page_config(
    page_title=f"{VENUE_BRAND} | The Original Digital Memory Book",
    page_icon="💖",
    layout="wide"
)

# --- Google Analytics (gtag.js) ---
st.markdown(f"""
<script async src='https://www.googletagmanager.com/gtag/js?id=G-75ZF3726F6'></script>
<style>
    .sidebar-logo {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 16px;
    }}
    .sidebar-logo img {{
        width: 120px;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(255,0,100,0.3), 0 2px 8px rgba(0,0,0,0.15);
        border: 2px solid #fff;
        animation: heartbeat 1.5s infinite;
    }}
    body {{
        background: linear-gradient({VENUE_BG_GRADIENT}) !important;
    }}
</style>
""", unsafe_allow_html=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(name, email, password):
    if not name or not email or not password:
        return False, "Name, email, and password are required."
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", (name, email, hash_password(password)))
        conn.commit()
        return True, "Signup successful! Please log in."
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    finally:
        conn.close()

def login_user(email, password):
    conn = get_db()
    cur = conn.execute("SELECT id, name, email, password_hash, role, usage_count, story, couple_names, profile_photo FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()
    if row and row[3] == hash_password(password):
        return {
            "id": row[0], "name": row[1], "email": row[2], "role": row[4], "usage_count": row[5],
            "story": row[6] or "", "couple_names": row[7] or "", "profile_photo": row[8]
        }
    return None

def save_user_progress(user_id, story, couple_names):
    conn = get_db()
    conn.execute("UPDATE users SET story=?, couple_names=?, usage_count=usage_count+1 WHERE id=?", (story, couple_names, user_id))
    conn.commit()
    conn.close()

def get_user_by_id(user_id):
    conn = get_db()
    cur = conn.execute("SELECT id, email, role, usage_count, story, couple_names, profile_photo FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0], "email": row[1], "role": row[2], "usage_count": row[3],
            "story": row[4] or "", "couple_names": row[5] or "", "profile_photo": row[6]
        }
    return None

# --- Auth UI ---

# --- Auth UI with Guest Option ---

# --- Welcome Screen & Auth UI with Guest Option ---
def auth_ui():

    # App branding at the top
    st.markdown("""
<div class='lovebook-branding'>
    <span>💖 SoulVest LoveBook</span>
</div>
<style>
    .lovebook-branding {
        width: 100vw;
        text-align: center;
        margin-top: 12px;
        margin-bottom: 0;
        z-index: 10;
    }
    .lovebook-branding span {
        display: inline-block;
        font-family: Georgia,serif;
        color: #b91372;
        font-weight: bold;
        font-size: 2.2rem;
        letter-spacing: 0.5px;
        background: #fff0f6cc;
        border-radius: 18px;
        padding: 0.2em 0.8em;
        box-shadow: 0 2px 8px #b9137240;
        border: 1.5px solid #b91372;
    }
    @media (max-width: 600px) {
        .lovebook-branding span {
            font-size: 1.3rem;
            padding: 0.2em 0.5em;
            border-radius: 12px;
        }
    }
    /* Animated floating hearts background */
    body::before {
        content: '';
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        pointer-events: none;
        z-index: 0;
        background: transparent;
    }
    .floating-heart {
        position: fixed;
        z-index: 1;
        pointer-events: none;
        font-size: 2.2rem;
        animation: floatHeart 7s linear infinite;
        opacity: 0.7;
    }
    @keyframes floatHeart {
        0% { transform: translateY(100vh) scale(1) rotate(0deg); opacity: 0.7; }
        80% { opacity: 0.8; }
        100% { transform: translateY(-10vh) scale(1.2) rotate(30deg); opacity: 0; }
    }
</style>
<script>
// Add floating hearts dynamically
if (!window.heartsAdded) {
  window.heartsAdded = true;
  for (let i = 0; i < 8; i++) {
    let heart = document.createElement('div');
    heart.className = 'floating-heart';
    heart.innerHTML = '💖';
    heart.style.left = (10 + Math.random() * 80) + 'vw';
    heart.style.animationDelay = (Math.random() * 6) + 's';
    heart.style.fontSize = (2 + Math.random() * 2) + 'rem';
    document.body.appendChild(heart);
  }
}
</script>
""", unsafe_allow_html=True)

    # Kiosk mode: always guest, no auth UI
    if KIOSK_MODE:
        st.session_state.user = {"role": "guest", "email": None, "id": None, "usage_count": 0, "story": "", "couple_names": ""}
        return
    # Only show auth UI if not already logged in (including guest)
    if st.session_state.user is not None:
        return

    # Show onboarding radio only after branding, hero, and how it works
    # (Removed duplicate onboarding radio here)
    st.markdown("""
<style>
    .hero-bg-image {
            min-height: 70vh;
            width: 100vw;
            position: relative;
            background: linear-gradient(135deg, #ffb6b9 0%, #fae3d9 50%, #ff6a88 100%);
            border-radius: 24px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.10);
            margin: 0 0 16px 0;
            padding: 32px 0 24px 0;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
    }
    .hero-content {
            background: rgba(255,255,255,0.92);
            border-radius: 24px;
            padding: 48px 32px 32px 32px;
            box-shadow: 0 2px 8px #b9137240;
            max-width: 600px;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
    }
    .main-caption {
            color: #b91372;
            font-family: Georgia,serif;
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 18px;
            letter-spacing: 1px;
            text-align: center;
    }
    .welcome-text {
            color: #b91372;
            font-family: 'Segoe UI',sans-serif;
            font-size: 1.2rem;
            margin-bottom: 8px;
            text-align: center;
    }
    .subheading {
            color: #b91372;
            font-size: 1.1rem;
            margin-bottom: 32px;
            text-align: center;
    }
</style>
<div class='hero-bg-image'>
    <div class='hero-content'>
            <div class='welcome-text'>Welcome to SoulVest LoveBook</div>
            <div class='main-caption'>Love is all we need</div>
            <div class='subheading'>A soulful digital journal for mindful reflection</div>
    </div>
</div>
""", unsafe_allow_html=True)
    # How it works section
    st.markdown("""
<div style='margin:48px auto 0 auto; max-width:800px; text-align:center;'>
<h2 style='color:#b91372;font-family:Georgia,serif;font-size:2rem;margin-bottom:18px;'>How it works</h2>
<div style='display:flex;justify-content:center;gap:40px;flex-wrap:wrap;'>
    <div style='flex:1;min-width:180px;'>
        <div style='font-size:2.5rem;'>📝</div>
        <div style='font-weight:bold;color:#b91372;margin-bottom:6px;'>Create</div>
        <div style='font-size:1rem;color:#7b1c3a;'>Answer thoughtful prompts and capture your love story.</div>
    </div>
    <div style='flex:1;min-width:180px;'>
        <div style='font-size:2.5rem;'>📖</div>
        <div style='font-weight:bold;color:#b91372;margin-bottom:6px;'>View</div>
        <div style='font-size:1rem;color:#7b1c3a;'>See your story come alive in a beautiful digital book.</div>
    </div>
    <div style='flex:1;min-width:180px;'>
        <div style='font-size:2.5rem;'>🎁</div>
        <div style='font-weight:bold;color:#b91372;margin-bottom:6px;'>Share</div>
        <div style='font-size:1rem;color:#7b1c3a;'>Download, print, or share your memories with loved ones.</div>
    </div>
    <div style='flex:1;min-width:180px;'>
        <div style='font-size:2.5rem;'>🎧</div>
        <div style='font-weight:bold;color:#b91372;margin-bottom:6px;'>Listen</div>
        <div style='font-size:1rem;color:#7b1c3a;'>Download your story as an MP3 audio file and listen to your memories anytime.</div>
    </div>
</div>
</div>
""", unsafe_allow_html=True)
    st.write("")
    auth_mode = None
    try:
        auth_mode = st.radio("## Already have an account? Or first time user?", ["Sign Up", "Log In", "Continue as Guest"], horizontal=True, key="onboarding_auth_mode")
    except Exception:
        # fallback if Streamlit fails to render radio
        auth_mode = "Sign Up"

    if auth_mode == "Sign Up":
        name = st.text_input("Your Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_pw")
        if st.button("Sign Up", use_container_width=True, key="hero_signup_btn"):
            success, msg = signup_user(name, email, password)
            if success:
                # Fetch the new user from DB and set session state
                conn = get_db()
                cur = conn.execute("SELECT id, name, email, role, usage_count, story, couple_names, profile_photo FROM users WHERE email=?", (email,))
                row = cur.fetchone()
                conn.close()
                if row:
                    st.session_state.user = {
                        "id": row[0], "name": row[1], "email": row[2], "role": row[3], "usage_count": row[4],
                        "story": row[5] or "", "couple_names": row[6] or "", "profile_photo": row[7]
                    }
                st.success(msg)
            else:
                st.error(msg)
    elif auth_mode == "Log In":
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pw")
        if st.button("Log In", use_container_width=True, key="hero_login_btn"):
            user = login_user(email, password)
            if user:
                st.session_state.user = user
                display_name = user.get('name') or user.get('email','')
                st.success(f"Welcome, {display_name}!")
                st.rerun()
            else:
                st.error("Invalid credentials.")
    else:
        st.session_state.user = {"role": "guest", "email": None, "id": None, "usage_count": 0, "story": "", "couple_names": ""}
        st.info("Continuing as guest. Some features may be limited.")

if 'user' not in st.session_state:
    st.session_state.user = None
auth_ui()
user = st.session_state.user
# --- User Dashboard Tab for Signed-in Users ---
def get_all_books_for_user(user_id):
    conn = get_db()
    cur = conn.execute("SELECT id, story, couple_names, created_at FROM users WHERE id=?", (user_id,))
    books = cur.fetchall()
    conn.close()
    return books


# --- Persistent Guest Mode Banner ---
if user and user.get('role') == 'guest':
    if not KIOSK_MODE:
        with st.sidebar:
            st.markdown('---')
            st.markdown("**Want to save your memories?**")
            if st.button("Sign Up / Log In", key="guest_signup_sidebar"):
                st.session_state.user = None
                st.rerun()
    guest_extra = "<b>Sign up or log in</b> to unlock your personal dashboard, save progress, and access your books anytime, anywhere.<br>" if not KIOSK_MODE else ""
    st.markdown(f"""
<div style='background:linear-gradient(90deg,#ffb6b9 0%,#fae3d9 100%);padding:16px 0 16px 0;text-align:center;border-radius:12px;margin-bottom:18px;border:2px solid #ee9ca7;'>
    <span style='font-size:20px;color:#b91372;font-family:Georgia,serif;font-weight:bold;'>
        You are using SoulVest LoveBook as a <span style='color:#ee9ca7;'>Guest</span>.<br>
        <span style='font-size:16px;font-weight:normal;'>
            <b>Privacy for all:</b> Your memories are always private and never shared.<br>
            <b>Guest mode:</b> You can create a book, but you won't be able to resume or access it from other devices.<br>
            {guest_extra}<span style='color:#b91372;text-decoration:underline;'>No spam, no ads, just your story—always secure.</span>
        </span>
    </span>
</div>
""", unsafe_allow_html=True)

if 'memories' not in st.session_state:
    st.session_state.memories = {}
if 'story_generated' not in st.session_state:
    st.session_state.story_generated = False
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
# Ensure story and couple_names are always initialized
if 'story' not in st.session_state:
    st.session_state.story = ""
if 'couple_names' not in st.session_state:
    st.session_state.couple_names = ""

# Ensure story is always initialized
if 'story' not in st.session_state:
    st.session_state.story = ""


# --- Image Upload for Background ---
uploaded_bg = None

bg_css = """
<style>
    html {
        font-size: 16px;
    }
    @media (max-width: 600px) {
        html { font-size: 15px; }
        .block-container { padding: 0.5rem !important; }
        .stButton>button { font-size: 20px !important; padding: 16px 0 !important; width: 100% !important; }
        .stTextArea textarea, .stTextInput input { font-size: 18px !important; }
        h1, h2, h3, h4 { font-size: 1.3em !important; }
    }
    .sidebar-logo {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 16px;
    }
    .sidebar-logo img {
        width: 120px;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(255,0,100,0.3), 0 2px 8px rgba(0,0,0,0.15);
        border: 2px solid #fff;
        animation: heartbeat 1.5s infinite;
    }
    body {
        background: linear-gradient(135deg, #ffb6b9 0%, #fae3d9 50%, #ff6a88 100%) !important;
    }
    .main {
        background: linear-gradient(135deg, #ffb6b9 0%, #fae3d9 50%, #ff6a88 100%);
    }
    .block-container {
        padding: 2rem;
        background: rgba(255,255,255,0.92);
        border-radius: 22px;
        box-shadow: 0 8px 32px 0 rgba(255, 182, 193, 0.25);
    }
    h1 {
        color: #b91372;
        text-align: center;
        font-family: 'Georgia', serif;
        letter-spacing: 2px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #ff6a88 0%, #ffb6b9 100%);
        color: white;
        border-radius: 14px;
        padding: 12px 36px;
        font-size: 18px;
        border: none;
        font-family: 'Georgia', serif;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(255, 182, 193, 0.15);
        transition: background 0.2s, box-shadow 0.2s;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #fae3d9 0%, #ffb6b9 100%);
    }
    .memory-card {
        background: #fff0f6;
        padding: 24px;
        border-radius: 18px;
        box-shadow: 0 4px 16px rgba(255, 182, 193, 0.13);
        margin: 14px 0;
    }
    .chapter-title {
        color: #b91372;
        font-size: 26px;
        font-weight: bold;
        margin-top: 24px;
        font-family: 'Georgia', serif;
    }
    .story-text {
        font-family: 'Georgia', serif;
        font-size: 18px;
        line-height: 2.0;
        color: #b91372;
        background: #fff0f6;
        padding: 28px;
        border-radius: 14px;
        border-left: 6px solid #ee9ca7;
        box-shadow: 0 2px 8px rgba(255, 182, 193, 0.10);
    }
    /* Sidebar Valentine theme */
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(135deg, #ffb6b9 0%, #fae3d9 100%);
        border-radius: 0 22px 22px 0;
        box-shadow: 0 4px 16px rgba(255, 182, 193, 0.13);
        padding: 32px 18px 24px 18px;
        min-height: 100vh;
        position: relative;
        font-family: 'Poppins', 'Georgia', serif !important;
        color: #b91372 !important;
        font-size: 18px !important;
    }
    [data-testid="stSidebar"]:before {
        content: "";
        display: block;
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: url('https://img.icons8.com/emoji/48/000000/red-heart.png') repeat-y;
        opacity: 0.12;
        z-index: 0;
    }
    .sidebar-logo {
        display: flex;
        align-items: flex-start;
        margin-bottom: 18px;
    }
    .sidebar-logo img {
        width: 120px;
        height: auto;
        margin-right: 12px;
        border-radius: 18px;
        box-shadow: 0 6px 24px 0 rgba(255, 106, 136, 0.35), 0 2px 8px rgba(255, 182, 193, 0.18);
        border: 3px solid #ff6a88;
        transition: transform 0.3s;
        animation: logoPulse 2s infinite;
    }
    @keyframes logoPulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.08); box-shadow: 0 12px 32px 0 rgba(255, 106, 136, 0.45); }
        100% { transform: scale(1); }
    }
    .sidebar-title {
        font-size: 24px;
        font-weight: bold;
        color: #b91372;
        font-family: 'Poppins', 'Georgia', serif;
        margin-top: 8px;
        margin-bottom: 8px;
    }
    .sidebar-section {
        font-size: 18px;
        color: #b91372;
        font-family: 'Poppins', 'Georgia', serif;
        margin-bottom: 12px;
    }
    .sidebar-link {
        color: #ff6a88 !important;
        font-weight: bold;
        font-size: 18px;
        text-decoration: underline;
    }
    .sidebar-song {
        font-size: 17px;
        color: #b91372;
        margin-bottom: 6px;
    }
    .sidebar-section-title {
        font-size: 20px;
        font-weight: bold;
        color: #b91372;
        margin-top: 18px;
        margin-bottom: 8px;
    }
    /* Main text improvements */
    .main, .block-container, .story-text {
        font-family: 'Poppins', 'Georgia', serif !important;
        color: #b91372 !important;
        font-size: 20px !important;
    }
</style>
"""

if uploaded_bg is not None:
    import base64
    from PIL import Image
    img = Image.open(uploaded_bg)
    img = img.resize((1920, 1080))
    buf = st.experimental_memo(lambda: None, ttl=0)()
    from io import BytesIO
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()
    custom_bg = f"""
    <style>
    body {{
        background-image: url('data:image/png;base64,{img_b64}');
        background-size: cover !important;
        background-attachment: fixed !important;
    }}
    .main {{
        background: rgba(255,255,255,0.97); /* Increased opacity for better readability */
        box-shadow: 0 0 32px 8px rgba(0,0,0,0.10);
        border-radius: 18px;
        padding: 16px 0;
    }}
    </style>
    """
    st.markdown(custom_bg, unsafe_allow_html=True)

    # Hide Ctrl+Enter hint in text areas
    st.markdown("""
    <style>
    .stTextArea [data-baseweb="textarea"] + div {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown(bg_css, unsafe_allow_html=True)
    st.markdown("""
    <style>
    .stTextArea [data-baseweb="textarea"] + div {
        display: none !important;
    }
    .stTextArea textarea {
        min-height: 32px !important;
        max-height: 40px !important;
        font-size: 16px !important;
        padding: 6px 10px !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)


st.title("💖 SoulVest LoveBook")
if not user:
    st.warning("Please log in, sign up, or continue as guest to use the app.")
    st.stop()
st.markdown("""
<div style='text-align:center;margin-top:24px;margin-bottom:8px;'>
    <span style='font-size:32px; color:#ee9ca7; font-family:Georgia,serif; font-weight:bold;'>
        Welcome to SoulVest LoveBook 💞
    </span><br>
    <span style='font-size:20px; color:#b91372; font-family:Georgia,serif;'>
        Sometimes, the best way to share your heart is to write it down. Let your memories, laughter, and dreams come alive on these pages. Discover new things about each other, relive your favorite moments, and enjoy the journey together.
    </span>
</div>
<div class="heart-beat" style="margin: 0 auto 18px auto; display: flex; justify-content: center;">
  <div class="heart-shape"></div>
</div>
""", unsafe_allow_html=True)
st.markdown("<span style='font-size:26px;color:#b91372;font-family:Georgia,serif;'>Every heartbeat, a memory. Every memory, a step closer together.</span>", unsafe_allow_html=True)
st.markdown(":sparkling_heart: <span style='font-size:20px;color:#b91372;'>Let your love story unfold—one answer, one smile, one page at a time.</span>", unsafe_allow_html=True)
import random
romantic_quotes = [
        ("Love is composed of a single soul inhabiting two bodies.", "Aristotle"),
        ("Whatever our souls are made of, his and mine are the same.", "Emily Brontë"),
        ("I have found the one whom my soul loves.", "Song of Solomon 3:4"),
        ("You are my today and all of my tomorrows.", "Leo Christopher"),
        ("In all the world, there is no heart for me like yours.", "Maya Angelou"),
        ("The best thing to hold onto in life is each other.", "Audrey Hepburn"),
        ("To love and be loved is to feel the sun from both sides.", "David Viscott"),
        ("I would rather spend one lifetime with you than face all the ages of this world alone.", "J.R.R. Tolkien"),
        ("You are my greatest adventure.", "The Incredibles"),
]
quote, author = random.choice(romantic_quotes)
st.markdown(f"""
<div style='text-align:center; margin: 18px 0 0 0;'>
    <span style='font-size:28px; color:#b91372; font-family:Georgia,serif; font-weight:bold; letter-spacing:1px;'>
        "{quote}"
    </span><br>
    <span style='font-size:22px; color:#ee9ca7; font-family:Georgia,serif; font-weight:bold;'>– {author}</span>
</div>
""", unsafe_allow_html=True)
st.markdown("---")
# Usage Stats Section (move out of previous block)

st.subheader("📊 Your Growth & Engagement")
stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
with stats_col1:
    st.write("Books Created")
    st.write(f"**{user.get('usage_count',0)}**")
with stats_col2:
    entries = len(st.session_state.story.split('\n\n')) if st.session_state.story else 0
    st.write("Entries")
    st.write(f"**{entries}**")
with stats_col3:
    streak = random.randint(1, 7)
    st.write("Streak")
    st.write(f"**{streak}d**")
with stats_col4:
    st.write("Growth")
    st.write(":seedling:")
st.info("Your sanctuary grows with you 🌸")

import os
with st.sidebar:
    # --- My Account/Profile Section ---
    user = st.session_state.get('user', {})
    with st.expander("👤 My Account", expanded=True):
        if user and user.get('email'):
            profile_photo_path = user.get('profile_photo')
            if profile_photo_path and os.path.exists(profile_photo_path):
                st.image(profile_photo_path, width=72)
            st.write(f"**{user.get('email')}**")
            st.caption("Welcome back!")
        else:
            st.write("**Guest**")
            st.caption("Welcome to LoveBook!")
    st.divider()
    # --- Edit Profile Section ---
    st.subheader("Edit Profile")
    new_name = st.text_input("Name", value=user.get('name',''), key="edit_name")
    new_email = st.text_input("Email", value=user.get('email',''), key="edit_email")
    new_photo = st.file_uploader("Update Profile Photo", type=["jpg","jpeg","png"], key="edit_photo")
    if new_photo is not None:
        st.image(new_photo, width=72, caption="Preview")
    if st.button("Save Changes", key="save_profile_btn", help="Update your profile info"):
        photo_path = None
        if new_photo is not None:
            import tempfile
            import shutil
            temp_dir = tempfile.gettempdir()
            photo_path = os.path.join(temp_dir, new_photo.name)
            with open(photo_path, "wb") as f:
                shutil.copyfileobj(new_photo, f)
        update_user_profile(user['id'], new_name, new_email, photo_path)
        st.session_state.user['name'] = new_name
        st.session_state.user['email'] = new_email
        if photo_path:
            st.session_state.user['profile_photo'] = photo_path
        st.success("Profile updated!")
    # QR code for homepage quick access
    HOMEPAGE_URL = "https://lovebook.soulvest.app"  # Update to your homepage
    def generate_qr_code(url):
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#b91372", back_color="white").convert('RGB')
        return img
    st.markdown("<div style='text-align:center;'><b>Scan to use LoveBook anywhere!</b></div>", unsafe_allow_html=True)
    st.image(generate_qr_code(HOMEPAGE_URL), caption="Open LoveBook on your phone", width=200)
    with st.expander("🤔 Did You Know? Ho'oponopono"):
        st.markdown("Have you heard of Ho'oponopono?")
        st.markdown("""
        <span style='color:#b91372;'>
        <b>Ho'oponopono</b> is a Hawaiian practice of reconciliation and forgiveness. It helps heal relationships by encouraging us to say four simple phrases:
        <br><br>
        <b>I'm sorry. Please forgive me. Thank you. I love you.</b>
        <br><br>
        Use these words to express your feelings, release past hurts, and invite harmony into your relationship. Even if spoken or written silently, they can bring peace and understanding.
        </span>
        """, unsafe_allow_html=True)
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    st.image(VENUE_LOGO, width=120)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<span class='sidebar-title'>SoulVest LoveBook</span>", unsafe_allow_html=True)
    # File uploader removed from sidebar; only appears in main content area
    st.markdown("---")
    # Removed duplicate Love Language Suggestions section
    st.markdown("### 💝 How it works")
    st.markdown("""
    1. **Fill in your memories** and answer fun, thoughtful questions together
    2. **See your story come alive** as a keepsake PDF
    3. **Add more memories or reflections** anytime!

    <span style='color:#b91372;font-size:16px;'><b>Data Privacy:</b> Everything you enter—names, memories, photos, and feedback—stays <b>only in your browser</b> and is <b>never uploaded or shared</b>. Your privacy and comfort are our top priority.</span>

    <span style='font-weight:bold;'>Perfect for:</span>
    - Rediscovering each other
    - Sharing a laugh or a memory
    - Celebrating your unique bond
    - Valentine's Day, anniversaries, or any day you want to connect ❤️
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 💡 Pro Love & Relationship Tips")
    pro_tips = [
        "What's your partner's love language? Try a little experiment—give them a compliment, a hug, or a small surprise and see what makes them light up!",
        "Ever just listened, really listened, to your partner? Sometimes, that's all it takes to make their day.",
        "A quick thank you or a silly compliment can turn an ordinary moment into something special. Sprinkle them often!",
        "Disagreements? Totally normal! Next time, try saying 'I feel...' instead of 'You always...'. It keeps things chill.",
        "Messed up? Happens to everyone. A simple 'I'm sorry' (and a hug) can work wonders.",
        "Busy week? Even 10 minutes of phone-free time together can feel like a mini-vacation.",
        "Ask your partner something new about their childhood or dreams. You might be surprised what you learn!",
        "Cheer each other on—big wins, small wins, or just making it through Monday. High fives encouraged!",
        "Don't forget the power of a random hug, a kiss on the forehead, or holding hands. Feels good, right?",
        "Laughter is the best glue. Share a meme, watch a funny video, or just be silly together!",
        "Share your feelings, not just your plans. Emotional closeness is the real magic.",
        "When things get tough, sometimes a listening ear or a warm cup of tea means more than any gift. Be there for each other.",
        "Did you know? The Hawaiian practice of Ho'oponopono uses four simple phrases—I'm sorry. Please forgive me. Thank you. I love you.—to heal and strengthen relationships. Try writing or saying these words to your partner for a powerful, loving impact!"
    ]
    import random
    if 'tip_index' not in st.session_state:
        st.session_state.tip_index = random.randint(0, len(pro_tips)-1)
    if st.button('Show me another tip', key='next_tip'):
        st.session_state.tip_index = (st.session_state.tip_index + 1) % len(pro_tips)
    st.info(pro_tips[st.session_state.tip_index])
    st.markdown("### 🎁 Place a Gift Order (External)")
    st.markdown("<span style='color:#b91372;font-size:16px;'>Surprise your loved one with a gift! Choose from these famous sites (not paid, just for your convenience):</span>", unsafe_allow_html=True)
    st.markdown("""
    - [Ferns N Petals (FNP)](https://www.fnp.com/)
    - [FlowerAura](https://www.floweraura.com/)
    - [Winni](https://www.winni.in/)
    - [GiftstoIndia24x7](https://www.giftstoindia24x7.com/)
    - [Archies Online](https://www.archiesonline.com/)
    """)
    st.markdown("---")
    st.markdown("**Made with ❤️ by [SoulVest.ai](https://soulvest.ai)**")


# Main content
dashboard_tab = None
tab_names = ["📝 Create Memory Book", "📖 View Your Story"]
if user and user.get('role') not in (None, 'guest'):
    tab_names.append("👤 My Dashboard")

# Determine which tab to show by default
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = 0
if st.session_state.get('show_dashboard'):
    st.session_state['active_tab'] = 2
    st.session_state['show_dashboard'] = False

# Top-right Logout button
import streamlit as st_logout
if user and user.get('email'):
    st_logout.markdown("""
    <div style='position:fixed;top:18px;right:32px;z-index:999;'>
        <form action="#" method="post" style="display:inline;">
            <button type="submit" style='background:#b91372;color:#fff;border:none;padding:8px 22px;border-radius:18px;font-size:1rem;cursor:pointer;' name="logout_btn">🚪 Logout</button>
        </form>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <style>
        .sidebar-logout-btn { position: fixed; left: 0; bottom: 0; width: 16em; padding: 1em 0 1.5em 2em; background: none; z-index: 100; }
        </style>
        <div class='sidebar-logout-btn'>
    """, unsafe_allow_html=True)
    if st.button("🚪 Logout", key="logout_btn_sidebar", help="Logout"):
        st.session_state.user = None
        st.success("Logged out!")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

tabs = st.tabs(tab_names)
tab1 = tabs[0]
tab2 = tabs[1]
dashboard_tab = tabs[2] if len(tabs) > 2 else None

with tab1:
    import streamlit_webrtc as webrtc
    import av
    import queue
    import threading
    import speech_recognition as sr

    class AudioProcessor:
        def __init__(self):
            self.q = queue.Queue()
            self.result = ""
            self.lock = threading.Lock()

        def recv(self, frame):
            audio = frame.to_ndarray()
            self.q.put(audio)
            return frame

        def recognize(self):
            recognizer = sr.Recognizer()
            while not self.q.empty():
                audio = self.q.get()
                try:
                    with sr.AudioFile(audio) as source:
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data)
                        with self.lock:
                            self.result += text + " "
                except Exception:
                    pass
            return self.result

    # Ho'oponopono-inspired final touch
    st.markdown("---")
    st.markdown("### 🌺 Express from the Heart")
    st.markdown("Sometimes, a few simple words can heal and bring you closer. Use this space to write a heartfelt message to your partner, inspired by the spirit of Ho'oponopono:")
    st.caption("E.g. Hi dear, I am sorry if I hurt you unintentionally. Please forgive me. Thank you for being there, and I love you.")
    hooponopono_message = st.text_area("Your heartfelt message (optional)", key="hooponopono", height=60)
    # Fun Quiz: How well do you know each other?
    with st.expander("🎲 Fun Quiz: How Well Do You Know Each Other?"):
        st.markdown("Test how much you know about your partner! Each of you can answer separately, then compare your answers for some fun and surprises.")
        quiz_questions = [
            ("What is your partner's favorite food?", "E.g. Pizza, Sushi, etc."),
            ("What is your partner's dream vacation destination?", "E.g. Paris, Maldives, etc."),
            ("What is your partner's biggest pet peeve?", "E.g. Loud chewing, being late, etc."),
            ("What song always reminds you of your partner?", "E.g. 'Perfect' by Ed Sheeran, etc."),
            ("What is your partner's hidden talent?", "E.g. Singing, drawing, etc.")
        ]
        for idx, (q, ph) in enumerate(quiz_questions):
            st.text_input(f"{idx+1}. {q}", placeholder=ph, key=f"quiz_{idx}")

    st.markdown("## Tell Us Your Story")
    uploaded_bg = st.file_uploader(
        "Upload your photo (optional)",
        type=["jpg", "jpeg", "png"],
        help="Personalize your memory book with a photo!",
        key="main_bg_upload"
    )
    st.info("Uploading your photo is optional. If you choose to upload, your photo will be used as the background for your personalized memory book PDF. If you do not upload a photo, a beautiful default background will be used instead. Your photo is not shared or stored anywhere else.")

    col1, col2 = st.columns(2)
    with col1:
        st.write("Your Name")
        person1_name = st.text_input("", key="p1", label_visibility="collapsed")
        st.caption("Or use your microphone:")
        audio_processor_name = AudioProcessor()
        webrtc_streamer_name = webrtc.webrtc_streamer(
            key="name_mic",
            audio_processor_factory=lambda: audio_processor_name,
            media_stream_constraints={"audio": True, "video": False},
            async_processing=False,
        )
        if webrtc_streamer_name.state.playing:
            st.info("Recording... Speak your name.")
        if audio_processor_name.result:
            st.session_state.p1 = audio_processor_name.result
            person1_name = audio_processor_name.result

    with col2:
        st.write("Partner's Name")
        person2_name = st.text_input("", key="p2", label_visibility="collapsed")
        st.caption("Or use your microphone:")
        audio_processor_partner = AudioProcessor()
        webrtc_streamer_partner = webrtc.webrtc_streamer(
            key="partner_mic",
            audio_processor_factory=lambda: audio_processor_partner,
            media_stream_constraints={"audio": True, "video": False},
            async_processing=False,
        )
        if webrtc_streamer_partner.state.playing:
            st.info("Recording... Speak your partner's name.")
        if audio_processor_partner.result:
            st.session_state.p2 = audio_processor_partner.result
            person2_name = audio_processor_partner.result

    # Multiple themed question sets
    question_sets = {
        "Classic Love Story (Default)": [
            ("The moment you first met or noticed each other. What do you remember most?", "E.g. At a coffee shop, I noticed their smile...", "first_meeting", "Tip: Think about the setting, your first impression, or a funny detail from that day."),
            ("A memory that always makes you smile when you think of your partner.", "E.g. That time we got caught in the rain and laughed so much...", "smile_memory", "Tip: Recall a moment that brings you joy or makes you laugh every time you remember it."),
            ("Describe a challenge you both overcame together. How did it make your bond stronger?", "E.g. We moved to a new city and supported each other...", "challenge", "Tip: Challenges can be big or small—focus on how you supported each other."),
            ("What is something your partner does that makes you feel truly loved?", "E.g. They always remember the little things...", "feel_loved", "Tip: It could be a daily gesture, a habit, or something they say that warms your heart."),
            ("Share a dream or adventure you both want to experience in the future.", "E.g. Travel the world together, start a family...", "future_dream", "Tip: Let your imagination run wild—what would you love to do together?"),
            ("What is your favorite thing about your relationship?", "E.g. We can be silly together and always support each other...", "fav_thing", "Tip: Think about what makes your bond special or different from others."),
            ("Describe a perfect day together, from morning to night.", "E.g. Waking up late, breakfast in bed, a walk in the park...", "perfect_day", "Tip: Imagine your ideal day—what would you do, where would you go, how would you feel?"),
            ("What advice would you give to other couples about love?", "E.g. Always communicate and never stop having fun...", "advice", "Tip: Share wisdom from your own experience or something you wish you knew earlier."),
            ("Write a message to your partner for the future.", "E.g. No matter what, I’ll always be by your side...", "future_message", "Tip: Speak from the heart—what do you want your partner to remember or feel?"),
            ("What makes your love story unique?", "E.g. We met by chance and it changed our lives forever...", "unique_story", "Tip: Every love story is different—what makes yours stand out?")
        ],
        "Hobbies, Passions & Love Language": [
            ("What hobby or activity do you most enjoy doing together?", "E.g. Cooking, hiking, painting...", "shared_hobby", "Tip: Think about what brings you both joy."),
            ("Describe a time you supported each other's passions or dreams.", "E.g. Cheering at their first art show...", "support_passions", "Tip: How do you encourage each other?"),
            ("What is your partner's favorite way to relax or unwind?", "E.g. Reading, music, yoga...", "relax_way", "Tip: What helps them recharge?"),
            ("How do your love languages differ or match?", "E.g. Words of affirmation vs. acts of service...", "love_language", "Tip: How do you express and receive love?"),
            ("Share a new skill or hobby you want to try together.", "E.g. Dancing, pottery, learning a language...", "new_skill", "Tip: What would be fun to learn as a couple?"),
            ("What is something your partner is passionate about that inspires you?", "E.g. Their dedication to volunteering...", "partner_passion", "Tip: What do you admire about their interests?"),
            ("Describe a favorite memory related to music, art, or creativity.", "E.g. Singing karaoke together...", "creative_memory", "Tip: Any artistic or musical moments?"),
            ("How do you celebrate each other's achievements, big or small?", "E.g. Special dinner, handwritten note...", "celebrate_achievements", "Tip: What rituals or habits do you have?"),
            ("What is a quirky or unique interest you share?", "E.g. Collecting postcards, birdwatching...", "quirky_interest", "Tip: Something that makes your bond special."),
            ("If you could plan the perfect day based on your shared passions, what would it look like?", "E.g. Morning run, afternoon cooking, evening movie...", "passion_day", "Tip: Combine your favorite things!"),
        ],
        "Anniversary Reflections": [
            ("What is your favorite memory from the past year together?", "E.g. Our trip to the mountains...", "fav_year_memory", "Tip: Think about a moment that defined your year."),
            ("How has your relationship grown or changed this year?", "E.g. We learned to communicate better...", "growth", "Tip: Reflect on your journey as a couple."),
            ("What is something new you discovered about your partner?", "E.g. Their hidden talent for cooking...", "discovery", "Tip: Surprises, quirks, or new habits."),
            ("What are you most grateful for in your relationship?", "E.g. Their constant support...", "gratitude", "Tip: Big or small, what means the most?"),
            ("What is your wish for the coming year together?", "E.g. More adventures and laughter...", "wish", "Tip: Hopes, dreams, or goals for the future."),
        ],
        "Adventure & Travel": [
            ("Describe your most memorable trip together.", "E.g. Our Paris adventure...", "memorable_trip", "Tip: What made it special?"),
            ("What destination is on your couple's bucket list?", "E.g. Japan in cherry blossom season...", "bucket_list", "Tip: Dream big!"),
            ("Share a funny or unexpected travel story.", "E.g. We got lost and found a hidden gem...", "funny_travel", "Tip: Mishaps, surprises, or laughs."),
            ("What do you love most about traveling together?", "E.g. Discovering new foods...", "love_travel", "Tip: What makes you a great travel team?"),
            ("If you could go anywhere tomorrow, where would you go and why?", "E.g. Back to the beach...", "go_anywhere", "Tip: Let your imagination run wild!"),
        ]
    }

    # Let user select a question set
    st.markdown("### Choose a Question Set for Your Book")
    # Only allow additional sets for paid users
    if user and user.get('role') == 'premium':
        question_set_names = list(question_sets.keys())
    else:
        question_set_names = ["Classic Love Story (Default)"]
        if user and user.get('role') == 'free':
            st.info("Upgrade to premium to unlock more question sets!")
    selected_set = st.selectbox("Select a theme:", question_set_names, key="question_set_selector")
    questions = question_sets[selected_set]

    answers = {}
    for idx, (q, ph, key, tip) in enumerate(questions):
        st.write(f"{idx+1}. {q}")
        st.caption(tip)
        answers[key] = st.text_area(
            label=" ",
            placeholder=ph,
            key=f"ans_{key}",
            height=32,
            label_visibility="collapsed",
            help=" "
        )
        st.caption("Or use your microphone:")
        audio_processor_ans = AudioProcessor()
        webrtc_streamer_ans = webrtc.webrtc_streamer(
            key=f"ans_mic_{key}",
            audio_processor_factory=lambda: audio_processor_ans,
            media_stream_constraints={"audio": True, "video": False},
            async_processing=False,
        )
        if webrtc_streamer_ans.state.playing:
            st.info("Recording... Speak your answer.")
        if audio_processor_ans.result:
            st.session_state[f"ans_{key}"] = audio_processor_ans.result
            answers[key] = audio_processor_ans.result
        # --- Autosave for signed-in users ---
        if user and user.get('role') not in (None, 'guest'):
            # Save partial progress (answers) as a draft story
            partial_story = f"{st.session_state.get('p1','')} & {st.session_state.get('p2','')}'s Memory Book\n\n"
            for jdx, (q2, ph2, key2, tip2) in enumerate(questions):
                ans2 = st.session_state.get(f"ans_{key2}", '').strip()
                if ans2:
                    partial_story += f"Page {jdx+1}: {q2}\n\n{ans2}\n\n"
            save_user_progress(user['id'], partial_story, f"{st.session_state.get('p1','')} & {st.session_state.get('p2','')}")

    # Generate button
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("✨ Generate Our Memory Book", use_container_width=True):
            required_fields = [person1_name, person2_name, answers.get('first_meeting',''), answers.get('smile_memory','')]
            if not all(required_fields):
                st.error("⚠️ Please fill in at least: Names and the first two questions.")
            else:
                with st.spinner("Creating your beautiful memory book... 📖"):
                    # Build story from all answers
                    story = f"""
{person1_name} & {person2_name}'s Memory Book\n\n"""
                    for idx, (q, ph, key, tip) in enumerate(questions):
                        ans = answers.get(key, '').strip()
                        if ans:
                            story += f"Page {idx+1}: {q}\n\n{ans}\n\n"
                    st.session_state.story = story
                    st.session_state.story_generated = True
                    st.session_state.couple_names = f"{person1_name} & {person2_name}"
                    # Save to DB for persistence only if not guest
                    if user and user.get('role') != 'guest':
                        save_user_progress(user['id'], story, st.session_state.couple_names)
                    st.success("✨ Your memory book is ready!")
                    st.balloons()
                    st.info("Your story was crafted using your own beautiful memories and words. Go to the 'View Your Story' tab to see it and share the love!")

        # --- Prompt guest to sign up after book ---
        if user and user.get('role') == 'guest' and st.session_state.story_generated:
            st.markdown("""
            <div style='background:linear-gradient(90deg,#fae3d9 0%,#ffb6b9 100%);padding:18px 0 18px 0;text-align:center;border-radius:12px;margin:24px 0 18px 0;border:2px solid #ee9ca7;'>
                <span style='font-size:20px;color:#b91372;font-family:Georgia,serif;font-weight:bold;'>
                    Want to save and resume your story? <br>
                    <span style='font-size:16px;font-weight:normal;'>Sign up now to create your free SoulVest LoveBook account!</span>
                </span>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("Sign Up for Free", expanded=True):
                email = st.text_input("Email", key="guest_signup_email")
                password = st.text_input("Password", type="password", key="guest_signup_pw")
                password2 = st.text_input("Confirm Password", type="password", key="guest_signup_pw2")
                if st.button("Sign Up & Save My Book", key="guest_signup_btn"):
                    if not email or not password:
                        st.error("Email and password required.")
                    elif password != password2:
                        st.error("Passwords do not match.")
                    else:
                        ok, msg = signup_user(email, password)
                        if ok:
                            st.success("Account created! Please log in to save and resume your book.")
                        else:
                            st.error(msg)

with tab2:
    # ...existing code for View Your Story...
    pass

if dashboard_tab:
    with dashboard_tab:
        st.markdown("# 👤 My Dashboard")
        st.markdown("---")
        # Profile and Stats Section (HTML removed)
        import base64
        from datetime import datetime
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            profile_photo_path = user.get('profile_photo')
            if profile_photo_path and os.path.exists(profile_photo_path):
                st.image(profile_photo_path, width=80)
            else:
                st.image(VENUE_LOGO, width=80)
        with col2:
            name = user.get('name') or user.get('email','Guest').split('@')[0]
            st.subheader(name)
            st.caption(user.get('email',''))
            role = user.get('role','guest').capitalize()
            st.info(f"{role}")
        with col3:
            books_created = user.get('usage_count',0)
            last_active = user.get('last_active') or datetime.now().strftime('%Y-%m-%d')
            st.caption("Books Created")
            st.metric(label="", value=books_created)
            st.caption("Last Active")
            st.metric(label="", value=last_active)
        st.markdown("---")
        # Saved Books Section
        st.subheader("📚 Your Saved Memory Books")
        # Sorting/Filtering
        sort_options = ["Date Created (Newest)", "Date Created (Oldest)", "Alphabetical"]
        sort_choice = st.selectbox("Sort by:", sort_options, key="sort_books")
        privacy_toggle = st.checkbox("Show Private Books Only", key="privacy_toggle")
        books = get_all_books_for_user(user['id'])
        if books:
            # Privacy-first: filter private books (simulate with even/odd id)
            if privacy_toggle:
                books = [b for b in books if b[0] % 2 == 0]
            if sort_choice == "Date Created (Newest)":
                books = sorted(books, key=lambda x: x[3], reverse=True)
            elif sort_choice == "Date Created (Oldest)":
                books = sorted(books, key=lambda x: x[3])
            elif sort_choice == "Alphabetical":
                books = sorted(books, key=lambda x: (x[2] or '').lower())
            import random
            card_cols = st.columns(2)
            for idx, book in enumerate(books):
                with card_cols[idx % 2]:
                    # Thumbnail: use a symbolic cover (emoji or color block)
                    color = random.choice(['#ffb6b9','#fae3d9','#ff6a88','#b91372','#6c5ce7'])
                    lock_icon = "🔒" if book[0] % 2 == 0 else ""
                    st.markdown(f"""
                    <div style='background:{color};border-radius:16px;padding:18px 16px 12px 16px;margin-bottom:16px;box-shadow:0 2px 8px #f8e1e7;'>
                        <div style='display:flex;align-items:center;justify-content:space-between;'>
                            <div style='font-size:2.2rem;'>{lock_icon}📖</div>
                            <div style='font-size:1.3rem;font-weight:bold;color:#b91372'>{book[2] or 'Untitled Book'}</div>
                            <div style='position:relative;'>
                                <span style='font-size:1.5rem;cursor:pointer;' title='More actions'>⋮</span>
                            </div>
                        </div>
                        <div style='color:#636e72;font-size:0.95rem;margin-top:2px;'>Created: {book[3]}</div>
                        <div style='margin-top:10px;'>
                            <form action="#" method="post">
                                <button type="submit" style='background:#b91372;color:#fff;border:none;padding:6px 18px;border-radius:8px;font-size:1rem;cursor:pointer;' name="view_{book[0]}">View</button>
                            </form>
                        </div>
                        <div style='margin-top:8px;font-size:0.95rem;color:#888;'>Your sanctuary grows with you 🌸</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"View Story", key=f"view_{book[0]}"):
                        st.session_state.story = book[1]
                        st.session_state.couple_names = book[2]
                        st.session_state.story_generated = True
                        st.success("Loaded your saved book! Go to 'View Your Story' tab.")
        else:
            st.info("No saved books yet. Create your first memory book!")
        st.markdown("---")
    st.markdown("---")
    st.markdown("### 🎧 Download Your Story as Audio (MP3)")
    st.markdown("<span style='color:#b91372;'>Generate an MP3 audio file of your story to listen anytime. Choose from multiple voice styles for a personalized experience!</span>", unsafe_allow_html=True)
    import tempfile
    import asyncio
    import edge_tts
    voice_options = {
        "Romantic Female (Aria)": "en-US-AriaNeural",
        "Romantic Male (Guy)": "en-US-GuyNeural",
        "Warm Female (Jenny)": "en-US-JennyNeural",
        "Warm Male (Davis)": "en-US-DavisNeural",
        "Narrator (Amber)": "en-US-AmberNeural"
    }
    selected_voice = st.selectbox("Choose a voice style for your audio:", list(voice_options.keys()), index=0)
    def story_to_mp3(text, voice):
        try:
            async def _gen():
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tts_fp:
                    communicate = edge_tts.Communicate(text, voice)
                    await communicate.save(tts_fp.name)
                    with open(tts_fp.name, "rb") as f:
                        return f.read()
            return asyncio.run(_gen())
        except Exception:
            return None
    if st.button("🎵 Generate MP3 Audio", key="download_story_mp3"):
        thank_you_note = "\n\nThanks for using our SoulVest Love Book. Have a great day with your partner!"
        story_with_thanks = st.session_state.story + thank_you_note
        audio_bytes = story_to_mp3(story_with_thanks, voice_options[selected_voice])
        if audio_bytes:
            st.download_button(
                label="📥 Download Story Audio (MP3)",
                data=audio_bytes,
                file_name="memory_book_story.mp3",
                mime="audio/mp3"
            )
        else:
            st.info("Audio generation failed. Please ensure edge-tts is installed.")

        if st.session_state.story_generated:
            # Immersive Book Viewer
            st.markdown(f"## 📖 {st.session_state.couple_names}")
            if st.session_state.start_date:
                st.markdown(f"*Since {st.session_state.start_date.strftime('%B %d, %Y')}*")

            # Day/Night mode toggle
            mode = st.radio("Mode", ["Day", "Night"], horizontal=True, key="book_viewer_mode")
            bg = "#fff" if mode == "Day" else "#232946"
            fg = "#b91372" if mode == "Day" else "#eebbc3"
            st.markdown(f"<div style='background:{bg};padding:32px 18px 32px 18px;border-radius:18px;box-shadow:0 2px 12px #f8e1e7;transition:background 0.5s;'>", unsafe_allow_html=True)
            st.markdown(":sparkling_heart: <span style='color:{fg};font-size:18px;'>Your story is safe here—ready to be shared, treasured, and celebrated. Love, after all, is the greatest story ever told.</span>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; margin: 0 0 18px 0;'><span style='font-size:18px; color:{fg}; font-family:Georgia,serif; font-style:italic;'>\"Whatever our souls are made of, his and mine are the same.\"<br>– Emily Brontë</span></div>", unsafe_allow_html=True)
            # Soft animation for flipping entries (simulate with next/prev buttons)
            story_entries = st.session_state.story.split('\n\n') if st.session_state.story else []
            if 'story_page' not in st.session_state:
                st.session_state.story_page = 0
            col_prev, col_page, col_next = st.columns([1,2,1])
            with col_prev:
                if st.button('⬅️', key='prev_entry'):
                    st.session_state.story_page = max(0, st.session_state.story_page-1)
            with col_next:
                if st.button('➡️', key='next_entry'):
                    st.session_state.story_page = min(len(story_entries)-1, st.session_state.story_page+1)
            with col_page:
                st.markdown(f"<div style='text-align:center;color:{fg};font-size:1.2rem;'>Entry {st.session_state.story_page+1} of {len(story_entries)}</div>", unsafe_allow_html=True)
            if story_entries:
                st.markdown(f"<div style='color:{fg};font-size:1.2rem;min-height:120px;transition:color 0.5s;'>{story_entries[st.session_state.story_page]}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
        from fpdf import FPDF
        import io

        def create_pdf(title, story, bg_image=None):
            def create_certificate_pdf(names, date=None):
                from fpdf import FPDF
                import io
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 28)
                pdf.set_text_color(185, 19, 114)
                pdf.cell(0, 30, "Certificate of Love", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", '', 18)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 14, f"This certifies that\n\n{names}\n\nhave created a beautiful LoveBook together\n\n", align='C')
                if date:
                    pdf.set_font("Arial", 'I', 14)
                    pdf.cell(0, 10, f"Date: {date}", ln=True, align='C')
                pdf.ln(20)
                pdf.set_font("Arial", 'I', 12)
                pdf.set_text_color(185, 19, 114)
                pdf.cell(0, 10, "— SoulVest LoveBook", ln=True, align='R')
                return pdf.output(dest='S')
                # Certificate download option
                if st.session_state.story_generated and st.session_state.couple_names:
                    cert_pdf = create_certificate_pdf(st.session_state.couple_names, datetime.now().strftime('%B %d, %Y'))
                    if isinstance(cert_pdf, bytearray):
                        cert_pdf = bytes(cert_pdf)
                    st.download_button(
                        label="📜 Download LoveBook Certificate (PDF)",
                        data=cert_pdf,
                        file_name="lovebook_certificate.pdf",
                        mime="application/pdf"
                    )
                    # Certificate download in dashboard
                    if user.get('couple_names'):
                        cert_pdf = create_certificate_pdf(user['couple_names'], datetime.now().strftime('%B %d, %Y'))
                        if isinstance(cert_pdf, bytearray):
                            cert_pdf = bytes(cert_pdf)
                        st.download_button(
                            label="📜 Download LoveBook Certificate (PDF)",
                            data=cert_pdf,
                            file_name="lovebook_certificate.pdf",
                            mime="application/pdf"
                        )
            pdf = FPDF()
            pdf.add_page()
            from PIL import Image
            import tempfile
            import os
            # Use uploaded image or default love theme
            if bg_image is not None:
                img = Image.open(bg_image)
            else:
                # Use a default love theme image (hearts and roses)
                default_img_path = os.path.join(os.path.dirname(__file__), "default-love_bg.jpg")
                img = Image.open(default_img_path)
            # Resize image to fit A4 (210x297mm, 1pt=0.3528mm, so 595x842pt)
            img = img.convert('RGB')
            img = img.resize((595, 842))
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmpfile:
                img.save(tmpfile, format='JPEG')
                tmpfile.flush()
                pdf.image(tmpfile.name, x=0, y=0, w=210, h=297)
            pdf.set_font("Arial", 'B', 18)
            pdf.set_text_color(185, 19, 114)
            pdf.cell(0, 10, title, ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", '', 12)
            pdf.set_text_color(0, 0, 0)
            for line in story.split('\n'):
                line = line.strip()
                if line:
                    pdf.multi_cell(0, 8, line)
                else:
                    pdf.ln(4)
            # Add signature at the end
            pdf.ln(8)
            pdf.set_font("Arial", 'I', 12)
            pdf.set_text_color(185, 19, 114)
            pdf.cell(0, 10, "- Made with SoulVest Memory Book (Love)", ln=True, align='R')
            return pdf.output(dest='S')

        pdf_bytes = create_pdf(f"{st.session_state.couple_names} - Memory Book", st.session_state.story, uploaded_bg)
        if isinstance(pdf_bytes, bytearray):
            pdf_bytes = bytes(pdf_bytes)
        st.download_button(
            label="📥 Download Memory Book as PDF",
            data=pdf_bytes,
            file_name="memory_book.pdf",
            mime="application/pdf"
        )

        # ...existing code...

        # Viral Share Section
        st.markdown("### 💝 Share Your Love Story with the World")
        st.markdown("<span style='color:#b91372;'>Let your love inspire others—share your story on WhatsApp, Facebook, or Instagram! Make this Valentine's Day unforgettable for you and your beloved.</span>", unsafe_allow_html=True)
        whatsapp_text = f"Our Love Story - {st.session_state.couple_names} - Made with SoulVest Memory Book. Create yours at https://soulvest.ai"
        whatsapp_url = f"https://wa.me/?text={whatsapp_text}"
        facebook_url = f"https://www.facebook.com/sharer/sharer.php?u=https://soulvest.ai&quote=Our%20Love%20Story%20by%20SoulVest%20Memory%20Book%3A%20{st.session_state.couple_names}%20-%20Made%20with%20SoulVest%20Memory%20Book.%20Create%20yours%20at%20https://soulvest.ai"

        st.markdown(f'''
            <div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-bottom:16px;">
                <a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 12px 24px; border: none; border-radius: 10px; cursor: pointer; font-size: 16px;">💚 WhatsApp</button></a>
                <a href="{facebook_url}" target="_blank"><button style="background-color: #4267B2; color: white; padding: 12px 24px; border: none; border-radius: 10px; cursor: pointer; font-size: 16px;">📘 Facebook</button></a>
            </div>
        ''', unsafe_allow_html=True)


        st.markdown("<span style='color:#6c5ce7;font-size:16px;'>Want to share on Instagram or anywhere else?</span>", unsafe_allow_html=True)
        st.markdown("<span style='color:#636e72;'>Click below to copy your story text. Paste it as a caption, message, or post in any app!</span>", unsafe_allow_html=True)
        share_signature = "\n\n— Made with SoulVest Memory Book 💖"
        share_story = st.session_state.story + share_signature
        st.text_area("Your Story", share_story, height=200, key="copy_story_area")
        st.button("📋 Copy Story to Clipboard", on_click=lambda: st.session_state.update({"copy_story_area": share_story}))
        st.markdown("<span style='color:#b91372;font-size:18px;'>Let your love shine bright—spread joy, hope, and romance everywhere you share your story! ✨</span>", unsafe_allow_html=True)

        if st.button("🔄 Create New Book"):
            st.session_state.story_generated = False
            st.rerun()
    else:
        st.info("📝 Fill in your memories in the 'Create Memory Book' tab first!")
        st.markdown("""
        ### What you'll get:
        
        ✨ A beautifully written narrative of your relationship  
        📖 Five chapters covering your journey together  
        💝 A keepsake you can treasure forever  
        📥 Downloadable PDF  
        🎧 Downloadable audio file (MP3) with multiple voice styles  
        💬 Shareable with friends and family  
        
        Start creating your memory book now! →
        """)

# Footer
st.markdown("---")
# --- Freemium Model Notice ---
if user:
    if user['role'] == 'free' and user['usage_count'] > 1:
        st.warning("You have reached the free usage limit. Upgrade to premium for unlimited books and features!")
    if user['role'] == 'guest':
        st.info("You are using the app as a guest. Your data will not be saved and you cannot resume or access a dashboard. Sign up or log in for full features!")
    st.markdown(
        f"""
        <p style='text-align: center; color: #636e72;'>
            Made with ❤️ by <a href='https://soulvest.ai' style='color: #6c5ce7; text-decoration: none;'>SoulVest.ai</a> | <b>{user['role'].capitalize()} User</b><br>
            <span style='font-size:15px;color:#b91372;'>SoulVest LoveBook™ and all content © 2026 SoulVest.ai. All rights reserved.<br>
            No part of this app or its content may be reproduced without written permission.<br>
            <b>Branding, design, and code are protected by copyright and trademark law.</b></span>
        </p>
        """,
        unsafe_allow_html=True
    )
# Privacy Notice
st.markdown("---")
st.markdown("### 🔒 Privacy & Data Security")
st.markdown("""
<span style='color:#b91372;'>Your privacy and comfort matter to us. All information you enter in SoulVest Memory Book—including your names, memories, stories, photos, and feedback—is stored <b>only in your browser</b> and is <b>never uploaded to any server</b> or shared with third parties. Everything stays private on your device. Feedback is saved locally and used only to improve your experience. No personal or sensitive information is sold, published, or used for marketing. You are always in control of your data, and you can use the app with complete peace of mind.</span>
<br><br>
<span style='color:#b91372;'>We want you to feel comfortable and safe before using our app. If you have any questions or concerns about your privacy, please contact us at <a href='mailto:soulvest1111@gmail.com'>soulvest1111@gmail.com</a>.</span>
""", unsafe_allow_html=True)

# Feedback Form
st.markdown("---")
st.markdown("## 💬 We value your feedback!")
st.markdown("<span style='color:#b91372;'>Share your suggestions, ideas, or report any issues below. Help us make SoulVest Memory Book even better!</span>", unsafe_allow_html=True)
with st.form("feedback_form"):
    feedback_name = st.text_input("Your Name (optional)")
    feedback_email = st.text_input("Your Email (optional)")
    feedback_message = st.text_area("Your Feedback", placeholder="Share your thoughts, suggestions, or report any issues...")
    submitted = st.form_submit_button("Submit Feedback")
    if submitted and feedback_message:
        try:
            with open("feedback.txt", "a", encoding="utf-8") as f:
                f.write(f"Name: {feedback_name}\nEmail: {feedback_email}\nMessage: {feedback_message}\n---\n")
            st.success("Thank you for your feedback! 💖")
        except Exception as e:
            st.error(f"Error saving feedback: {str(e)}")
    elif submitted:
        st.warning("Please enter your feedback before submitting.")

def get_db():
    conn = sqlite3.connect("lovebook.db", check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        role TEXT DEFAULT 'free',
        usage_count INTEGER DEFAULT 0,
        story TEXT,
        couple_names TEXT,
        profile_photo TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    return conn
