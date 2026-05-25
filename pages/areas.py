import pandas as pd
import streamlit as st

from services.supabase_client import get_supabase


st.set_page_config(page_title="ORION GRC | Areas", layout="wide")


def apply_theme() -> None:
    st.markdown(
        """
        <style>
            .stApp { background: #0f172a; color: #e5e7eb; }
            [data-testid="stSidebar"] { background: #020617; border-right: 1px solid #1e293b; }
            [data-testid="stSidebarNav"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_areas() -> pd.DataFrame:
    supabase = get_supabase()
    if supabase is None:
        return pd.DataFrame()
    try:
        data = supabase.table("areas").select("*").order("nome").execute().data
    except Exception as exc:
        st.error(f"Nao foi possivel carregar areas: {exc}")
        return pd.DataFrame()
    return pd.DataFrame(data)


apply_theme()

with st.sidebar:
    st.title("Vaekor Labs")
    st.caption("ORION GRC")
    st.divider()
    st.page_link("app.py", label="Inicio")
    st.page_link("pages/dashboard.py", label="Dashboard")
    st.page_link("pages/areas.py", label="Areas")
    st.page_link("pages/documentos.py", label="Documentos")
    st.page_link("pages/riscos.py", label="Riscos")

st.title("ORION GRC")
st.subheader("Areas")

supabase = get_supabase()
if supabase is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env.")

with st.form("form_area", clear_on_submit=True):
    nome = st.text_input("Nome da area")
    submitted = st.form_submit_button("Cadastrar area")

    if submitted:
        if supabase is None:
            st.error("Supabase nao configurado.")
        elif not nome.strip():
            st.error("Informe o nome da area.")
        else:
            try:
                supabase.table("areas").insert({"nome": nome.strip()}).execute()
                st.success("Area cadastrada com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Nao foi possivel cadastrar a area: {exc}")

st.markdown("### Areas cadastradas")
areas_df = load_areas()
if areas_df.empty:
    st.info("Nenhuma area cadastrada.")
else:
    st.dataframe(areas_df[["id", "nome", "created_at"]], use_container_width=True, hide_index=True)
