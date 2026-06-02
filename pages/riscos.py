import pandas as pd
import streamlit as st

from services.supabase_client import get_supabase
from services.ui import (
    apply_theme,
    badge_html,
    display_label,
    filter_non_corporate_area_rows,
    is_non_corporate_area_name,
    render_data_table,
    render_empty_state,
    render_hero,
    render_sidebar,
)


st.set_page_config(page_title="ORION GRC | Riscos", layout="wide")


def classify_risk(score: int) -> str:
    if score <= 4:
        return "Baixo"
    if score <= 9:
        return "Medio"
    if score <= 15:
        return "Alto"
    return "Critico"


def load_areas() -> list[dict]:
    supabase = get_supabase()
    if supabase is None:
        return []
    try:
        data = supabase.table("areas").select("id, nome").order("nome").execute().data
    except Exception as exc:
        st.error(f"Não foi possível carregar as áreas: {exc}")
        return []
    return [
        area
        for area in data
        if not is_non_corporate_area_name(area.get("nome"))
    ]


def load_riscos() -> pd.DataFrame:
    supabase = get_supabase()
    if supabase is None:
        return pd.DataFrame()
    try:
        data = (
            supabase.table("riscos")
            .select("id, descricao, probabilidade, impacto, risco, classificacao, areas(nome)")
            .order("risco", desc=True)
            .execute()
            .data
        )
    except Exception as exc:
        st.error(f"Não foi possível carregar os riscos: {exc}")
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if not df.empty and "areas" in df:
        df["area"] = df["areas"].apply(
            lambda item: item.get("nome") if isinstance(item, dict) else "Sem área"
        )
    return filter_non_corporate_area_rows(df, "area")


apply_theme()
render_sidebar("Riscos")
render_hero(
    "Registro de riscos",
    "Matriz de riscos",
    (
        "Classifique riscos por probabilidade e impacto para priorizar "
        "controles internos, evidências e planos de resposta."
    ),
)

supabase = get_supabase()
areas = load_areas()
area_options = {area["nome"]: area["id"] for area in areas}

if supabase is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env ou em st.secrets.")

st.markdown("### Novo risco")
st.markdown(
    '<p class="orion-section">Registre eventos que podem afetar continuidade, conformidade ou eficiência.</p>',
    unsafe_allow_html=True,
)
with st.form("form_risco", clear_on_submit=True):
    area_nome = st.selectbox(
        "Área",
        list(area_options.keys()) or ["Cadastre uma área primeiro"],
        format_func=display_label,
    )
    descricao = st.text_area("Descrição")
    col1, col2, col3 = st.columns(3)
    probabilidade = col1.slider("Probabilidade", min_value=1, max_value=5, value=3)
    impacto = col2.slider("Impacto", min_value=1, max_value=5, value=3)
    risco = probabilidade * impacto
    classificacao = classify_risk(risco)
    with col3:
        st.metric("Score de risco", risco, display_label(classificacao), delta_color="off")
        st.markdown(badge_html(classificacao), unsafe_allow_html=True)

    submitted = st.form_submit_button("Cadastrar risco")
    if submitted:
        if supabase is None:
            st.error("Supabase não configurado.")
        elif not area_options:
            st.error("Cadastre uma área antes de registrar riscos.")
        elif not descricao.strip():
            st.error("Informe a descrição do risco.")
        else:
            try:
                supabase.table("riscos").insert(
                    {
                        "area_id": area_options[area_nome],
                        "descricao": descricao.strip(),
                        "probabilidade": probabilidade,
                        "impacto": impacto,
                        "risco": risco,
                        "classificacao": classificacao,
                    }
                ).execute()
                st.success("Risco cadastrado com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível cadastrar o risco: {exc}")

st.markdown("### Riscos cadastrados")
st.markdown(
    '<p class="orion-table-note">Priorização operacional calculada automaticamente pelo score.</p>',
    unsafe_allow_html=True,
)
with st.spinner("Carregando matriz de riscos..."):
    riscos_df = load_riscos()
if riscos_df.empty:
    render_empty_state(
        "Nenhum risco cadastrado",
        "A matriz ainda não possui eventos registrados. Cadastre riscos por área para criar uma visão executiva de exposição e priorização.",
        "Comece pelos eventos com maior impacto operacional, contratual ou regulatório.",
    )
else:
    columns = ["id", "area", "descricao", "probabilidade", "impacto", "risco", "classificacao"]
    render_data_table(riscos_df, columns)
