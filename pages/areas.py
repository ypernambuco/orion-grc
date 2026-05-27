import pandas as pd
import streamlit as st

from services.supabase_client import get_supabase
from services.ui import apply_theme, render_data_table, render_empty_state, render_hero, render_sidebar


st.set_page_config(page_title="ORION GRC | Áreas", layout="wide")


def load_areas() -> pd.DataFrame:
    supabase = get_supabase()
    if supabase is None:
        return pd.DataFrame()
    try:
        data = supabase.table("areas").select("*").order("nome").execute().data
    except Exception as exc:
        st.error(f"Não foi possível carregar as áreas: {exc}")
        return pd.DataFrame()
    return pd.DataFrame(data)


apply_theme()
render_sidebar("Áreas")
render_hero(
    "Unidades de governança",
    "Áreas corporativas",
    "Cadastre e acompanhe as áreas responsáveis por documentos, controles, riscos e pendências.",
)

supabase = get_supabase()
if supabase is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env ou em st.secrets.")

form_col, insight_col = st.columns([1.1, 0.9])
with form_col:
    st.markdown("### Nova área")
    st.markdown(
        '<p class="orion-section">Use áreas como responsáveis operacionais por documentos, controles e riscos.</p>',
        unsafe_allow_html=True,
    )
    with st.form("form_area", clear_on_submit=True):
        nome = st.text_input("Nome da área")
        submitted = st.form_submit_button("Cadastrar área")

        if submitted:
            if supabase is None:
                st.error("Supabase não configurado.")
            elif not nome.strip():
                st.error("Informe o nome da área.")
            else:
                try:
                    supabase.table("areas").insert({"nome": nome.strip()}).execute()
                    st.success("Área cadastrada com sucesso.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Não foi possível cadastrar a área: {exc}")

with insight_col:
    st.markdown("### Modelo da demonstração")
    st.markdown(
        '<p class="orion-section">'
        "A demonstração profissional usa Financeiro, Jurídico, RH, TI e Operações "
        "para mostrar governança por responsável."
        "</p>",
        unsafe_allow_html=True,
    )

st.markdown("### Áreas cadastradas")
st.markdown(
    '<p class="orion-table-note">Base de áreas usada nos filtros, formulários e indicadores.</p>',
    unsafe_allow_html=True,
)
with st.spinner("Carregando áreas corporativas..."):
    areas_df = load_areas()
if areas_df.empty:
    render_empty_state(
        "Nenhuma área cadastrada",
        "A base de governança ainda não possui áreas responsáveis. Cadastre as unidades operacionais para estruturar documentos, riscos e indicadores.",
        "Comece pela área responsável pelo maior volume de controles ou documentos críticos.",
    )
else:
    render_data_table(areas_df, ["id", "nome", "created_at"])
