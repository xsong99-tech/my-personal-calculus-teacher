import streamlit as st
import requests
import io
import time
from gtts import gTTS

# --- 1. CONFIGURATION & SYLLABUS ---
GEMINI_KEY = st.secrets["GEMINI_KEY"]
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

# The "Professor's" personality and curriculum grounding
SYLLABUS = """
You are 'Professor Gemini', a Socratic Calculus Teacher following the OpenStax syllabus.
MISSION: Lead the student through Calculus 1, 2, and 3.
RULES:
1. Use Socratic questioning. Never give the full answer immediately.
2. Ground explanations in REAL WORLD use (e.g., Bridge stress, Fluid flow, AI Gradients).
3. Visuals: Use the tag [IMAGE: description] for graphs/diagrams.
4. Videos: Use the tag [VIDEO: topic] for animations.
5. Keep language concise for voice reading.
"""

# --- 2. THE VOICE ENGINE ---
def speak_lesson(text):
    try:
        # Clean the text of symbols that sound weird when spoken
        clean_text = text.replace("$", "").replace("*", "").split("[")[0].strip()
        if clean_text:
            tts = gTTS(text=clean_text, lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            # Standard Streamlit audio with autoplay
            st.audio(audio_fp.getvalue(), format="audio/mp3", autoplay=True)
    except Exception as e:
        st.error(f"Voice Error: {e}")

# --- 3. THE BRAIN (API CALL) ---
def call_professor(prompt, history):
    headers = {'Content-Type': 'application/json'}
    messages = [{"role": "user", "parts": [{"text": SYLLABUS}]}]
    messages.append({"role": "model", "parts": [{"text": "Class is in session. What shall we discover today?"}]})
    
    for msg in history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        messages.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    messages.append({"role": "user", "parts": [{"text": prompt}]})
    payload = {"contents": messages, "generationConfig": {"temperature": 0.4}}
    
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    return "The Professor is temporarily unavailable. Check your API key."

# --- 4. THE CLASSROOM UI ---
st.set_page_config(page_title="AI Calculus Classroom", layout="centered")
st.title("👨‍🏫 Professor Gemini's Classroom")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar for Progress
with st.sidebar:
    st.header("Classroom Settings")
    st.info("Currently following OpenStax Calculus Volumes 1-3.")
    if st.button("Clear Blackboard (Reset)"):
        st.session_state.chat_history = []
        st.rerun()

# Display Chat
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# User Input
if user_input := st.chat_input("Ask a question (e.g., 'What is the intuition behind a derivative?')"):
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Professor is thinking..."):
            response = call_professor(user_input, st.session_state.chat_history[:-1])
            st.markdown(response)
            
            # 1. Play Voice
            speak_lesson(response)
            
            # 2. Check for Image Triggers
            if "[IMAGE:" in response:
                img_desc = response.split("[IMAGE:")[1].split("]")[0]
                st.info(f"🎨 Diagram Suggestion: {img_desc}")
            
            # 3. Check for Video Triggers
            if "[VIDEO:" in response:
                st.video("https://www.youtube.com/watch?v=WUvTyaaN26w") # Essence of Calculus link
                
            st.session_state.chat_history.append({"role": "assistant", "content": response})
