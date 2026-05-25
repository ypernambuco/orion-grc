import pandas as pd
import streamlit as st

from services.supabase_client import get_supabase


st.set_page_config(page_title="ORION GRC | Documentos", layout="wide")

STATUS_OPTIONS = ["Vigente", "Pendente", "Vencido", "Em revisao"]
CATEGORY_OPTIONS = ["Politica", "Procedimento", "Norma", "Controle", "Relatorio", "Juridico"]


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


def load_areas() -> list[dict]:
    supabase = get_supabase()
    if supabase is None:
        return []
    try:
        return supabase.table("areas").select("id, nome").order("nome").execute().data
    except Exception as exc:
        st.error(f"Nao foi possivel carregar areas: {exc}")
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
        st.error(f"Nao foi possivel carregar documentos: {exc}")
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if not df.empty and "areas" in df:
        df["area"] = df["areas"].apply(
            lambda item: item.get("nome") if isinstance(item, dict) else "Sem area"
        )
    return df


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
st.subheader("Documentos")

supabase = get_supabase()
areas = load_areas()
area_options = {area["nome"]: area["id"] for area in areas}

if supabase is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env.")

with st.form("form_documento", clear_on_submit=True):
    col1, col2 = st.columns(2)
    nome = col1.text_input("Nome")
    categoria = col2.selectbox("Categoria", CATEGORY_OPTIONS)
    area_nome = col1.selectbox("Area", list(area_options.keys()) or ["Cadastre uma area primeiro"])
    responsavel = col2.text_input("Responsavel")
    vencimento = col1.date_input("Vencimento")
    status = col2.selectbox("Status", STATUS_OPTIONS)

    submitted = st.form_submit_button("Cadastrar documento")
    if submitted:
        if supabase is None:
            st.error("Supabase nao configurado.")
        elif not area_options:
            st.error("Cadastre uma area antes de registrar documentos.")
        elif not nome.strip() or not responsavel.strip():
            st.error("Preencha nome e responsavel.")
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
                st.error(f"Nao foi possivel cadastrar o documento: {exc}")

st.markdown("### Documentos cadastrados")
documentos_df = load_documentos()
if documentos_df.empty:
    st.info("Nenhum documento cadastrado.")
else:
    columns = ["id", "nome", "categoria", "area", "responsavel", "vencimento", "status"]
    st.dataframe(documentos_df[columns], use_container_width=True, hide_index=True)
