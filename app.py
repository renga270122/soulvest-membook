import streamlit as st
from fpdf import FPDF
from datetime import datetime
import base64

# Page config
st.set_page_config(
    page_title="SoulVest LoveBook 💖",
    page_icon="💖",
    layout="wide"
)

# --- Session State Initialization ---
if 'memories' not in st.session_state:
    st.session_state.memories = {}
if 'story_generated' not in st.session_state:
    st.session_state.story_generated = False
if 'start_date' not in st.session_state:
    st.session_state.start_date = None


# --- Image Upload for Background ---
uploaded_bg = None

bg_css = """
<style>
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
    </style>
    """, unsafe_allow_html=True)


st.title("💖 SoulVest LoveBook")
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

# Sidebar - About
    # File uploader already defined above; remove duplicate
import os
with st.sidebar:
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
    logo_path = os.path.join(os.path.dirname(__file__), "soulvest_logo.png")
    st.image(logo_path, width=120)
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
tab1, tab2 = st.tabs(["📝 Create Memory Book", "📖 View Your Story"])

with tab1:
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


    import tempfile
    import asyncio
    import edge_tts

    def tts_audio(text):
        try:
            async def _gen():
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tts_fp:
                    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
                    await communicate.save(tts_fp.name)
                    return tts_fp.name
            return asyncio.run(_gen())
        except Exception:
            return None

    col1, col2 = st.columns(2)
    with col1:
        st.write("Your Name")
        if st.button("🔊", key="tts_p1"):
            audio_file = tts_audio("Your Name")
            if audio_file:
                st.audio(audio_file, format='audio/mp3')
        person1_name = st.text_input("", key="p1", label_visibility="collapsed")
    with col2:
        st.write("Partner's Name")
        if st.button("🔊", key="tts_p2"):
            audio_file = tts_audio("Partner's Name")
            if audio_file:
                st.audio(audio_file, format='audio/mp3')
        person2_name = st.text_input("", key="p2", label_visibility="collapsed")


    # Redesigned, engaging questions for harmony and reconciliation
    questions = [
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
    ]

    answers = {}
    for idx, (q, ph, key, tip) in enumerate(questions):
        st.write(f"{idx+1}. {q}")
        st.caption(tip)
        if st.button("🔊", key=f"tts_{key}"):
            audio_file = tts_audio(q)
            if audio_file:
                st.audio(audio_file, format='audio/mp3')
        answers[key] = st.text_area("", placeholder=ph, key=f"ans_{key}", height=60, label_visibility="collapsed", help=None)

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
                    st.success("✨ Your memory book is ready!")
                    st.balloons()
                    st.info("Your story was crafted using your own beautiful memories and words. Go to the 'View Your Story' tab to see it and share the love!")

with tab2:
    if st.session_state.story_generated:
        st.markdown(f"## 📖 {st.session_state.couple_names}")
        if st.session_state.start_date:
            st.markdown(f"*Since {st.session_state.start_date.strftime('%B %d, %Y')}*")

        st.markdown(":sparkling_heart: <span style='color:#b91372;font-size:18px;'>Your story is safe here—ready to be shared, treasured, and celebrated. Love, after all, is the greatest story ever told.</span>", unsafe_allow_html=True)

        st.markdown("---")

        # Add a romantic quote above the story
        st.markdown("<div style='text-align:center; margin: 0 0 18px 0;'><span style='font-size:18px; color:#b91372; font-family:Georgia,serif; font-style:italic;'>\"Whatever our souls are made of, his and mine are the same.\"<br>– Emily Brontë</span></div>", unsafe_allow_html=True)

        # Display story (only in the main story section, not in the share section)


        # PDF Download Option
        from fpdf import FPDF
        import io

        def create_pdf(title, story, bg_image=None):
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

        # Local TTS Option using edge-tts
        st.markdown("---")
        st.markdown("### 🔊 Listen to Your Love Story (In-App)")
        st.markdown("<span style='color:#b91372;'>Click below to play your story audio safely inside the app.</span>", unsafe_allow_html=True)
        import tempfile
        import asyncio
        import edge_tts
        def story_tts_audio(text):
            try:
                async def _gen():
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tts_fp:
                        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
                        await communicate.save(tts_fp.name)
                        return tts_fp.name
                return asyncio.run(_gen())
            except Exception:
                return None
        if st.button("▶️ Play Story Audio", key="play_story_tts"):
            audio_file = story_tts_audio(st.session_state.story)
            if audio_file:
                st.audio(audio_file, format='audio/mp3')
            else:
                st.info("Text-to-speech is not available. Please ensure edge-tts is installed.")
        st.markdown("---")

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
        📥 Downloadable PDF (coming soon)  
        💬 Shareable with friends and family  
        
        Start creating your memory book now! →
        """)

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #636e72;'>Made with ❤️ by <a href='https://soulvest.ai' style='color: #6c5ce7; text-decoration: none;'>SoulVest.ai</a> | Free for Valentine's Week<br>"
    "&copy; 2026 SoulVest LoveBook. All rights reserved." 
    "</p>",
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
