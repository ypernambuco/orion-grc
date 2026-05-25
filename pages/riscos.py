import pandas as pd
import streamlit as st

from services.supabase_client import get_supabase


st.set_page_config(page_title="ORION GRC | Riscos", layout="wide")


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
        return supabase.table("areas").select("id, nome").order("nome").execute().data
    except Exception as exc:
        st.error(f"Nao foi possivel carregar areas: {exc}")
        return []


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
        st.error(f"Nao foi possivel carregar riscos: {exc}")
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
st.subheader("Riscos")

supabase = get_supabase()
areas = load_areas()
area_options = {area["nome"]: area["id"] for area in areas}

if supabase is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env.")

with st.form("form_risco", clear_on_submit=True):
    area_nome = st.selectbox("Area", list(area_options.keys()) or ["Cadastre uma area primeiro"])
    descricao = st.text_area("Descricao")
    col1, col2, col3 = st.columns(3)
    probabilidade = col1.slider("Probabilidade", min_value=1, max_value=5, value=3)
    impacto = col2.slider("Impacto", min_value=1, max_value=5, value=3)
    risco = probabilidade * impacto
    classificacao = classify_risk(risco)
    col3.metric("Risco", f"{risco} - {classificacao}")

    submitted = st.form_submit_button("Cadastrar risco")
    if submitted:
        if supabase is None:
            st.error("Supabase nao configurado.")
        elif not area_options:
            st.error("Cadastre uma area antes de registrar riscos.")
        elif not descricao.strip():
            st.error("Informe a descricao do risco.")
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
                st.error(f"Nao foi possivel cadastrar o risco: {exc}")

st.markdown("### Riscos cadastrados")
riscos_df = load_riscos()
if riscos_df.empty:
    st.info("Nenhum risco cadastrado.")
else:
    columns = ["id", "area", "descricao", "probabilidade", "impacto", "risco", "classificacao"]
    st.dataframe(riscos_df[columns], use_container_width=True, hide_index=True)
