import streamlit as st
from fpdf import FPDF
from datetime import datetime
import base64
import google.generativeai as genai

# Page config
st.set_page_config(
    page_title="SoulVest Memory Book 📖",
    page_icon="📖",
    layout="wide"
)
# --- Session State Initialization ---
if 'memories' not in st.session_state:
    st.session_state.memories = {}
if 'story_generated' not in st.session_state:
    st.session_state.story_generated = False


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
        background: rgba(255,255,255,0.85);
    }}
    </style>
    """
    st.markdown(custom_bg, unsafe_allow_html=True)
else:
    st.markdown(bg_css, unsafe_allow_html=True)


# Move SoulVest Memory Book title to top, then welcome banner
st.title("💖 SoulVest Memory Book")
st.markdown("""
<div style='text-align:center;margin-top:24px;margin-bottom:8px;'>
    <span style='font-size:32px; color:#ee9ca7; font-family:Georgia,serif; font-weight:bold;'>
        Welcome to Your Digital Love Story 💞
    </span><br>
    <span style='font-size:20px; color:#b91372; font-family:Georgia,serif;'>
        Celebrate your journey, cherish your memories, and let your love shine brighter than ever this Valentine's Day!
    </span>
</div>
<div class="heart-beat" style="margin: 0 auto 18px auto; display: flex; justify-content: center;">
  <div class="heart-shape"></div>
</div>
""", unsafe_allow_html=True)
st.markdown("<span style='font-size:26px;color:#b91372;font-family:Georgia,serif;'>Every heartbeat, a memory. Every memory, a love story.</span>", unsafe_allow_html=True)
st.markdown(":sparkling_heart: <span style='font-size:20px;color:#b91372;'>Let your love blossom on this page—AI will turn your sweetest moments into a keepsake as timeless as your bond. Perfect for Valentine's Day, anniversaries, or any day you want to say 'I love you.'</span>", unsafe_allow_html=True)
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
with st.sidebar:
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    st.image("soulvest_logo.png", width=120)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<span class='sidebar-title'>SoulVest Memory Book</span>", unsafe_allow_html=True)
    # File uploader removed from sidebar; only appears in main content area
    st.markdown("---")
    # Removed duplicate Love Language Suggestions section
    st.markdown("### 💝 How it works")
    st.markdown("""
    1. **Fill in your memories** across different chapters
    2. **AI weaves them** into a beautiful narrative
    3. **Download** your memory book as PDF
    4. **Add more memories** anytime!

    Perfect for:
    - Valentine's Day gift
    - Anniversary surprise
    - Relationship milestone
    - Just because ❤️
    """)
    st.markdown("---")
    st.markdown("### 🤔 Do You Know?")
    st.markdown("<span style='color:#b91372;font-size:16px;'>Tips to impress your love partner:</span>", unsafe_allow_html=True)
    import random
    love_tips = [
        "Words of affirmation: Tell your partner how much they mean to you.",
        "Acts of service: Do something thoughtful for your loved one.",
        "Quality time: Spend uninterrupted moments together.",
        "Physical touch: A warm hug or gentle touch can say a lot.",
        "Gift giving: Surprise your partner with a meaningful gift.",
        "Write a love letter and share your feelings.",
        "Plan a romantic date night.",
        "Share a favorite memory and relive it together.",
        "Compliment your partner sincerely.",
        "Listen deeply and show you care."
    ]
    st.success(random.choice(love_tips))
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
    st.markdown("## Tell Us Your Story")
    uploaded_bg = st.file_uploader(
        "Upload your personal photo with your loved one (JPG/PNG, optional)",
        type=["jpg", "jpeg", "png"],
        help="Personalize your memory book with a photo of you and your loved one!",
        key="main_bg_upload"
    )
    st.info("Upload a photo with your loved one to make your memory book more special. JPG, JPEG, PNG formats supported.")
    # Basic Info
    st.markdown("### 💑 About You and Your Beloved")
    col1, col2 = st.columns(2)
    
    with col1:
        person1_name = st.text_input("Your Name:", key="p1")
        
    with col2:
        person2_name = st.text_input("Partner's Name:", key="p2")
    
    relationship_start = st.date_input(
        "When did your relationship start?",
        value=None,
        max_value=datetime.now()
    )
    
    st.markdown("---")
    
    # Chapter 1: How We Met
    st.markdown("### 🌹 Chapter 1: When Paths First Crossed")
    with st.expander("💌 Share your magical first meeting", expanded=True):
        how_met_where = st.text_input("Where did you meet?", placeholder="Coffee shop, college, online...")
        how_met_story = st.text_area(
            "Tell us the story:",
            placeholder="It was a rainy Tuesday afternoon...",
            height=120
        )
        first_impression = st.text_input(
            "First impression of each other?",
            placeholder="I thought they were..."
        )
    
    st.markdown("---")
    
    # Chapter 2: First Date
    st.markdown("### 🥂 Chapter 2: The First Date That Sparked Forever")
    with st.expander("💌 Relive your first date"):
        first_date_where = st.text_input("Where was your first date?")
        first_date_story = st.text_area(
            "What happened?",
            placeholder="We went to...",
            height=120
        )
        first_date_feeling = st.text_input(
            "How did it feel?",
            placeholder="I felt nervous but excited..."
        )
    
    st.markdown("---")
    
    # Chapter 3: Special Moments
    st.markdown("### ✨ Chapter 3: Cherished Moments & Milestones")
    with st.expander("💌 Recall your most beautiful memories"):
        favorite_memory = st.text_area(
            "Most cherished memory together:",
            placeholder="That time we...",
            height=120
        )
        funniest_moment = st.text_area(
            "Funniest moment:",
            placeholder="We still laugh about...",
            height=120
        )
        milestone_moment = st.text_area(
            "A milestone moment:",
            placeholder="When we moved in together, got engaged, traveled together...",
            height=120
        )
    
    st.markdown("---")
    
    # Chapter 4: Challenges
    st.markdown("### 💪 Chapter 4: Weathering Storms, Growing Stronger")
    with st.expander("💌 Share how love helped you overcome challenges (optional)"):
        challenge_faced = st.text_area(
            "A challenge you overcame together:",
            placeholder="Long distance, tough times, disagreements...",
            height=120
        )
        what_learned = st.text_input(
            "What did you learn?",
            placeholder="We learned that..."
        )
    
    st.markdown("---")
    
    # Chapter 5: Future Dreams
    st.markdown("### 🌟 Chapter 5: Dreams for Tomorrow, Together")
    with st.expander("💌 Paint your shared dreams"):
        future_dreams = st.text_area(
            "What do you dream about together?",
            placeholder="We want to travel to..., build a home..., start a family...",
            height=120
        )
        why_together = st.text_input(
            "In one sentence, why are you perfect together?",
            placeholder="Because we..."
        )
    
    st.markdown("---")
    

    # Generate button
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("✨ Generate Our Memory Book", use_container_width=True):
            required_fields = [
                person1_name, person2_name, how_met_story,
                first_date_story, favorite_memory
            ]
            if not all(required_fields):
                st.error("⚠️ Please fill in at least: Names, How We Met, First Date, and One Special Memory")
            else:
                with st.spinner("Creating your beautiful memory book... 📖"):
                    try:
                        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                        model = genai.GenerativeModel("gemini-pro")
                        prompt = f"""
You are creating a beautiful, heartfelt memory book for a couple. Write it as a cohesive narrative story, not as answers to questions.

HOW THEY MET:
Location: {how_met_where}
Story: {how_met_story}
First impressions: {first_impression}

FIRST DATE:
Location: {first_date_where}
What happened: {first_date_story}
How it felt: {first_date_feeling}

SPECIAL MOMENTS:
Favorite memory: {favorite_memory}
Funniest moment: {funniest_moment}
Milestone: {milestone_moment}

CHALLENGES:
Challenge faced: {challenge_faced if challenge_faced else 'Not mentioned'}
What they learned: {what_learned if what_learned else 'Not mentioned'}

DREAMS:
Future together: {future_dreams}
Why perfect together: {why_together}

Write this as a beautiful, flowing narrative in 5 chapters. Make it:
- Personal and authentic (use their actual details)
- Warm and heartfelt
- Like a story someone would treasure forever
- 600-800 words total
- Use their names naturally throughout

Format each chapter with a title, then the narrative.

Chapter 1: When Our Eyes First Met
Chapter 2: The First Date That Changed Everything
Chapter 3: Moments That Define Us
Chapter 4: Growing Stronger Together
Chapter 5: The Future We're Building

Write only the story, nothing else.
"""
                        response = model.generate_content(prompt)
                        story = response.text
                        st.session_state.story = story
                        st.session_state.story_generated = True
                        st.session_state.couple_names = f"{person1_name} & {person2_name}"
                        st.session_state.start_date = relationship_start
                        st.success("✨ Your memory book is ready!")
                        st.balloons()
                        st.info("Your story was crafted with the help of Google Gemini AI, blending your memories into a unique keepsake. Go to the 'View Your Story' tab to see it and share the love!")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.info("💡 Make sure your Gemini API key is set correctly.")

with tab2:
    if st.session_state.story_generated:
        st.markdown(f"## 📖 {st.session_state.couple_names}")
        if st.session_state.start_date:
            st.markdown(f"*Since {st.session_state.start_date.strftime('%B %d, %Y')}*")

        st.markdown(":sparkling_heart: <span style='color:#b91372;font-size:18px;'>Your story is safe here—ready to be shared, treasured, and celebrated. Love, after all, is the greatest story ever told.</span>", unsafe_allow_html=True)

        st.markdown("---")

        # Add a romantic quote above the story
        st.markdown("<div style='text-align:center; margin: 0 0 18px 0;'><span style='font-size:18px; color:#b91372; font-family:Georgia,serif; font-style:italic;'>\"Whatever our souls are made of, his and mine are the same.\"<br>– Emily Brontë</span></div>", unsafe_allow_html=True)

        # Display story
        st.markdown(f'<div class="story-text">{st.session_state.story}</div>', unsafe_allow_html=True)

        # TTS Option
        st.markdown("---")
        st.markdown("### 🔊 Listen to Your Love Story")
        st.markdown("<span style='color:#b91372;'>Click below to hear your story read aloud (uses your browser's voice).</span>", unsafe_allow_html=True)
        tts_script = f"""
        <script>
        function speakStory() {{
            var story = `{st.session_state.story}`;
            var utter = new SpeechSynthesisUtterance(story);
            utter.rate = 1;
            utter.pitch = 1.1;
            utter.lang = 'en-US';
            window.speechSynthesis.speak(utter);
        }}
        </script>
        <button onclick='speakStory()' style='background:#ff6a88;color:white;padding:12px 32px;border:none;border-radius:12px;font-size:18px;font-family:Georgia,serif;margin-top:8px;'>❤️ Play Story Audio</button>
        """
        st.markdown(tts_script, unsafe_allow_html=True)

        st.markdown("---")

        # Viral Share Section
        st.markdown("### 💝 Share Your Love Story with the World")
        st.markdown("<span style='color:#b91372;'>Let your love inspire others—share your story on WhatsApp, Facebook, or Instagram! Make this Valentine's Day unforgettable for you and your beloved.</span>", unsafe_allow_html=True)
        whatsapp_text = f"Our Love Story - {st.session_state.couple_names}%0A%0A{st.session_state.story[:500]}...%0A%0ACreated with SoulVest Memory Book"
        whatsapp_url = f"https://wa.me/?text={whatsapp_text}"
        facebook_url = f"https://www.facebook.com/sharer/sharer.php?u=https://soulvest.ai&quote=Our%20Love%20Story%20by%20SoulVest%20Memory%20Book%3A%20{st.session_state.couple_names}%20%F0%9F%92%97%20{st.session_state.story[:200]}..."

        st.markdown(f'''
            <div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-bottom:16px;">
                <a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 12px 24px; border: none; border-radius: 10px; cursor: pointer; font-size: 16px;">💚 WhatsApp</button></a>
                <a href="{facebook_url}" target="_blank"><button style="background-color: #4267B2; color: white; padding: 12px 24px; border: none; border-radius: 10px; cursor: pointer; font-size: 16px;">📘 Facebook</button></a>
            </div>
        ''', unsafe_allow_html=True)

        st.markdown("<span style='color:#6c5ce7;font-size:16px;'>Want to share on Instagram?</span>", unsafe_allow_html=True)
        st.markdown("<span style='color:#636e72;'>Copy your story below and paste it as a caption or story in the Instagram app. Add a beautiful photo for extra impact!</span>", unsafe_allow_html=True)
        if st.button("📋 Copy Story for Instagram"):
            st.code(st.session_state.story, language=None)
            st.info("Story copied! Open Instagram and paste as your caption or story text.")

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
    "&copy; 2026 SoulVest Memory Book. All rights reserved." 
    "</p>",
    unsafe_allow_html=True
)

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
