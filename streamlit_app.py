import streamlit as st
import requests
import xml.etree.ElementTree as ET
from google import genai

# --- 1. CONFIGURATION ---
# These must be set in your Streamlit Cloud "Secrets" tab
WOLFRAM_ID = st.secrets["WOLFRAM_ID"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]
client = genai.Client(api_key=GEMINI_KEY)

# --- 2. WOLFRAM ENGINE (THE CALCULATOR) ---
def get_wolfram_steps(query):
    """Bypasses LLM math errors by fetching real steps from Wolfram."""
    url = f"https://api.wolframalpha.com/v2/query?input=show+steps+{query}&appid={WOLFRAM_ID}&format=plaintext"
    try:
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.text)
        steps = []
        for pod in root.findall('.//pod'):
            title = pod.get('title', '').lower()
            if 'step-by-step' in title or 'solution' in title:
                text = pod.find('.//plaintext').text
                if text: steps.append(text)
        return "\n".join(steps) if steps else "No automated steps found."
    except Exception:
        return "Verification engine offline."

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="Socratic Calc Tutor", page_icon="🎓")
st.title("🎓 Socratic Calculus Agent")
st.caption("Grounded in OpenStax Calculus Vol 1 & Wolfram Alpha")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. THE TUTORING LOOP ---
if prompt := st.chat_input("I'm stuck on the Chain Rule..."):
    # Store user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Background: Get the "Correct" steps
    hidden_truth = get_wolfram_steps(prompt)
    
    # Socratic System Instruction
    system_prompt = f"""
    ROLE: You are the 'OpenStax Calculus Tutor'.
    INTERNAL VERIFICATION (DO NOT SHOW USER): {hidden_truth}
    
    YOUR GOAL: 
    - Lead the student to the answer using Socratic questioning.
    - Never give the final answer or full steps at once.
    - Use OpenStax Vol 1 terminology (e.g.,
