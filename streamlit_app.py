import streamlit as st
import requests
import io
import time
from gtts import gTTS

# --- 1. CONFIGURATION & SYLLABUS ---
# Ensure GEMINI_KEY is set in Streamlit Cloud Secrets
GEMINI_KEY = st.secrets["GEMINI_KEY"]
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

SYLLABUS = """
You are 'Professor Gemini', a Socratic Calculus Teacher following the OpenStax syllabus.
MISSION: Lead the student through Calculus 1, 2, and 3.
RULES:
1. Use Socratic questioning. Never give the full answer immediately.
2. Ground explanations in REAL WORLD use (e.g., Engineering, Physics, AI).
3. Visuals: Use the tag [IMAGE: description] for graphs/diagrams.
4. Videos: Use the tag [VIDEO: topic] for animations.
5. Keep language concise for voice reading.
"""

# --- 2. THE VOICE ENGINE ---
def speak_lesson(text):
    try:
        # Strip markdown symbols so the voice doesn't say "star star" or "dollar sign"
        clean_text = text.replace("$", "").replace("*", "").replace("#", "").split("[")[0].strip()
        if clean_text:
            tts = gTTS(text=clean_text, lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            # Play with autoplay enabled for a classroom feel
            st.audio(audio_fp.getvalue(), format="audio/mp3", autoplay=True)
    except Exception as e:
        st.error(f"Voice Error: {e}")

# --- 3. THE BRAIN (API CALL) ---
def call_professor(prompt, history):
    headers = {'Content-Type': 'application/json'}
    
    # Constructing the message history
    messages = [{"role": "user", "parts": [{"text": SYLLABUS}]}]
    messages.append({"role": "model", "parts": [{"text": "Class is in session. What shall we discover today?"}]})
    
    for msg in history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        messages.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    messages.append({"role": "user", "parts": [{"text": prompt}]})

    # Defining the payload correctly before the request
    payload = {
        "contents": messages,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1000
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- 4. THE UI ---
st.set_page_config(page_title="AI Calculus Classroom", layout="centered")
st.title("👨‍🏫 Professor Gemini's Classroom")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar for Progress & Settings
with st.sidebar:
    st.header("Classroom Control")
    st.info("Syllabus: OpenStax Calculus (Vols 1-3)")
    if st.button("Reset Blackboard"):
        st.session_state.chat_history = []
        st.rerun()

# Display Chat History
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# User Input (Voice or Text)
if user_input := st.chat_input("Ask your Calculus question..."):
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Professor Gemini is drafting a response..."):
            response = call_professor(user_input, st.session_state.chat_history[:-1])
            st.markdown(response)
            
            # Trigger Voice
            speak_lesson(response)
            
            # Handle Visual Triggers
            if "[IMAGE:" in response:
                img_desc = response.split("[IMAGE:")[1].split("]")[0]
                st.info(f"💡 Visualization Tip: {img_desc}")
            
            if "[VIDEO:" in response:
                # Defaulting to 3Blue1Brown's Essence of Calculus for animations
                st.video("https://www.youtube.com/watch?v=WUvTyaaN26w")
                
            st.session_state.chat_history.append({"role": "assistant", "content": response})
