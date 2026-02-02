import streamlit as st
import google.generativeai as genai
import wolframalpha
import matplotlib.pyplot as plt
import numpy as np
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="AI Calculus Tutor", layout="wide")

# Get keys from Streamlit Secrets (for Cloud deployment)
GEMINI_KEY = st.secrets["GEMINI_KEY"]
WOLFRAM_ID = st.secrets["WOLFRAM_ID"]

# Initialize Engines
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
wa_client = wolframalpha.Client(WOLFRAM_ID)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_KEY)

# --- 2. THE LIBRARIAN (Book Search) ---
@st.cache_resource
def index_textbook():
    try:
        loader = PyPDFLoader("data/textbook.pdf")
        pages = loader.load_and_split()
        return Chroma.from_documents(pages, embeddings)
    except:
        st.warning("Textbook PDF not found in data/ folder. Using general knowledge mode.")
        return None

vector_db = index_textbook()

# --- 3. TEACHING MODES ---
def get_socratic_response(user_input, context=""):
    system_prompt = f"""
    You are a Socratic Calculus Tutor. 
    Reference the book content provided: {context}
    
    RULES:
    - Explain using real-world analogies (speedometers, mountains, leaky buckets).
    - NEVER give the final numerical answer immediately.
    - Ask a follow-up question to check the student's logic.
    - Use LaTeX for math like $\int x^2 dx$.
    """
    response = model.generate_content(system_prompt + "\nStudent: " + user_input)
    return response.text

# --- 4. THE INTERFACE ---
st.title("🎓 Your Socratic Calculus Tutor")
st.sidebar.markdown("### 📊 Learning Progress")
st.sidebar.progress(35) # Manual example

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask me about the Big Picture of Calculus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Search book for context
    book_context = ""
    if vector_db:
        docs = vector_db.similarity_search(prompt, k=2)
        book_context = "\n".join([d.page_content for d in docs])

    # Get Tutor Response
    with st.chat_message("assistant"):
        response_text = get_socratic_response(prompt, book_context)
        st.markdown(response_text)
        
        # Automatic Graphing Logic
        if "graph" in prompt.lower() or "plot" in prompt.lower():
            x = np.linspace(-10, 10, 100)
            y = x**2 # Simplified example; in pro version, LLM extracts formula
            fig, ax = plt.subplots()
            ax.plot(x, y)
            ax.set_title("Visualizing your Concept")
            st.pyplot(fig)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
