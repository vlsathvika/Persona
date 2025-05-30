import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def query_groq(prompt, model="llama3-70b-8192", temperature=0.7, max_tokens=800):
    if not client.api_key:
        raise ValueError("Missing GROQ_API_KEY environment variable.")

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a marketing decision-maker persona responding thoughtfully and professionally, simulating realistic buyer psychology."},
            {"role": "user", "content": prompt}
        ],
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return chat_completion.choices[0].message.content