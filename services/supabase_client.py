import os
import base64
import json
from functools import lru_cache
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError
from supabase import Client, create_client


load_dotenv()


def get_config_value(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value:
        return value

    try:
        return st.secrets.get(name)
    except (AttributeError, FileNotFoundError, KeyError, StreamlitSecretNotFoundError):
        return None


def is_service_role_key(key: str) -> bool:
    """Return True when the Supabase JWT payload identifies a service_role key."""
    try:
        payload = key.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("utf-8"))
        return json.loads(decoded).get("role") == "service_role"
    except (IndexError, ValueError, json.JSONDecodeError):
        return False


@lru_cache(maxsize=1)
def get_supabase() -> Optional[Client]:
    url = get_config_value("SUPABASE_URL")
    key = get_config_value("SUPABASE_KEY")

    if not url or not key:
        return None

    if is_service_role_key(key):
        st.error("SUPABASE_KEY não pode ser service_role. Use a chave pública anon.")
        return None

    try:
        return create_client(url, key)
    except Exception as exc:
        st.error(f"Não foi possível conectar ao Supabase: {exc}")
        return None
