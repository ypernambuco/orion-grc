import pandas as pd
import plotly.express as px
import streamlit as st

from services.supabase_client import get_supabase
from services.ui import apply_chart_theme, apply_theme, display_label, render_hero, render_sidebar


st.set_page_config(page_title="ORION GRC | Dashboard", layout="wide")


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
        st.error(f"Não foi possível carregar os dados do Supabase: {exc}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    return pd.DataFrame(areas), pd.DataFrame(documentos), pd.DataFrame(riscos)


def normalize_area_name(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "areas" not in df:
        return df
    df = df.copy()
    df["area"] = df["areas"].apply(
        lambda item: item.get("nome") if isinstance(item, dict) else "Sem área"
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
render_sidebar("Dashboard")
render_hero(
    "Visão executiva",
    "Dashboard executivo",
    (
        "Indicadores consolidados para entender conformidade documental, "
        "riscos críticos e eficiência operacional por área."
    ),
)

areas_df, documentos_df, riscos_df = load_data()
documentos_df = normalize_area_name(documentos_df)
riscos_df = normalize_area_name(riscos_df)

if get_supabase() is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env ou em st.secrets para carregar os dados.")

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
metric_cols[3].metric("Riscos críticos", riscos_criticos)

chart_cols = st.columns(2)
with chart_cols[0]:
    st.markdown("### Riscos por área")
    st.markdown(
        '<p class="orion-section">Mapa de concentração para priorização gerencial.</p>',
        unsafe_allow_html=True,
    )
    if not riscos_df.empty and "area" in riscos_df:
        riscos_area = riscos_df.groupby("area", as_index=False).size()
        riscos_area["area"] = riscos_area["area"].apply(display_label)
        fig = px.bar(
            riscos_area,
            x="area",
            y="size",
            labels={"size": "Riscos", "area": "Área"},
        )
        fig.update_traces(
            marker_color="#D4A64A",
            marker_line_color="rgba(245,201,106,0.28)",
            marker_line_width=1,
            hovertemplate="<b>%{x}</b><br>Riscos: %{y}<extra></extra>",
        )
        apply_chart_theme(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum risco cadastrado.")

with chart_cols[1]:
    st.markdown("### Documentos por status")
    st.markdown(
        '<p class="orion-section">Distribuição do ciclo documental por situação atual.</p>',
        unsafe_allow_html=True,
    )
    if not documentos_df.empty and "status" in documentos_df:
        status_df = documentos_df.groupby("status", as_index=False).size()
        status_df["status"] = status_df["status"].apply(display_label)
        fig = px.pie(
            status_df,
            names="status",
            values="size",
            hole=0.58,
            color_discrete_sequence=["#D4A64A", "#F5C96A", "#C45F5F", "#D6D9E0"],
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            marker=dict(line=dict(color="rgba(5,5,5,0.92)", width=2)),
            hovertemplate="<b>%{label}</b><br>Documentos: %{value}<extra></extra>",
        )
        apply_chart_theme(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum documento cadastrado.")

st.markdown("### Eficiência por área")
st.markdown(
    '<p class="orion-section">Percentual estimado de documentos vigentes e sem pendências por área.</p>',
    unsafe_allow_html=True,
)
efficiency_df = build_area_efficiency(documentos_df)
if not efficiency_df.empty:
    efficiency_df = efficiency_df.copy()
    efficiency_df["area"] = efficiency_df["area"].apply(display_label)
    fig = px.bar(
        efficiency_df,
        x="area",
        y="eficiencia",
        text="eficiencia",
        labels={"area": "Área", "eficiencia": "Eficiência (%)"},
        range_y=[0, 100],
    )
    fig.update_traces(
        texttemplate="%{text}%",
        textposition="outside",
        marker_color="#D6D9E0",
        marker_line_color="rgba(245,201,106,0.28)",
        marker_line_width=1,
        hovertemplate="<b>%{x}</b><br>Eficiência: %{y}%<extra></extra>",
    )
    apply_chart_theme(fig, height=390)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Cadastre documentos por área para calcular a eficiência operacional.")
