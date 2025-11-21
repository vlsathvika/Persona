import time
import logging
import openai
import streamlit as st

# Initialize OpenAI client using Streamlit secrets
if "openai" not in st.secrets:
    raise ValueError("Missing OpenAI API key in Streamlit secrets (st.secrets['openai']).")

try:
    # older openai package expects openai.api_key
    openai.api_key = st.secrets["openai"]
except Exception:
    # newer OpenAI client may prefer a client instance (we'll handle below)
    pass

logger = logging.getLogger(__name__)


def _extract_content(resp):
    # Try several common response shapes
    try:
        # new-style: choices[0].message.content
        return resp.choices[0].message.content
    except Exception:
        pass
    try:
        # dict-like: choices[0]['message']['content']
        return resp.choices[0]["message"]["content"]
    except Exception:
        pass
    try:
        # older ChatCompletion: choices[0].text
        return resp.choices[0].text
    except Exception:
        pass
    # Fallback: stringify whole response
    return str(resp)


def query_openai(prompt, model="gpt4o", temperature=0.7, max_tokens=800, retries=3, backoff=1.0):
    """
    Query OpenAI with a compatibility wrapper that supports multiple SDK shapes.

    This version will attempt the requested model first and then fall back to
    a small list of safe alternatives (e.g. gpt-4, gpt-3.5-turbo) if the model
    is not available for your account.
    """

    messages = [
        {"role": "system", "content": "You are a marketing decision-maker persona responding thoughtfully and professionally, simulating realistic buyer psychology."},
        {"role": "user", "content": prompt}
    ]

    # Build candidate models: prefer the requested model, then fallbacks
    fallback_candidates = ["gpt-4", "gpt-3.5-turbo"]
    model_candidates = [model] + [m for m in fallback_candidates if m != model]

    overall_errors = []

    for candidate in model_candidates:
        last_exc = None
        for attempt in range(1, retries + 1):
            try:
                # 1) Preferred: Use new OpenAI client (openai.OpenAI) when available
                OpenAI = getattr(openai, "OpenAI", None)
                if OpenAI is not None:
                    client = OpenAI(api_key=st.secrets.get("openai"))
                    chat_attr = getattr(client, "chat", None)
                    if chat_attr is not None:
                        comps = getattr(chat_attr, "completions", None)
                        if comps is not None and hasattr(comps, "create"):
                            resp = comps.create(model=candidate, messages=messages, temperature=temperature, max_tokens=max_tokens)
                            return _extract_content(resp)

                # 2) Try module-level namespacing: openai.chat.completions.create
                chat_mod = getattr(openai, "chat", None)
                if chat_mod is not None:
                    comps = getattr(chat_mod, "completions", None)
                    if comps is not None and hasattr(comps, "create"):
                        resp = comps.create(model=candidate, messages=messages, temperature=temperature, max_tokens=max_tokens)
                        return _extract_content(resp)

                # 3) Try resources path (older or alternate SDK layouts)
                resources = getattr(openai, "resources", None)
                if resources is not None:
                    chat_res = getattr(resources, "chat", None)
                    if chat_res is not None:
                        comps = getattr(chat_res, "completions", None)
                        if comps is not None and hasattr(comps, "create"):
                            resp = comps.create(model=candidate, messages=messages, temperature=temperature, max_tokens=max_tokens)
                            return _extract_content(resp)

                # If none of the above call paths exist, raise to trigger retry/fallback
                raise AttributeError("No supported OpenAI chat completion method found on the installed openai package.")

            except Exception as exc:
                last_exc = exc
                logger.exception("OpenAI call failed for model '%s' on attempt %s: %s", candidate, attempt, exc)
                # If this error obviously indicates the model isn't available, break
                msg = str(exc).lower()
                if "model" in msg and ("not found" in msg or "does not exist" in msg or "model_not_found" in msg or "model not found" in msg):
                    overall_errors.append(f"Model '{candidate}' unavailable: {exc}")
                    break
                if attempt < retries:
                    time.sleep(backoff * attempt)
                    continue
                overall_errors.append(f"Model '{candidate}' failed after {retries} attempts: {exc}")
                # try next candidate
                break

    # If we reach here, no candidate succeeded
    combined = " | ".join(overall_errors) if overall_errors else "Unknown error"
    return f"OpenAI request failed for all candidate models. Details: {combined}"
