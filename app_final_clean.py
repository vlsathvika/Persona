# app.py

import streamlit as st
import json
import os
from utils.chat_utils import query_groq
from utils.file_utils import extract_text_from_file
from utils.prompt_templates import build_prompt
from fpdf import FPDF
import tempfile

st.set_page_config(page_title="Persona Bot", layout="wide")

# Load JSON files
with open("persona_data/icp_profiles.json", "r") as f:
    ICP_PROFILES = json.load(f)

with open("persona_data/brandience_profile.json", "r") as f:
    BRAND_PROFILES = json.load(f)

with open("persona_data/role_profiles.json", "r") as f:
    ROLE_PROFILES = json.load(f)

# Mode selector
mode = st.sidebar.radio("Select Mode", ["Current Brand Positioning", "Exploration Mode"])
profile_data = BRAND_PROFILES if mode == "Current Brand Positioning" else ICP_PROFILES

# Persona options
if isinstance(profile_data, dict):
    persona_options = list(profile_data.keys())
else:
    persona_options = [p['name'] for p in profile_data]

persona_name = st.sidebar.selectbox("Choose a Persona", persona_options)

# Persona data
if isinstance(profile_data, dict):
    persona_data = profile_data[persona_name]
else:
    persona_data = next(p for p in profile_data if p['name'] == persona_name)

# Optional context
custom_context = st.sidebar.text_area("Describe Idea (Exploration Mode Only)", "") if mode == "Exploration Mode" else ""
scenario = st.sidebar.selectbox("Scenario Type", [
    "General Q&A",
    "Messaging Tester",
    "Differentiation Analyzer",
    "Expectation Explorer",
    "Negotiation Simulator"
])

# File upload
st.sidebar.markdown("Upload a file")
uploaded_file = st.sidebar.file_uploader("Attach a file (PDF or DOCX)", type=["pdf", "docx"])
file_context = ""
file_description = ""

if uploaded_file:
    st.sidebar.success(f"{uploaded_file.name} attached.")
    file_description = st.sidebar.text_input("Describe this file (optional):")
    file_context = extract_text_from_file(uploaded_file)

# UI Title
st.title("Persona Bot – Simulate Realistic Persona Conversations")

# Concise Persona Snapshot
role = ROLE_PROFILES.get(persona_name, {}).get('Roles', 'Marketing leader')
industry = ROLE_PROFILES.get(persona_name, {}).get('Industry', 'N/A')
style = persona_data.get('Style', persona_data.get('communication_style', 'N/A'))
summary = persona_data.get('description', 'Strategic marketing decision-maker')

st.markdown(f"""
> Chatting with: `{persona_name}`  
> {role} in {industry}  
> Style: {style}  
> Summary: {summary}
""")

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
        brand_context=custom_context if mode == "Exploration Mode" else None,
        role_data=ROLE_PROFILES
    )
    with st.spinner("Thinking like your persona..."):
        response = query_groq(full_prompt)
    st.chat_message("assistant").write(response)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "assistant", "content": response})

# PDF Export

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

if st.session_state.chat_history:
    if st.button("Download Chat as PDF"):
        pdf_path = generate_chat_pdf(st.session_state.chat_history)
        with open(pdf_path, "rb") as f:
            st.download_button("Click to Download", f, file_name="persona_chat_history.pdf")