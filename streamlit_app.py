import streamlit as st
import requests
import io
import re
from gtts import gTTS

# --- 1. CONFIGURATION ---
GEMINI_KEY = st.secrets["GEMINI_KEY"]
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

SYLLABUS = """
You are 'Professor Gemini', a Socratic Calculus Teacher.
1. Use LaTeX for math, enclosed in double dollar signs (e.g., $$f(x)=x^2$$).
2. To show a diagram, use the exact tag: [IMAGE: description]
3. To show a video, use the exact tag: [VIDEO: topic]
"""

# --- 2. THE VOICE ENGINE ---
def speak_lesson(text):
    try:
        # Clean text for speech
        clean_text = re.sub(r'\[.*?\]', '', text) # Remove [IMAGE/VIDEO] tags
        clean_text = clean_text.replace("$", "").strip()
        if clean_text:
            tts = gTTS(text=clean_text, lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.audio(audio_fp.getvalue(), format="audio/mp3", autoplay=True)
    except Exception as e:
        st.error(f"Voice Error: {e}")

# --- 3. THE MOBILE RENDERING ENGINE ---
def render_content(text):
    # 1. Handle Math (LaTeX) and Text
    # Splitting by $$ to find math blocks
    parts = re.split(r'(\$\$.*?\$\$)', text, flags=re.DOTALL)
    for part in parts:
        if part.startswith("$$") and part.endswith("$$"):
            st.latex(part.strip("$"))
        else:
            # 2. Handle Image Tags
            if "[IMAGE:" in part:
                desc = part.split("[IMAGE:")[1].split("]")[0]
                st.image("https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=1000", caption=desc)
            # 3. Handle Video Tags
            elif "[VIDEO:" in part:
                st.video("https://www.youtube.com/watch?v=WUvTyaaN26w")
            else:
                st.write(part)

# --- 4. THE BRAIN ---
def call_professor(prompt, history):
    messages = [{"role": "user", "parts": [{"text": SYLLABUS}]}]
    for msg in history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        messages.append({"role": role, "parts": [{"text": msg["content"]}]})
    messages.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {"contents": messages, "generationConfig": {"temperature": 0.4}}
    try:
        response = requests.post(API_URL, json=payload)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "The Professor is unavailable. Check your internet and API Key."

# --- 5. MOBILE UI ---
st.set_page_config(page_title="Calc Tutor", layout="centered")

with st.sidebar:
    st.title("🎙️ Controls")
    voice_msg = st.audio_input("Speak to Professor")
    if st.button("Reset Blackboard"):
        st.session_state.chat_history = []
        st.rerun()

st.title("👨‍🏫 Professor Gemini")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        render_content(chat["content"])

if prompt := st.chat_input("Ask about Limits, Derivatives, or Integrals..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        response = call_professor(prompt, st.session_state.chat_history[:-1])
        render_content(response)
        speak_lesson(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
