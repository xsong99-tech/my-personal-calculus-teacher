import streamlit as st
import requests
import xml.etree.ElementTree as ET
from google import genai

# --- 1. SETUP ---
WOLFRAM_ID = st.secrets["WOLFRAM_ID"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]
client = genai.Client(api_key=GEMINI_KEY)

def get_wolfram_math(query):
    url = f"https://api.wolframalpha.com/v2/query?input={query}&appid={WOLFRAM_ID}&format=plaintext"
    try:
        root = ET.fromstring(requests.get(url).text)
        if root.get('success') == 'true':
            # Look for common calculus pod titles
            for pod in root.findall('.//pod'):
                if pod.get('title') in ['Derivative', 'Result', 'Indefinite integral', 'Limit']:
                    return pod.find('.//plaintext').text
    except:
        return None
    return None

# --- 2. STREAMLIT UI ---
st.title("Socratic Calculus Tutor 🎓")
st.write("I won't give you the answer, but I'll help you find it.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 3. TUTOR LOGIC ---
if prompt := st.chat_input("Ask a calculus question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Step A: Get ground-truth math from Wolfram
    correct_math = get_wolfram_math(prompt)

    # Step B: Generate Socratic response with Gemini
    with st.chat_message("assistant"):
        system_instruction = f"""
        You are a Socratic Calculus Tutor. 
        The student's question is: {prompt}
        The verified mathematical answer is: {correct_math}
        
        INSTRUCTIONS:
        1. Never reveal the verified answer directly.
        2. Use the verified answer to spot if the student is wrong.
        3. Ask a leading question about a rule (Power Rule, Chain Rule, etc.) to help them.
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=[system_instruction, prompt]
        )
        
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
