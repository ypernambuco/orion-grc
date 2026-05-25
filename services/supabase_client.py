import os
from functools import lru_cache
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client


load_dotenv()


def get_config_value(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value:
        return value

    try:
        return st.secrets.get(name)
    except (AttributeError, FileNotFoundError, KeyError):
        return None


@lru_cache(maxsize=1)
def get_supabase() -> Optional[Client]:
    url = get_config_value("SUPABASE_URL")
    key = get_config_value("SUPABASE_KEY")

    if not url or not key:
        return None

    return create_client(url, key)
