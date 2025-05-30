import streamlit as st
from utils.prompt_templates import build_prompt
from utils.chat_utils import query_groq
from utils.file_utils import extract_text_from_file
from fpdf import FPDF
import json

# Load personas
with open("persona_data/icp_profiles.json", "r") as f:
    ICP_PROFILES = json.load(f)

with open("persona_data/brandience_profile.json", "r") as f:
    BRANDIENCE_PROFILES = json.load(f)

with open("persona_data/brandience_meta.json", "r") as f:
    BRAND_META = json.load(f)
# Password Protection
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        st.error("❌ Incorrect password")
        return False
    else:
        return True

if not check_password():
    st.stop()
# Set up the Streamlit page
st.set_page_config(page_title="Persona Bot by Brandience", layout="wide")
st.title("🤖 Persona Bot – Simulate Realistic Persona Conversations")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar: Mode + Persona selection
mode = st.sidebar.radio("Bot Mode", ["Current Brand Positioning", "Exploration Mode"])

if mode == "Current Brand Positioning":
    persona_options = [p["name"] for p in BRANDIENCE_PROFILES]
    persona_name = st.sidebar.selectbox("Choose a Persona", persona_options)
    persona_data = next(p for p in BRANDIENCE_PROFILES if p["name"] == persona_name)
    brand_context = BRAND_META
else:
    persona_options = list(ICP_PROFILES.keys())
    persona_name = st.sidebar.selectbox("Choose a Persona", persona_options)
    persona_data = ICP_PROFILES[persona_name]
    brand_context = None

custom_context = ""
if mode == "Exploration Mode":
    custom_context = st.sidebar.text_area("Describe what Brandience is exploring")

scenario = st.sidebar.selectbox(
    "Scenario",
    ["General Q&A", "Messaging Tester", "Differentiation Analyzer", "Expectation Explorer", "Negotiation Simulator"]
)

uploaded_file = st.sidebar.file_uploader("Upload a document for context", type=["pdf", "docx", "txt"])
file_description = st.sidebar.text_input("Describe the uploaded file")

# Persona Summary
with st.expander("📄 Persona Summary"):
    for key, val in persona_data.items():
        if isinstance(val, list):
            st.markdown(f"**{key}:**\n- " + "\n- ".join(val))
        else:
            st.markdown(f"**{key}:** {val}")

# Chat display
st.subheader("💬 Persona Chat")
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])

# Chat input
if user_input := st.chat_input("Ask the persona something or test a message"):
    st.chat_message("user").write(user_input)

    file_context = ""
    if uploaded_file:
        file_context = extract_text_from_file(uploaded_file)

    prompt = build_prompt(
        persona_data=persona_data,
        user_input=user_input,
        file_context=file_context,
        file_description=file_description,
        scenario=scenario,
        brand_context=brand_context if mode == "Current Brand Positioning" else custom_context
    )

    with st.spinner("Thinking like your persona..."):
        response = query_groq(prompt)

    st.chat_message("assistant").write(response)

    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "assistant", "content": response})

import re
import tempfile
from fpdf import FPDF

def force_wrap_unbreakable(text, max_word_len=100):
    return re.sub(r'(\S{%d})' % max_word_len, r'\1 ', text)

def sanitize_for_pdf(text):
    text = ''.join(char if 32 <= ord(char) <= 126 else ' ' for char in text)
    return force_wrap_unbreakable(text, 100)

def generate_chat_pdf(history):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for msg in history:
        role = msg["role"].capitalize()
        content = sanitize_for_pdf(msg["content"])

        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, f"{role}:", ln=True)

        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, content)
        pdf.ln()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        pdf.output(tmp_file.name)
        return tmp_file.name

if st.button("📄 Download Chat History as PDF") and st.session_state.chat_history:
    path = generate_chat_pdf(st.session_state.chat_history)
    with open(path, "rb") as f:
        st.download_button("Download PDF", f, file_name="persona_chat.pdf", mime="application/pdf")
