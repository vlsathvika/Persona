import streamlit as st
import json
from utils.chat_utils import query_groq
from utils.file_utils import load_persona_profiles, extract_text_from_file
from utils.prompt_templates import build_prompt
from fpdf import FPDF
import tempfile

st.set_page_config(page_title="Persona Bot", layout="wide")

# Load personas
with open("persona_data/icp_profiles.json", "r") as f:
    ICP_PROFILES = json.load(f)

with open("persona_data/brandience_profile.json", "r") as f:
    BRAND_PROFILES = json.load(f)

# Sidebar
mode = st.sidebar.radio("Select Mode", ["Current Brand Positioning", "Exploration Mode"])
profile_data = BRAND_PROFILES if mode == "Current Brand Positioning" else ICP_PROFILES 

# FIX: Handle different structures
if isinstance(profile_data, dict):
    persona_options = list(profile_data.keys())
else:
    persona_options = [p['name'] for p in profile_data]

persona_name = st.sidebar.selectbox("🎭 Choose a Persona", persona_options)

if isinstance(profile_data, dict):
    persona_data = profile_data[persona_name]
else:
    persona_data = next(p for p in profile_data if p['name'] == persona_name)

custom_context = st.sidebar.text_area("📝 Describe Idea (Exploration Mode Only)", "") if mode == "Exploration Mode" else ""
scenario = st.sidebar.selectbox("🎯 Scenario Type", [
    "General Q&A",
    "Messaging Tester",
    "Differentiation Analyzer",
    "Expectation Explorer",
    "Negotiation Simulator"
])

# File upload
st.sidebar.markdown("### 📎 Upload a file")
uploaded_file = st.sidebar.file_uploader("Attach a file (PDF or DOCX)", type=["pdf", "docx"])
file_context = ""
file_description = ""

if uploaded_file:
    st.sidebar.success(f"📄 `{uploaded_file.name}` attached.")
    file_description = st.sidebar.text_input("📝 Describe this file (optional):")
    file_context = extract_text_from_file(uploaded_file)

# Title
st.title("🤖 Persona Bot – Simulate Realistic Persona Conversations")

# Persona Summary
with st.expander("📄 Persona Summary"):
    st.markdown(f"**Description:** {persona_data.get('description', '_N/A in Exploration Mode_')}")
    goals = persona_data.get('Goals', persona_data.get('goals', []))
    if goals:
        st.markdown("**Goals:**\n- " + "\n- ".join(goals))

    pain_points = persona_data.get('Pain Points', persona_data.get('pain_points', []))
    if pain_points:
        st.markdown("**Pain Points:**\n- " + "\n- ".join(pain_points))

    style = persona_data.get('communication_style', persona_data.get('Style', 'N/A'))
    st.markdown(f"**Communication Style:** {style}")

    triggers = persona_data.get('triggers', [])
    if triggers:
        st.markdown("**Triggers for Engagement:**\n- " + "\n- ".join(triggers))

# Spacer
st.markdown("---")

# Chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])

# Chat input
user_input = st.chat_input("Type your message to the persona...")
if user_input:
    st.chat_message("user").write(user_input)
    full_prompt = build_prompt(
        persona_data=persona_data,
        user_input=user_input,
        file_context=file_context,
        file_description=file_description,
        scenario=scenario,
        brand_context=custom_context if mode == "Exploration Mode" else None
    )
    with st.spinner("🤔 Thinking like your persona..."):
        response = query_groq(full_prompt)
    st.chat_message("assistant").write(response)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "assistant", "content": response})

# Download chat as PDF
def generate_chat_pdf(history):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for msg in history:
        role = msg["role"].capitalize()
        pdf.multi_cell(0, 10, f"{role}:", border=0)
        pdf.multi_cell(0, 10, msg["content"], border=0)
        pdf.ln()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        pdf.output(tmp_file.name)
        return tmp_file.name
