import streamlit as st
import requests
import json
import time

# --- 1. CONFIGURATION ---
GEMINI_KEY = st.secrets["GEMINI_KEY"]
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

# --- 2. THE BOOK'S TEACHING BRAIN ---
# We bake the 'Book's Knowledge' into the System Instruction
BOOK_CONTEXT = """
You are the 'OpenStax Calculus Tutor'. You follow the curriculum of Volumes 1, 2, and 3.
TEACHING STYLE:
1. NEVER solve the problem for the student.
2. Use Socratic questioning: Ask 'What is the limit as x approaches a?' instead of giving the limit.
3. Terminology: Use 'Difference Quotient' for derivatives, 'Riemann Sums' for integrals, and 'Partial Derivatives' for Calc 3.
4. Analogies: Use the 'Speedometer' analogy for derivatives and the 'Area under a fence' for integrals.
5. Progression: 
   - Calc 1: Limits, Derivatives, Integrals.
   - Calc 2: Sequences, Series, Integration Techniques.
   - Calc 3: Vectors, Multivariable, Vector Fields.
"""

def call_gemini_agent(user_prompt, history):
    headers = {'Content-Type': 'application/json'}
    
    # Construct the conversation with the 'Book Context' as the first message
    messages = [{"role": "user", "parts": [{"text": BOOK_CONTEXT}]}]
    messages.append({"role": "model", "parts": [{"text": "Understood. I am now the OpenStax Calculus Tutor. I will guide you step-by-step."}]})
    
    # Add conversation history
    for msg in history[-5:]: # Send last 5 messages to save tokens
        messages.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})
    
    # Add current prompt
    messages.append({"role": "user", "parts": [{"text": user_prompt}]})

    payload = {
        "contents": messages,
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1000}
    }

    # Retry logic for 429 Errors
    for attempt in range(3):
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            time.sleep(2 ** attempt) # Wait longer each time
        else:
            return f"Error {response.status_code}: {response.text}"
    return "The tutor is currently over-capacity. Please wait a moment."

# --- 3. STREAMLIT UI ---
st.set_page_config(page_title="Calculus AI Tutor", layout="wide")
st.title("📚 Calculus 1-2-3 Socratic Tutor")
st.sidebar.markdown("""
### Your Textbook
Grounded in **OpenStax Calculus**.
- **Vol 1:** Basic Change
- **Vol 2:** Infinite Series
- **Vol 3:** 3D Space
""")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display history
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# User Input
if prompt := st.chat_input("Ask about Limits, Integrals, or Vectors..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consulting the textbook..."):
            answer = call_gemini_agent(prompt, st.session_state.chat_history[:-1])
            st.markdown(answer)
            st.session_state.chat_history.append({"role": "model", "content": answer})
