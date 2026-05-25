import pandas as pd
import streamlit as st

from services.supabase_client import get_supabase
from services.ui import apply_theme, render_hero, render_sidebar


st.set_page_config(page_title="ORION GRC | Areas", layout="wide")


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
render_sidebar("Areas")
render_hero(
    "Governance Units",
    "Areas corporativas",
    "Cadastre e acompanhe as areas responsaveis por documentos, controles, riscos e pendencias.",
)

supabase = get_supabase()
if supabase is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env ou em st.secrets.")

form_col, insight_col = st.columns([1.1, 0.9])
with form_col:
    st.markdown("### Nova area")
    st.markdown(
        '<p class="orion-section">Use areas como donos operacionais de documentos e riscos.</p>',
        unsafe_allow_html=True,
    )
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

with insight_col:
    st.markdown("### Modelo demo")
    st.markdown(
        '<p class="orion-section">'
        "A demo profissional usa Financeiro, Juridico, RH, TI e Operacoes "
        "para mostrar governanca por responsavel."
        "</p>",
        unsafe_allow_html=True,
    )

st.markdown("### Areas cadastradas")
st.markdown(
    '<p class="orion-table-note">Base de areas usada nos filtros, formularios e indicadores.</p>',
    unsafe_allow_html=True,
)
areas_df = load_areas()
if areas_df.empty:
    st.info("Nenhuma area cadastrada.")
else:
    st.dataframe(areas_df[["id", "nome", "created_at"]], use_container_width=True, hide_index=True)
