import streamlit as st
import requests
import matplotlib.pyplot as plt
import numpy as np

# --- 1. API CONFIGURATION ---
GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
WOLFRAM_APP_ID = st.secrets["WOLFRAM_ID"]

# Gemini REST Endpoint
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# Wolfram Alpha Short Answers Endpoint
WOLFRAM_URL = "http://api.wolframalpha.com/v1/result"

# --- 2. HELPER FUNCTIONS ---

def call_gemini(prompt):
    """Calls the Gemini API using the requests library."""
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(GEMINI_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"Error: {response.status_code} - {response.text}"

def call_wolfram(query):
    """Calls Wolfram Alpha using a GET request."""
    params = {
        "i": query,
        "appid": WOLFRAM_APP_ID
    }
    response = requests.get(WOLFRAM_URL, params=params)
    
    if response.status_code == 200:
        return response.text
    return "Could not compute math."

# --- 3. THE INTERFACE ---
st.title("🎓 Requests-Powered Calculus Tutor")

if "history" not in st.session_state:
    st.session_state.history = []

# Display Chat
for chat in st.session_state.history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# User Input Loop
if user_input := st.chat_input("Teach me about derivatives..."):
    st.session_state.history.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)

    # Brain Logic
    with st.chat_message("assistant"):
        # We tell the AI to behave Socratically
        socratic_prompt = f"""
        Act as a Socratic Calculus Teacher. 
        Explain concepts using real-world analogies. 
        User asks: {user_input}
        """
        
        # Call Gemini via Requests
        ai_response = call_gemini(socratic_prompt)
        st.markdown(ai_response)
        
        # Optional: Double check math with Wolfram if needed
        if "calculate" in user_input.lower():
            math_truth = call_wolfram(user_input)
            st.info(f"Verified Math: {math_truth}")

    st.session_state.history.append({"role": "assistant", "content": ai_response})
