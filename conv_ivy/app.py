import os
import streamlit as st
import hashlib
import inspect
import base64
from streamlit_mic_recorder import mic_recorder
from src.brain import CareerBrain
from src.audio_utils import transcribe_audio
from src.reporter import generate_career_pdf

# -------------------------------
# Utility Functions
# -------------------------------

@st.cache_resource
def get_ivy_gif():
    gif = os.path.join(os.path.dirname(__file__), "assets", "Ivy_animation.gif") 
    with open(gif, "rb") as f:
        return base64.b64encode(f.read()).decode()

@st.cache_resource 
def load_css(): 
    css_path = os.path.join(os.path.dirname(__file__), "src", "styles.css")
    with open(css_path) as f:
        return f.read()

# -------------------------------
# UI Configuration
# -------------------------------
st.set_page_config(layout="wide", page_title="helloivy")
st.markdown(f"<style>{load_css()}</style>", unsafe_allow_html=True)

try:
    ivy_base64 = get_ivy_gif()
    ivy_img_html = f'<img src="data:image/gif;base64,{ivy_base64}" width="30" height="30" style="border-radius:50%;">'
except FileNotFoundError:
    ivy_img_html = "🌈"

# -------------------------------
# Session State Initialization
# -------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "scribe" not in st.session_state:
    st.session_state.scribe = {
        "name": "",
        "grade": "",
        "board": "",
        "interests": [],
        "strengths": [],
        "values": [],
        "work_environment": "",
        "goals": "",
        "paths": [],
        "count": 0,
    }

if not st.session_state.history:
    st.session_state.history.append({
        "role": "assistant",
        "content": "Hi! I'm Ivy. To start, what is your name, grade, and school board?"
    })

# Limit chat history length
MAX_HISTORY = 30
if len(st.session_state.history) > MAX_HISTORY:
    st.session_state.history = st.session_state.history[-MAX_HISTORY:]

brain = CareerBrain()

# -------------------------------
# UI Layout
# -------------------------------
col_chat, col_scribe = st.columns([0.6, 0.4])

with col_chat:
    st.markdown(f"**Chat with Ivy** — Milestone {min(st.session_state.scribe['count'], 8)}/8")

    # Render Chat History
    chat_html = ""
    for m in st.session_state.history:
        role, content = m["role"], m["content"]
        if role == "assistant":
            chat_html += inspect.cleandoc(f'''
                <div style="display:flex; gap:10px; margin-bottom:15px;">
                    <div style="font-size:20px">{ivy_img_html}</div>
                    <div style="background:#F3F4F6; padding:10px; border-radius:10px; max-width:85%; color:#1F2937;">{content}</div>
                </div>''')
        else:
            chat_html += inspect.cleandoc(f'''
                <div style="display:flex; justify-content:flex-end; gap:10px; margin-bottom:15px;">
                    <div style="background:#FFFFFF; border:1px solid #E5E7EB; padding:10px; border-radius:10px; max-width:85%; color:#1F2937;">{content}</div>
                    <div style="font-size:20px;">👤</div>
                </div>''')

    st.markdown(
        f'<div class="capture-card" style="height:450px; overflow-y:auto; border:1px solid #DDD; padding:15px; border-radius:15px;">{chat_html}</div>',
        unsafe_allow_html=True
    )

    # Audio Recording
    audio = mic_recorder(start_prompt="Speak to Ivy", stop_prompt="Stop", key='mic')
    if audio and audio.get('bytes'):
        ahash = hashlib.sha256(audio['bytes']).hexdigest()
        if st.session_state.get('last_hash') != ahash:
            st.session_state['last_hash'] = ahash
            user_text = transcribe_audio(audio['bytes'])

            # Free audio bytes immediately
            audio['bytes'] = None

            if user_text:
                st.session_state.history.append({"role": "user", "content": user_text})

                # Get response from Brain
                res = brain.get_response(user_text, st.session_state.scribe)

                # Update Scribe data
                updates = res.get('update_scribe', {})
                if updates:
                    for k, v in updates.items():
                        if isinstance(v, list):
                            existing = st.session_state.scribe.get(k, [])
                            st.session_state.scribe[k] = list(set(existing + v))
                        else:
                            st.session_state.scribe[k] = v
                    st.session_state.scribe['count'] += 1

                # Add Ivy's response to history
                st.session_state.history.append({"role": "assistant", "content": res['ai_speech']})

                # Rerun only when new info added
                st.rerun()

with col_scribe:
    st.markdown('<div class="scribe-panel" style="background:#F9FAFB; padding:20px; border-radius:15px; border:1px solid #EEE;">', unsafe_allow_html=True)
    st.subheader("📝 Live Discovery Scribe")
    s = st.session_state.scribe

    st.markdown(f"**Student Name:** {s['name'] or '...'}")
    st.markdown(f"**Grade:** {s['grade'] or '...'}")
    st.markdown(f"**Top Interests:** {', '.join(s['interests']) if s['interests'] else '...'}")
    st.markdown(f"**Key Strengths:** {', '.join(s['strengths']) if s['strengths'] else '...'}")
    st.markdown(f"**Core Values:** {', '.join(s['values']) if s['values'] else '...'}")
    st.markdown(f"**Preferred Work Environment:** {s['work_environment'] or '...'}")
    st.markdown(f"**Long-term Goals:** {s['goals'] or '...'}")
    st.markdown(f"**Recommended Paths:** {', '.join(s['paths']) if s['paths'] else '...'}")

    if st.button("Download Career Report", use_container_width=True):
        pdf = generate_career_pdf(s)
        st.download_button("Download PDF", pdf, "Career_Discovery.pdf")

    st.markdown('</div>', unsafe_allow_html=True)