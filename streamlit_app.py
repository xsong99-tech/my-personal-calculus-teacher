import streamlit as st
import google.generativeai as genai
import wolframalpha

# 1. Access Secrets from the Cloud
GENAI_KEY = st.secrets["GEMINI_KEY"]
WOLFRAM_ID = st.secrets["WOLFRAM_ID"]

# 2. Configure Engines
genai.configure(api_key=GENAI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
wa_client = wolframalpha.Client(WOLFRAM_ID)

st.set_page_config(page_title="Calculus Socratic Tutor", page_icon="🎓")
st.title("🎓 Calculus Tutor: Step-by-Step")

# 3. System Prompt for Socratic Teaching
SYSTEM_INSTRUCTION = """
You are a world-class Calculus Tutor. Follow these rules:
- Do NOT provide the final answer immediately.
- Use analogies (e.g., Derivatives are like a car's speedometer).
- Ask the user 'What do you think is the next step?' after explaining a concept.
- Use LaTeX for all math: e.g., $\int x^2 \, dx$.
"""

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Explain the Chain Rule to me..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_query = f"{SYSTEM_INSTRUCTION}\n\nUser Question: {prompt}"
        response = model.generate_content(full_query)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
