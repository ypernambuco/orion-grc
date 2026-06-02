from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from services.supabase_client import get_supabase
from services.ui import (
    apply_chart_theme,
    apply_theme,
    badge_html,
    display_label,
    render_card,
    render_empty_state,
    render_hero,
    render_sidebar,
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
                "label": "Compliance",
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


def render_cockpit_styles() -> None:
    st.markdown(
        """
        <style>
            .orion-cockpit-panel {
                border: 1px solid rgba(212, 166, 74, 0.15);
                border-radius: 8px;
                background:
                    linear-gradient(140deg, rgba(212, 166, 74, 0.085), rgba(214, 217, 224, 0.022)),
                    rgba(15, 17, 21, 0.92);
                box-shadow: 0 22px 52px rgba(0, 0, 0, 0.34);
                padding: 22px 24px;
                min-height: 204px;
            }

            .orion-cockpit-kicker {
                color: var(--orion-gold-accent);
                font-size: 0.72rem;
                font-weight: 780;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 10px;
            }

            .orion-cockpit-title {
                color: var(--orion-silver);
                font-size: 1.2rem;
                font-weight: 800;
                line-height: 1.25;
                margin-bottom: 10px;
            }

            .orion-cockpit-text {
                color: var(--orion-muted-strong);
                font-size: 0.95rem;
                line-height: 1.56;
                margin: 0;
            }

            .orion-score-value {
                color: var(--orion-silver);
                font-size: 3rem;
                font-weight: 820;
                line-height: 1;
                margin: 14px 0 12px;
            }

            .orion-score-row {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
                margin-bottom: 10px;
            }

            .orion-alert-list {
                display: grid;
                gap: 10px;
            }

            .orion-alert-item {
                border: 1px solid rgba(212, 166, 74, 0.13);
                border-radius: 8px;
                background: rgba(214, 217, 224, 0.035);
                padding: 12px 13px;
            }

            .orion-alert-title {
                color: var(--orion-silver);
                font-size: 0.92rem;
                font-weight: 780;
                margin: 7px 0 5px;
            }

            .orion-alert-message {
                color: var(--orion-muted);
                font-size: 0.85rem;
                line-height: 1.45;
            }

            .orion-section-break {
                margin-top: 30px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_compliance_score(metrics: dict[str, object]) -> None:
    st.markdown(
        f"""
        <div class="orion-cockpit-panel">
            <div class="orion-cockpit-kicker">Compliance Score</div>
            <div class="orion-score-value">{metrics['conformidade']}%</div>
            <div class="orion-score-row">
                {badge_html(str(metrics["compliance_badge"]))}
                <span class="orion-cockpit-title">{escape(str(metrics["compliance_status"]))}</span>
            </div>
            <p class="orion-cockpit-text">{escape(str(metrics["compliance_description"]))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_risk_posture(metrics: dict[str, object]) -> None:
    posture = metrics["risk_posture"]
    st.markdown(
        f"""
        <div class="orion-cockpit-panel">
            <div class="orion-cockpit-kicker">Risk Posture</div>
            <div class="orion-cockpit-title">Postura {escape(str(posture["status"]))}</div>
            <div class="orion-score-row">
                {badge_html(str(posture["badge"]))}
                <span class="orion-cockpit-text">{metrics['riscos_criticos']} risco(s) crítico(s)</span>
            </div>
            <p class="orion-cockpit-text">{escape(str(posture["description"]))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_executive_summary(summary: str) -> None:
    st.markdown(
        f"""
        <div class="orion-cockpit-panel">
            <div class="orion-cockpit-kicker">Executive Summary</div>
            <div class="orion-cockpit-title">Leitura estratégica do momento</div>
            <p class="orion-cockpit-text">{escape(summary)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_strategic_alerts(alerts: list[dict[str, str]]) -> None:
    if not alerts:
        render_empty_state(
            "Sem alertas estratégicos",
            "A visão atual não aponta documentos vencidos, pendências relevantes, riscos críticos ou áreas sem cobertura.",
            "Mantenha a rotina de revisão para preservar a estabilidade operacional.",
        )
        return

    alerts_html = []
    for alert in alerts:
        alerts_html.append(
            f"""
            <div class="orion-alert-item">
                {badge_html(alert["label"])}
                <div class="orion-alert-title">{escape(alert["title"])}</div>
                <div class="orion-alert-message">{escape(alert["message"])}</div>
            </div>
            """
        )

    st.markdown(
        f"""
        <div class="orion-alert-list">
            {''.join(alerts_html)}
        </div>
        """,
        unsafe_allow_html=True,
    )


apply_theme()
render_cockpit_styles()
render_sidebar("Dashboard")
render_hero(
    "Vaekor Labs | ORION GRC",
    "Executive Cockpit",
    (
        "Visão consolidada de governança, riscos e conformidade para apoiar "
        "decisões executivas, priorização de controles e acompanhamento operacional."
    ),
)

with st.spinner("Carregando visão executiva..."):
    areas_df, documentos_df, riscos_df = load_data()
documentos_df = normalize_area_name(documentos_df)
riscos_df = normalize_area_name(riscos_df)

if get_supabase() is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env ou em st.secrets para carregar os dados.")

metrics = calculate_cockpit_metrics(areas_df, documentos_df, riscos_df)
executive_summary = generate_executive_summary(metrics)
strategic_alerts = generate_strategic_alerts(areas_df, documentos_df, riscos_df, metrics)

summary_col, score_col, posture_col = st.columns([1.5, 0.85, 0.85])
with summary_col:
    render_executive_summary(executive_summary)
with score_col:
    render_compliance_score(metrics)
with posture_col:
    render_risk_posture(metrics)

st.markdown("### Alertas estratégicos")
st.markdown(
    '<p class="orion-section">Prioridades gerenciais derivadas dos dados atuais de governança, documentos e riscos.</p>',
    unsafe_allow_html=True,
)
render_strategic_alerts(strategic_alerts)

st.markdown("### Indicadores executivos principais")
st.markdown(
    '<p class="orion-section">Sinais consolidados para acompanhamento rápido da saúde operacional do GRC.</p>',
    unsafe_allow_html=True,
)
metric_cols = st.columns(3)
with metric_cols[0]:
    render_card(
        "Conformidade geral",
        f"{metrics['conformidade']}%",
        "Base consolidada" if metrics["total_documentos"] else "Aguardando dados documentais.",
    )
with metric_cols[1]:
    render_card(
        "Documentos vencidos",
        str(metrics["documentos_vencidos"]),
        "Sem alertas" if metrics["documentos_vencidos"] == 0 else "Requer regularização.",
    )
with metric_cols[2]:
    render_card(
        "Documentos pendentes",
        str(metrics["documentos_pendentes"]),
        "Fluxo controlado" if metrics["documentos_pendentes"] == 0 else "Acompanhar resolução.",
    )

metric_cols = st.columns(3)
with metric_cols[0]:
    render_card(
        "Riscos críticos",
        str(metrics["riscos_criticos"]),
        "Sem exposição crítica" if metrics["riscos_criticos"] == 0 else "Prioridade executiva.",
    )
with metric_cols[1]:
    render_card(
        "Áreas monitoradas",
        str(metrics["total_areas"]),
        "Unidades corporativas no escopo do cockpit.",
    )
with metric_cols[2]:
    render_card(
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
        st.plotly_chart(fig, width="stretch")
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
        st.plotly_chart(fig, width="stretch")
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
    st.plotly_chart(fig, width="stretch")
else:
    render_empty_state(
        "Eficiência ainda indisponível",
        "O indicador depende de documentos vinculados às áreas corporativas e seus respectivos status.",
        "Cadastre documentos por área para calcular a eficiência operacional estimada.",
    )
