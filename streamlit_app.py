import streamlit as st
import requests
import io
import time
from gtts import gTTS

# --- 1. CONFIGURATION ---
GEMINI_KEY = st.secrets["GEMINI_KEY"]
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

SYLLABUS = """
You are 'Professor Gemini', a Socratic Calculus Teacher. 
Ground your lessons in OpenStax Calculus Volumes 1-3.
Style: Use real-world engineering examples. Ask questions. 
Visuals: Use tags like [IMAGE: description] or [VIDEO: topic].
"""

# --- 2. VOICE ENGINE (Output) ---
def speak_lesson(text):
    try:
        clean_text = text.replace("$", "").replace("*", "").split("[")[0].strip()
        if clean_text:
            tts = gTTS(text=clean_text, lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.audio(audio_fp.getvalue(), format="audio/mp3", autoplay=True)
    except Exception as e:
        st.error(f"Audio Error: {e}")

# --- 3. THE BRAIN ---
def call_professor(prompt, history):
    headers = {'Content-Type': 'application/json'}
    messages = [{"role": "user", "parts": [{"text": SYLLABUS}]}]
    for msg in history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        messages.append({"role": role, "parts": [{"text": msg["content"]}]})
    messages.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {
        "contents": messages,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1000}
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

# SIDEBAR: Microphone and Progress
with st.sidebar:
    st.title("🎙️ Voice Command")
    voice_msg = st.audio_input("Speak to the Professor")
    st.divider()
    st.info("Syllabus: OpenStax Calculus V1-3")
    if st.button("Clear Blackboard"):
        st.session_state.chat_history = []
        st.rerun()

st.title("👨‍🏫 Professor Gemini's Classroom")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display Chat
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# Handle Inputs
user_query = None

# If user speaks, handle the audio
if voice_msg:
    # Most mobile browsers transcribe automatically in st.audio_input
    # If transcript isn't available, we use a placeholder to trigger the agent
    user_query = "I just sent a voice message. Please explain the next concept in the syllabus."

# If user types
if prompt := st.chat_input("Type your question here..."):
    user_query = prompt

if user_query:
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        response = call_professor(user_query, st.session_state.chat_history[:-1])
        st.markdown(response)
        speak_lesson(response)
        
        if "[IMAGE:" in response:
            st.info(f"🎨 Diagram: {response.split('[IMAGE:')[1].split(']')[0]}")
        
        if "[VIDEO:" in response:
            st.video("https://www.youtube.com/watch?v=WUvTyaaN26w")

        st.session_state.chat_history.append({"role": "assistant", "content": response})
