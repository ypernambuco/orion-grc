import pandas as pd
import streamlit as st

from services.supabase_client import get_supabase
from services.ui import apply_theme, display_label, render_data_table, render_empty_state, render_hero, render_sidebar


st.set_page_config(page_title="ORION GRC | Documentos", layout="wide")

STATUS_OPTIONS = ["Vigente", "Pendente", "Vencido", "Em revisao"]
CATEGORY_OPTIONS = [
    "Contrato",
    "Politica",
    "Procedimento",
    "Controle",
    "Relatorio",
    "Fluxograma",
    "KPI",
    "Auditoria",
    "Juridico",
]


def load_areas() -> list[dict]:
    supabase = get_supabase()
    if supabase is None:
        return []
    try:
        return supabase.table("areas").select("id, nome").order("nome").execute().data
    except Exception as exc:
        st.error(f"Não foi possível carregar as áreas: {exc}")
        return []


def load_documentos() -> pd.DataFrame:
    supabase = get_supabase()
    if supabase is None:
        return pd.DataFrame()
    try:
        data = (
            supabase.table("documentos")
            .select("id, nome, categoria, responsavel, vencimento, status, areas(nome)")
            .order("vencimento")
            .execute()
            .data
        )
    except Exception as exc:
        st.error(f"Não foi possível carregar os documentos: {exc}")
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if not df.empty and "areas" in df:
        df["area"] = df["areas"].apply(
            lambda item: item.get("nome") if isinstance(item, dict) else "Sem área"
        )
    return df


apply_theme()
render_sidebar("Documentos")
render_hero(
    "Ciclo documental",
    "Gestão documental",
    (
        "Controle contratos, políticas, relatórios, evidências e documentos "
        "de auditoria com dono, vencimento e status operacional."
    ),
)

supabase = get_supabase()
areas = load_areas()
area_options = {area["nome"]: area["id"] for area in areas}

if supabase is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env ou em st.secrets.")

st.markdown("### Novo documento")
st.markdown(
    '<p class="orion-section">Registre itens que precisam de monitoramento, revisão ou evidência.</p>',
    unsafe_allow_html=True,
)
with st.form("form_documento", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    nome = col1.text_input("Nome")
    categoria = col2.selectbox("Categoria", CATEGORY_OPTIONS, format_func=display_label)
    area_nome = col3.selectbox(
        "Área",
        list(area_options.keys()) or ["Cadastre uma área primeiro"],
        format_func=display_label,
    )
    responsavel = col1.text_input("Responsável")
    vencimento = col2.date_input("Vencimento")
    status = col3.selectbox("Status", STATUS_OPTIONS, format_func=display_label)

    submitted = st.form_submit_button("Cadastrar documento")
    if submitted:
        if supabase is None:
            st.error("Supabase não configurado.")
        elif not area_options:
            st.error("Cadastre uma área antes de registrar documentos.")
        elif not nome.strip() or not responsavel.strip():
            st.error("Preencha nome e responsável.")
        else:
            try:
                supabase.table("documentos").insert(
                    {
                        "nome": nome.strip(),
                        "categoria": categoria,
                        "area_id": area_options[area_nome],
                        "responsavel": responsavel.strip(),
                        "vencimento": vencimento.isoformat(),
                        "status": status,
                    }
                ).execute()
                st.success("Documento cadastrado com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível cadastrar o documento: {exc}")

st.markdown("### Documentos cadastrados")
st.markdown(
    '<p class="orion-table-note">Visão operacional por área, responsável, vencimento e status.</p>',
    unsafe_allow_html=True,
)
with st.spinner("Carregando ciclo documental..."):
    documentos_df = load_documentos()
if documentos_df.empty:
    render_empty_state(
        "Nenhum documento cadastrado",
        "O ciclo documental ainda não possui itens monitorados. Registre contratos, políticas, evidências ou relatórios para acompanhar vencimentos e responsabilidades.",
        "Priorize documentos com vencimento recorrente ou impacto direto em auditoria e conformidade.",
    )
else:
    columns = ["id", "nome", "categoria", "area", "responsavel", "vencimento", "status"]
    render_data_table(documentos_df, columns)
