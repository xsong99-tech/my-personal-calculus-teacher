import streamlit as st
import requests
import json
import time
from streamlit_tts import auto_play

# --- 1. SETTINGS & SYLLABUS ---
GEMINI_KEY = st.secrets["GEMINI_KEY"]
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

# This prompt "programs" the agent's teaching personality and syllabus
SYLLABUS_CONTEXT = """
You are 'Professor Gemini', a Socratic Calculus Teacher following the OpenStax Calculus Syllabus (Vols 1, 2, 3).
CLASSROOM RULES:
1. NEVER give the student the final answer. Ask questions to lead them there.
2. Ground explanations in REAL WORLD use (e.g., bridge engineering for derivatives, fluid dynamics for vectors).
3. Use tags for visuals:
   - [IMAGE: <description of a calculus diagram>]
   - [VIDEO: <YouTube URL or topic>]
4. Use Voice-friendly language (scannable, clear, not too many numbers at once).
5. Always end with a Socratic question.
"""

# --- 2. AGENT ENGINE ---
def call_professor(query, history):
    headers = {'Content-Type': 'application/json'}
    messages = [{"role": "user", "parts": [{"text": SYLLABUS_CONTEXT}]}]
    messages.append({"role": "model", "parts": [{"text": "Class is in session. I am ready to follow the OpenStax syllabus. What is our first topic?"}]})
    
    for msg in history[-6:]: # Maintain context of last 3 exchanges
        messages.append({"role": "user" if msg["role"] == "user" else "model", "parts": [{"text": msg["content"]}]})
    
    messages.append({"role": "user", "parts": [{"text": query}]})

    payload = {"contents": messages, "generationConfig": {"temperature": 0.4}}
    
    for attempt in range(3):
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            time.sleep(2 ** attempt)
    return "The professor is busy. Please try again in a moment."

# --- 3. CLASSROOM UI ---
st.set_page_config(page_title="AI Calculus Classroom", layout="wide")
st.title("👨‍🏫 Professor Gemini's Calculus Classroom")

# Sidebar Syllabus
with st.sidebar:
    st.header("OpenStax Syllabus")
    st.caption("Volume 1: Limits & Derivatives")
    st.caption("Volume 2: Integration & Series")
    st.caption("Volume 3: Multivariable & Vectors")
    st.divider()
    audio_query = st.audio_input("Ask a question with your voice")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display Lesson History
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# Handle Input (Voice or Text)
user_msg = None
if audio_query:
    user_msg = "Explain the visual intuition of a limit." # In a full app, you'd add Whisper STT here
if prompt := st.chat_input("Ex: Why do we use the chain rule in rocket science?"):
    user_msg = prompt

if user_msg:
    st.session_state.chat_history.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    with st.chat_message("assistant"):
        with st.spinner("Professor is preparing the lesson..."):
            response = call_professor(user_msg, st.session_state.chat_history[:-1])
            
            # 1. Clean response for Voice (strip tags)
            clean_text = response.split("[")[0].strip()
            
            # 2. Display text
            st.markdown(response)
            
            # 3. Audio Lesson
            auto_play(clean_text, lang='en')
            
            # 4. Trigger Visuals
            if "[IMAGE:" in response:
                img_query = response.split("[IMAGE:")[1].split("]")[0]
                st.info(f"🎨 Diagram: {img_query}")
                # Use a specific image tag for fetching
                st.write("")
                
            if "[VIDEO:" in response:
                video_url = response.split("[VIDEO:")[1].split("]")[0]
                st.video("https://www.youtube.com/watch?v=WUvTyaaN26w") # Standard example
                
            st.session_state.chat_history.append({"role": "assistant", "content": response})
