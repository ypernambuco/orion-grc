import pandas as pd
import plotly.express as px
import streamlit as st

from services.supabase_client import get_supabase
from services.ui import (
    apply_chart_theme,
    apply_theme,
    chart_efficiency_color,
    chart_risk_density_colors,
    chart_status_color,
    display_label,
    filter_non_corporate_area_rows,
    orion_loading,
    render_compliance_score,
    render_empty_state,
    render_executive_summary,
    render_hero,
    render_kpi_card,
    render_orion_chart,
    render_risk_posture,
    render_sidebar,
    render_status_message,
    render_strategic_alerts,
)


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
        render_status_message(
            f"Não foi possível carregar os dados do Supabase: {exc}",
            title="Dados indisponíveis",
            kind="error",
        )
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


def remove_non_corporate_demo_residue(
    areas_df: pd.DataFrame,
    documentos_df: pd.DataFrame,
    riscos_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return (
        filter_non_corporate_area_rows(areas_df, "nome"),
        filter_non_corporate_area_rows(documentos_df, "area"),
        filter_non_corporate_area_rows(riscos_df, "area"),
    )


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


def calculate_risk_posture(riscos_criticos: int) -> dict[str, str]:
    if riscos_criticos == 0:
        return {
            "status": "Baixa",
            "badge": "Baixo",
            "description": "Sem riscos críticos registrados na matriz atual.",
        }
    if riscos_criticos <= 2:
        return {
            "status": "Moderada",
            "badge": "Médio",
            "description": "Há riscos críticos pontuais que exigem acompanhamento executivo.",
        }
    if riscos_criticos <= 5:
        return {
            "status": "Elevada",
            "badge": "Alto",
            "description": "A exposição crítica está distribuída e pede priorização gerencial.",
        }
    return {
        "status": "Crítica",
        "badge": "Crítico",
        "description": "A concentração de riscos críticos demanda resposta executiva imediata.",
    }


def calculate_organizational_efficiency(documentos_df: pd.DataFrame) -> dict[str, object]:
    efficiency_df = build_area_efficiency(documentos_df)
    if efficiency_df.empty:
        return {
            "average": 0,
            "best_area": "Indisponível",
            "lowest_area": "Indisponível",
            "data": efficiency_df,
        }

    average = round(float(efficiency_df["eficiencia"].mean()), 1)
    best_area = display_label(str(efficiency_df.iloc[0]["area"]))
    lowest_area = display_label(str(efficiency_df.iloc[-1]["area"]))
    return {
        "average": average,
        "best_area": best_area,
        "lowest_area": lowest_area,
        "data": efficiency_df,
    }


def calculate_cockpit_metrics(
    areas_df: pd.DataFrame,
    documentos_df: pd.DataFrame,
    riscos_df: pd.DataFrame,
) -> dict[str, object]:
    expired_mask = classify_expired(documentos_df)
    documentos_vencidos = int(expired_mask.sum()) if not documentos_df.empty else 0

    pending_mask = (
        documentos_df["status"].fillna("").astype(str).str.lower().eq("pendente")
        if not documentos_df.empty and "status" in documentos_df
        else pd.Series(dtype=bool)
    )
    documentos_pendentes = int(pending_mask.sum()) if not pending_mask.empty else 0

    riscos_criticos = (
        int(riscos_df["classificacao"].fillna("").astype(str).str.lower().eq("critico").sum())
        if not riscos_df.empty and "classificacao" in riscos_df
        else 0
    )
    total_documentos = len(documentos_df)
    total_areas = len(areas_df)
    total_riscos = len(riscos_df)
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

    if conformidade >= 90:
        compliance_status = "Excelente"
        compliance_badge = "Baixo"
        compliance_description = "A base documental está saudável e com baixa fricção operacional."
    elif conformidade >= 70:
        compliance_status = "Atenção"
        compliance_badge = "Médio"
        compliance_description = "A operação está funcional, mas já existem pontos que pedem correção."
    else:
        compliance_status = "Crítico"
        compliance_badge = "Crítico"
        compliance_description = "A conformidade documental está abaixo do nível executivo esperado."

    return {
        "conformidade": conformidade,
        "compliance_status": compliance_status,
        "compliance_badge": compliance_badge,
        "compliance_description": compliance_description,
        "documentos_vencidos": documentos_vencidos,
        "documentos_pendentes": documentos_pendentes,
        "documentos_conformes": documentos_conformes,
        "documentos_fora_do_fluxo": documentos_fora_do_fluxo,
        "riscos_criticos": riscos_criticos,
        "total_documentos": total_documentos,
        "total_areas": total_areas,
        "total_riscos": total_riscos,
        "risk_posture": calculate_risk_posture(riscos_criticos),
        "organizational_efficiency": calculate_organizational_efficiency(documentos_df),
    }


def generate_executive_summary(metrics: dict[str, object]) -> str:
    conformidade = float(metrics["conformidade"])
    riscos_criticos = int(metrics["riscos_criticos"])
    documentos_vencidos = int(metrics["documentos_vencidos"])
    documentos_pendentes = int(metrics["documentos_pendentes"])
    total_documentos = int(metrics["total_documentos"])

    if total_documentos == 0:
        opening = (
            "Ainda não há documentos suficientes para medir a conformidade executiva. "
            "A prioridade é estruturar a base documental por área antes de ampliar a leitura estratégica."
        )
    elif conformidade >= 90:
        opening = (
            "O cenário de governança está estável e saudável, com alto nível de conformidade documental."
        )
    elif conformidade >= 70:
        opening = (
            "O cenário exige atenção: a operação mantém controle geral, mas já apresenta desvios relevantes."
        )
    else:
        opening = (
            "O cenário é crítico para governança e compliance, com baixa conformidade documental consolidada."
        )

    details = []
    if riscos_criticos:
        details.append(
            f"Existem {riscos_criticos} risco(s) crítico(s) que devem entrar na pauta executiva."
        )
    if documentos_vencidos or documentos_pendentes:
        details.append(
            f"Há {documentos_vencidos} documento(s) vencido(s) e {documentos_pendentes} pendente(s), exigindo plano de ação."
        )
    if not details and total_documentos:
        details.append("Não há sinais imediatos de ruptura no fluxo documental monitorado.")

    return " ".join([opening, *details])


def _area_names(areas_df: pd.DataFrame) -> set[str]:
    if areas_df.empty or "nome" not in areas_df:
        return set()
    return set(areas_df["nome"].dropna().astype(str))


def _used_area_names(df: pd.DataFrame) -> set[str]:
    if df.empty or "area" not in df:
        return set()
    return set(df["area"].dropna().astype(str))


def generate_strategic_alerts(
    areas_df: pd.DataFrame,
    documentos_df: pd.DataFrame,
    riscos_df: pd.DataFrame,
    metrics: dict[str, object],
) -> list[dict[str, str]]:
    alerts = []

    if int(metrics["documentos_vencidos"]):
        alerts.append(
            {
                "label": "Documento",
                "title": "Documentos vencidos",
                "message": f"{metrics['documentos_vencidos']} documento(s) ultrapassaram o vencimento e precisam de regularização.",
            }
        )
    if int(metrics["documentos_pendentes"]):
        alerts.append(
            {
                "label": "Conformidade",
                "title": "Pendências documentais",
                "message": f"{metrics['documentos_pendentes']} documento(s) seguem pendentes no ciclo de controle.",
            }
        )
    if int(metrics["riscos_criticos"]):
        alerts.append(
            {
                "label": "Risco",
                "title": "Riscos críticos ativos",
                "message": f"{metrics['riscos_criticos']} risco(s) crítico(s) requerem resposta executiva.",
            }
        )

    monitored_areas = _area_names(areas_df)
    areas_without_documents = sorted(monitored_areas - _used_area_names(documentos_df))
    areas_without_risks = sorted(monitored_areas - _used_area_names(riscos_df))

    if areas_without_documents:
        alerts.append(
            {
                "label": "Área",
                "title": "Áreas sem documentos",
                "message": f"{len(areas_without_documents)} área(s) ainda não possuem documentos monitorados.",
            }
        )
    if areas_without_risks:
        alerts.append(
            {
                "label": "Área",
                "title": "Áreas sem riscos",
                "message": f"{len(areas_without_risks)} área(s) ainda não possuem riscos registrados.",
            }
        )

    return alerts[:5]


apply_theme()
render_sidebar("Dashboard")
render_hero(
    "Vaekor Labs | ORION GRC",
    "Cockpit Executivo",
    (
        "Visão consolidada de governança, riscos e conformidade para apoiar "
        "decisões executivas, priorização de controles e acompanhamento operacional."
    ),
)

with orion_loading("Carregando visão executiva..."):
    areas_df, documentos_df, riscos_df = load_data()
documentos_df = normalize_area_name(documentos_df)
riscos_df = normalize_area_name(riscos_df)
areas_df, documentos_df, riscos_df = remove_non_corporate_demo_residue(
    areas_df,
    documentos_df,
    riscos_df,
)

if get_supabase() is None:
    render_status_message(
        "Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env ou em st.secrets para carregar os dados.",
        title="Conexão de dados pendente",
        kind="warning",
    )

metrics = calculate_cockpit_metrics(areas_df, documentos_df, riscos_df)
executive_summary = generate_executive_summary(metrics)
strategic_alerts = generate_strategic_alerts(areas_df, documentos_df, riscos_df, metrics)

render_executive_summary(executive_summary)

decision_cols = st.columns(3)
with decision_cols[0]:
    render_compliance_score(metrics)
with decision_cols[1]:
    render_risk_posture(metrics)
with decision_cols[2]:
    render_strategic_alerts(strategic_alerts)

st.markdown('<div class="orion-section-break"></div>', unsafe_allow_html=True)
st.markdown("### Indicadores Executivos")
st.markdown(
    '<p class="orion-section">Sinais consolidados para acompanhamento rápido da saúde operacional do GRC.</p>',
    unsafe_allow_html=True,
)

metric_cols = st.columns(3)
with metric_cols[0]:
    render_kpi_card(
        "Conformidade geral",
        f"{metrics['conformidade']}%",
        "Base consolidada" if metrics["total_documentos"] else "Aguardando dados documentais.",
    )
with metric_cols[1]:
    render_kpi_card(
        "Documentos vencidos",
        str(metrics["documentos_vencidos"]),
        "Sem alertas" if metrics["documentos_vencidos"] == 0 else "Requer regularização.",
    )
with metric_cols[2]:
    render_kpi_card(
        "Documentos pendentes",
        str(metrics["documentos_pendentes"]),
        "Fluxo controlado" if metrics["documentos_pendentes"] == 0 else "Acompanhar resolução.",
    )

metric_cols = st.columns(3)
with metric_cols[0]:
    render_kpi_card(
        "Riscos críticos",
        str(metrics["riscos_criticos"]),
        "Sem exposição crítica" if metrics["riscos_criticos"] == 0 else "Prioridade executiva.",
    )
with metric_cols[1]:
    render_kpi_card(
        "Áreas monitoradas",
        str(metrics["total_areas"]),
        "Unidades corporativas no escopo do cockpit.",
    )
with metric_cols[2]:
    render_kpi_card(
        "Riscos registrados",
        str(metrics["total_riscos"]),
        "Eventos classificados na matriz operacional.",
    )

st.markdown('<div class="orion-section-break"></div>', unsafe_allow_html=True)
st.markdown("## Análises Operacionais")
st.markdown(
    '<p class="orion-section">Gráficos de apoio para investigar concentração de riscos, ciclo documental e eficiência por área.</p>',
    unsafe_allow_html=True,
)

chart_cols = st.columns(2)
with chart_cols[0]:
    st.markdown("### Riscos por área")
    st.markdown(
        '<p class="orion-section">Mapa de concentração para priorização gerencial.</p>',
        unsafe_allow_html=True,
    )
    if not riscos_df.empty and "area" in riscos_df:
        riscos_area = riscos_df.groupby("area", as_index=False).size()
        riscos_area = riscos_area.sort_values("size", ascending=False)
        riscos_area["area"] = riscos_area["area"].apply(display_label)
        riscos_area["color"] = chart_risk_density_colors(riscos_area["size"])
        fig = px.bar(
            riscos_area,
            x="area",
            y="size",
            labels={"size": "Riscos", "area": "Área"},
        )
        fig.update_traces(
            marker_color=riscos_area["color"].tolist(),
            marker_line_color="rgba(245,201,106,0.28)",
            marker_line_width=1,
            hovertemplate="<b>%{x}</b><br>Riscos: %{y}<extra></extra>",
        )
        apply_chart_theme(fig, height=350)
        render_orion_chart(fig)
    else:
        render_empty_state(
            "Sem riscos para consolidar",
            "A visão por área será exibida assim que a matriz de riscos receber eventos classificados.",
            "Registre riscos na página Riscos para ativar a análise executiva por área.",
        )

with chart_cols[1]:
    st.markdown("### Documentos por status")
    st.markdown(
        '<p class="orion-section">Distribuição do ciclo documental por situação atual.</p>',
        unsafe_allow_html=True,
    )
    if not documentos_df.empty and "status" in documentos_df:
        status_df = documentos_df.groupby("status", as_index=False).size()
        status_df["status"] = status_df["status"].apply(display_label)
        status_df["color"] = status_df["status"].apply(chart_status_color)
        fig = px.pie(
            status_df,
            names="status",
            values="size",
            hole=0.58,
            color="status",
            color_discrete_map=dict(zip(status_df["status"], status_df["color"])),
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            marker=dict(line=dict(color="rgba(5,5,5,0.92)", width=2)),
            hovertemplate="<b>%{label}</b><br>Documentos: %{value}<extra></extra>",
        )
        apply_chart_theme(fig, height=350)
        render_orion_chart(fig)
    else:
        render_empty_state(
            "Sem documentos para analisar",
            "A distribuição por status aparecerá quando houver documentos cadastrados no ciclo documental.",
            "Cadastre documentos com responsável, vencimento e status para liberar esta visão.",
        )

st.markdown("### Eficiência por área")
st.markdown(
    '<p class="orion-section">Percentual estimado de documentos vigentes e sem pendências por área.</p>',
    unsafe_allow_html=True,
)
efficiency_df = metrics["organizational_efficiency"]["data"]
if not efficiency_df.empty:
    efficiency_df = efficiency_df.copy()
    efficiency_df["area"] = efficiency_df["area"].apply(display_label)
    efficiency_df["color"] = efficiency_df["eficiencia"].apply(chart_efficiency_color)
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
        marker_color=efficiency_df["color"].tolist(),
        marker_line_color="rgba(245,201,106,0.28)",
        marker_line_width=1,
        hovertemplate="<b>%{x}</b><br>Eficiência: %{y}%<extra></extra>",
    )
    apply_chart_theme(fig, height=390)
    render_orion_chart(fig)
else:
    render_empty_state(
        "Eficiência ainda indisponível",
        "O indicador depende de documentos vinculados às áreas corporativas e seus respectivos status.",
        "Cadastre documentos por área para calcular a eficiência operacional estimada.",
    )
