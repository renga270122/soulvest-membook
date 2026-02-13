import streamlit as st

st.set_page_config(page_title="💖 Soulvest Memory Book Pricing", page_icon="💖")
st.title("💖 Soulvest Memory Book")
st.subheader("Preserve your memories forever")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Free Plan")
    st.write("""
    - Capture up to 10 memories
    - Basic journaling features
    - Share with loved ones
    """)
    st.button("Start Free", key="start_free")

with col2:
    st.markdown("#### Premium Plan (Coming Soon)")
    st.write("""
    ✨ Unlimited entries  
    ✨ Export to PDF/Word  
    ✨ Private cloud storage  
    ✨ AI-powered reflection prompts  
    """)
    st.button("Upgrade to Premium", key="upgrade_premium", disabled=True)

st.markdown("---")
st.markdown("**Start your free Memory Book today and gift yourself or your loved one timeless memories.**")
