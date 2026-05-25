import pandas as pd
import plotly.express as px
import streamlit as st

from services.supabase_client import get_supabase


st.set_page_config(page_title="ORION GRC | Dashboard", layout="wide")


def apply_theme() -> None:
    st.markdown(
        """
        <style>
            .stApp { background: #0f172a; color: #e5e7eb; }
            [data-testid="stSidebar"] { background: #020617; border-right: 1px solid #1e293b; }
            [data-testid="stSidebarNav"] { display: none; }
            div[data-testid="stMetric"] {
                background: #111827;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 18px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def classify_expired(df: pd.DataFrame) -> pd.Series:
    if df.empty or "vencimento" not in df:
        return pd.Series(dtype=bool)
    vencimentos = pd.to_datetime(df["vencimento"], errors="coerce").dt.date
    return vencimentos < pd.Timestamp.today().date()


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    supabase = get_supabase()
    if supabase is None:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    try:
        areas = supabase.table("areas").select("*").order("nome").execute().data
        documentos = (
            supabase.table("documentos")
            .select("*, areas(nome)")
            .order("vencimento")
            .execute()
            .data
        )
        riscos = (
            supabase.table("riscos")
            .select("*, areas(nome)")
            .order("risco", desc=True)
            .execute()
            .data
        )
    except Exception as exc:
        st.error(f"Nao foi possivel carregar dados do Supabase: {exc}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    return pd.DataFrame(areas), pd.DataFrame(documentos), pd.DataFrame(riscos)


def normalize_area_name(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "areas" not in df:
        return df
    df = df.copy()
    df["area"] = df["areas"].apply(
        lambda item: item.get("nome") if isinstance(item, dict) else "Sem area"
    )
    return df


def build_area_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "area" not in df or "status" not in df:
        return pd.DataFrame()

    df = df.copy()
    df["vencido"] = classify_expired(df)
    df["pendente"] = df["status"].fillna("").str.lower().eq("pendente")
    df["fora_do_fluxo"] = df["vencido"] | df["pendente"]

    grouped = (
        df.groupby("area", as_index=False)
        .agg(total=("id", "count"), fora_do_fluxo=("fora_do_fluxo", "sum"))
    )
    grouped["eficiencia"] = (
        ((grouped["total"] - grouped["fora_do_fluxo"]) / grouped["total"]) * 100
    ).round(1)
    return grouped.sort_values("eficiencia", ascending=False)


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
st.subheader("Dashboard executivo")

areas_df, documentos_df, riscos_df = load_data()
documentos_df = normalize_area_name(documentos_df)
riscos_df = normalize_area_name(riscos_df)

if get_supabase() is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env para carregar dados.")

expired_mask = classify_expired(documentos_df)
documentos_vencidos = int(expired_mask.sum()) if not documentos_df.empty else 0
pending_mask = (
    documentos_df["status"].fillna("").astype(str).str.lower().eq("pendente")
    if not documentos_df.empty and "status" in documentos_df
    else pd.Series(dtype=bool)
)
documentos_pendentes = (
    int(pending_mask.sum()) if not pending_mask.empty else 0
)
riscos_criticos = (
    int(riscos_df["classificacao"].fillna("").astype(str).str.lower().eq("critico").sum())
    if not riscos_df.empty and "classificacao" in riscos_df
    else 0
)
total_documentos = len(documentos_df)
documentos_fora_do_fluxo = (
    int((expired_mask | pending_mask).sum())
    if not documentos_df.empty and not pending_mask.empty
    else documentos_vencidos + documentos_pendentes
)
documentos_conformes = max(total_documentos - documentos_fora_do_fluxo, 0)
conformidade = (
    round((documentos_conformes / total_documentos) * 100, 1)
    if total_documentos
    else 0
)

metric_cols = st.columns(4)
metric_cols[0].metric("Conformidade geral", f"{conformidade}%")
metric_cols[1].metric("Documentos vencidos", documentos_vencidos)
metric_cols[2].metric("Documentos pendentes", documentos_pendentes)
metric_cols[3].metric("Riscos criticos", riscos_criticos)

chart_cols = st.columns(2)
with chart_cols[0]:
    st.markdown("### Riscos por area")
    if not riscos_df.empty and "area" in riscos_df:
        riscos_area = riscos_df.groupby("area", as_index=False).size()
        fig = px.bar(riscos_area, x="area", y="size", labels={"size": "Riscos", "area": "Area"})
        fig.update_layout(template="plotly_dark", paper_bgcolor="#0f172a", plot_bgcolor="#111827")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum risco cadastrado.")

with chart_cols[1]:
    st.markdown("### Documentos por status")
    if not documentos_df.empty and "status" in documentos_df:
        status_df = documentos_df.groupby("status", as_index=False).size()
        fig = px.pie(status_df, names="status", values="size", hole=0.45)
        fig.update_layout(template="plotly_dark", paper_bgcolor="#0f172a", plot_bgcolor="#111827")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum documento cadastrado.")

st.markdown("### Eficiencia por area")
efficiency_df = build_area_efficiency(documentos_df)
if not efficiency_df.empty:
    fig = px.bar(
        efficiency_df,
        x="area",
        y="eficiencia",
        text="eficiencia",
        labels={"area": "Area", "eficiencia": "Eficiencia (%)"},
        range_y=[0, 100],
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(template="plotly_dark", paper_bgcolor="#0f172a", plot_bgcolor="#111827")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Cadastre documentos por area para calcular eficiencia operacional.")
