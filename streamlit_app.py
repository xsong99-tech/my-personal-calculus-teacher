import streamlit as st
import requests
import json
import time

# --- 1. CONFIGURATION ---
GEMINI_KEY = st.secrets["GEMINI_KEY"]
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

# --- 2. THE AGENT'S BRAIN (SYSTEM INSTRUCTIONS) ---
SYSTEM_INSTRUCTIONS = """
You are the 'OpenStax Calculus Socratic Agent'. 
YOUR MISSION: Guide students through Calculus 1, 2, and 3 using discovery-based learning.
RULES:
1. NEVER provide a final numerical answer or a full solved derivative/integral immediately.
2. If a student is stuck, provide a HINT based on OpenStax definitions (e.g., 'Remember the definition of a limit as x approaches a').
3. Use analogies: Compare derivatives to a car's speedometer and integrals to the area of a fence.
4. Ask EXACTLY ONE probing question at the end of every response to keep the student thinking.
5. Format all math in LaTeX using $ symbols, like $\frac{dy}{dx} = 2x$.
6. **MULTIMODAL INSTRUCTION:**
   - If a concept is highly visual (e.g., Riemann sums, 3D graphs, tangent lines), suggest an image. To do this, output exactly: 
     <GENERATE_IMAGE: brief, clear description for the image generation model>
     This tag MUST be on its own line.
   - If a concept would benefit from a video explanation (e.g., Chain Rule animation, vector field flow), suggest a YouTube link. To do this, output exactly:
     <EMBED_VIDEO: YouTube_URL_here>
     This tag MUST be on its own line.
   - Prioritize images for static concepts and videos for dynamic, animated concepts.
"""

# --- 3. CORE AGENT LOGIC ---
def call_calculus_agent(user_query, history):
    headers = {'Content-Type': 'application/json'}
    
    contents = []
    contents.append({"role": "user", "parts": [{"text": f"SYSTEM: {SYSTEM_INSTRUCTIONS}"}]})
    contents.append({"role": "model", "parts": [{"text": "Understood. I am your Socratic Calculus Tutor. How can I help you discover calculus today?"}]})
    
    for chat in history[-6:]: 
        contents.append({"role": "user" if chat["role"] == "user" else "model", 
                         "parts": [{"text": chat["content"]}]})
    
    contents.append({"role": "user", "parts": [{"text": user_query}]})

    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 800}
    }

    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                time.sleep(2 ** (attempt + 1)) 
            else:
                return f"⚠️ API Error ({response.status_code}). Please check your API key."
        except Exception as e:
            return f"⚠️ Connection Error: {str(e)}"
    
    return "⚠️ The tutor is busy. Please try again in 30 seconds."

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="Calculus Agent", page_icon="🎓")
st.title("🎓 Socratic Calculus Agent")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("image_description"):
            st.markdown("Generating image based on AI's suggestion:")
            # Here, we output the special tag to trigger my image generation ability
            # In a real app, you would send this description to an image generation API
            st.markdown(f"**Image Request:** {message['image_description']}")
            
        if message.get("video_url"):
            st.markdown("Embedding video based on AI's suggestion:")
            st.video(message["video_url"])

# User interaction
if prompt := st.chat_input("Ex: Explain a tangent line with an image."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Tutor is consulting the textbook and preparing visuals..."):
            response_text = call_calculus_agent(prompt, st.session_state.messages[:-1])
            
            # --- PARSE FOR MULTIMODAL TAGS ---
            processed_response = response_text
            image_description = None
            video_url = None

            # Check for image tag
            if "<GENERATE_IMAGE:" in response_text:
                start = response_text.find("<GENERATE_IMAGE:") + len("<GENERATE_IMAGE:")
                end = response_text.find(">", start)
                if end != -1:
                    image_description = response_text[start:end].strip()
                    processed_response = response_text.replace(f"<GENERATE_IMAGE:{image_description}>", "").strip()
            
            # Check for video tag
            if "<EMBED_VIDEO:" in response_text:
                start = response_text.find("<EMBED_VIDEO:") + len("<EMBED_VIDEO:")
                end = response_text.find(">", start)
                if end != -1:
                    video_url = response_text[start:end].strip()
                    processed_response = processed_response.replace(f"<EMBED_VIDEO:{video_url}>", "").strip()

            st.markdown(processed_response) # Display text first

            if image_description:
                st.session_state.messages.append({"role": "assistant", "content": processed_response, "image_description": image_description})
                st.markdown(f"**Image Request:** {image_description}")
                # Trigger my internal image generation
                
            if video_url:
                st.session_state.messages.append({"role": "assistant", "content": processed_response, "video_url": video_url})
                st.video(video_url)
                
            if not image_description and not video_url: # If no multimodal content, just store the text
                 st.session_state.messages.append({"role": "assistant", "content": processed_response})
