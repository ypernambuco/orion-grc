import pandas as pd
import plotly.express as px
import streamlit as st

from services.access_control import require_permission
from services.supabase_client import get_supabase
from services.ui import (
    apply_chart_theme,
    apply_theme,
    chart_efficiency_color,
    chart_efficiency_label,
    chart_risk_density_colors,
    chart_risk_density_labels,
    chart_status_color,
    display_label,
    filter_non_corporate_area_rows,
    orion_loading,
    render_compliance_score,
    render_empty_state,
    render_executive_summary,
    render_hero,
    render_insight_card,
    render_kpi_card,
    render_orion_chart,
    render_priority_card,
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
    except Exception:
        render_status_message(
            "Não foi possível carregar os dados corporativos no momento.",
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
    documentos_vigentes = (
        int(documentos_df["status"].fillna("").astype(str).str.lower().eq("vigente").sum())
        if not documentos_df.empty and "status" in documentos_df
        else 0
    )

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
        "documentos_vigentes": documentos_vigentes,
        "percentual_vigentes": (
            round((documentos_vigentes / total_documentos) * 100, 1)
            if total_documentos
            else 0
        ),
        "documentos_conformes": documentos_conformes,
        "documentos_fora_do_fluxo": documentos_fora_do_fluxo,
        "riscos_criticos": riscos_criticos,
        "total_documentos": total_documentos,
        "total_areas": total_areas,
        "total_riscos": total_riscos,
        "risk_posture": calculate_risk_posture(riscos_criticos),
        "organizational_efficiency": calculate_organizational_efficiency(documentos_df),
    }


def _risk_concentration_by_area(riscos_df: pd.DataFrame) -> pd.DataFrame:
    if riscos_df.empty or "area" not in riscos_df:
        return pd.DataFrame(columns=["area", "size"])
    return (
        riscos_df.groupby("area", as_index=False)
        .size()
        .sort_values("size", ascending=False)
    )


def generate_organizational_assessment(
    metrics: dict[str, object],
    riscos_df: pd.DataFrame,
) -> str:
    conformidade = float(metrics["conformidade"])
    riscos_criticos = int(metrics["riscos_criticos"])
    documentos_vencidos = int(metrics["documentos_vencidos"])
    documentos_pendentes = int(metrics["documentos_pendentes"])
    total_documentos = int(metrics["total_documentos"])
    total_riscos = int(metrics["total_riscos"])
    efficiency = metrics["organizational_efficiency"]

    if total_documentos == 0 and total_riscos == 0:
        return (
            "A organização ainda não possui base documental ou matriz de riscos suficiente "
            "para uma leitura executiva consolidada. O foco inicial deve ser estabelecer "
            "cobertura mínima por área antes de avaliar desempenho e exposição."
        )

    assessment = []
    if total_documentos == 0:
        assessment.append(
            "A matriz de riscos já permite leitura de exposição, mas a ausência de documentos "
            "impede avaliar conformidade e eficiência operacional."
        )
    elif conformidade >= 90 and riscos_criticos == 0:
        assessment.append(
            f"A organização opera em condição controlada, com {conformidade}% de conformidade "
            "documental e sem riscos críticos ativos."
        )
    elif conformidade >= 90:
        assessment.append(
            f"A base documental apresenta desempenho sólido, com {conformidade}% de conformidade, "
            f"mas {riscos_criticos} risco(s) crítico(s) mantêm pressão sobre a postura corporativa."
        )
    elif conformidade >= 70:
        assessment.append(
            f"A organização mantém controle intermediário, com {conformidade}% de conformidade, "
            f"{documentos_vencidos} documento(s) vencido(s) e {documentos_pendentes} pendente(s)."
        )
    else:
        assessment.append(
            f"A conformidade de {conformidade}% indica exposição operacional relevante e exige "
            "regularização prioritária do ciclo documental."
        )

    efficiency_df = efficiency["data"]
    if not efficiency_df.empty:
        assessment.append(
            f"A eficiência média entre áreas é de {efficiency['average']}%, com menor desempenho "
            f"em {efficiency['lowest_area']}."
        )

    risk_concentration = _risk_concentration_by_area(riscos_df)
    if not risk_concentration.empty:
        top_risk_area = display_label(str(risk_concentration.iloc[0]["area"]))
        top_risk_count = int(risk_concentration.iloc[0]["size"])
        assessment.append(
            f"{top_risk_area} concentra a maior exposição observada, com {top_risk_count} risco(s) registrado(s)."
        )

    return " ".join(assessment)


def generate_executive_insights(
    riscos_df: pd.DataFrame,
    metrics: dict[str, object],
) -> list[dict[str, str]]:
    insights = []
    efficiency_df = metrics["organizational_efficiency"]["data"]
    risk_concentration = _risk_concentration_by_area(riscos_df)

    if not efficiency_df.empty:
        lowest = efficiency_df.iloc[-1]
        insights.append(
            {
                "label": "Eficiência",
                "title": f"{display_label(str(lowest['area']))}: {lowest['eficiencia']}%",
                "message": "Área com menor eficiência documental e maior necessidade de acompanhamento.",
            }
        )
    else:
        insights.append(
            {
                "label": "Eficiência",
                "title": "Leitura ainda indisponível",
                "message": "A eficiência por área será calculada quando houver documentos vinculados.",
            }
        )

    if not risk_concentration.empty:
        top_risk = risk_concentration.iloc[0]
        share = round((int(top_risk["size"]) / int(metrics["total_riscos"])) * 100, 1)
        insights.append(
            {
                "label": "Concentração de riscos",
                "title": display_label(str(top_risk["area"])),
                "message": f"Concentra {int(top_risk['size'])} risco(s), equivalentes a {share}% da matriz atual.",
            }
        )
    else:
        insights.append(
            {
                "label": "Concentração de riscos",
                "title": "Matriz ainda indisponível",
                "message": "Nenhuma área possui riscos suficientes para análise de concentração.",
            }
        )

    if int(metrics["riscos_criticos"]):
        insights.append(
            {
                "label": "Exposição crítica",
                "title": f"{metrics['riscos_criticos']} risco(s) crítico(s)",
                "message": "Eventos críticos ativos exigem acompanhamento na pauta executiva.",
            }
        )
    elif int(metrics["total_riscos"]):
        insights.append(
            {
                "label": "Exposição crítica",
                "title": "Sem riscos críticos",
                "message": "A matriz atual não apresenta eventos classificados como críticos.",
            }
        )

    if int(metrics["documentos_vencidos"]):
        insights.append(
            {
                "label": "Ciclo documental",
                "title": f"{metrics['documentos_vencidos']} documento(s) vencido(s)",
                "message": "Itens fora da validade reduzem a conformidade e demandam regularização.",
            }
        )
    elif int(metrics["total_documentos"]):
        insights.append(
            {
                "label": "Ciclo documental",
                "title": "Sem documentos vencidos",
                "message": "A base monitorada não apresenta documentos fora da validade.",
            }
        )
    else:
        insights.append(
            {
                "label": "Ciclo documental",
                "title": "Base ainda indisponível",
                "message": "Nenhum documento está disponível para análise do ciclo de controle.",
            }
        )

    if not efficiency_df.empty:
        best = efficiency_df.iloc[0]
        insights.append(
            {
                "label": "Melhor desempenho",
                "title": f"{display_label(str(best['area']))}: {best['eficiencia']}%",
                "message": "Área com melhor desempenho documental entre as unidades monitoradas.",
            }
        )

    if int(metrics["total_documentos"]):
        insights.append(
            {
                "label": "Conformidade consolidada",
                "title": f"{metrics['conformidade']}%",
                "message": f"{metrics['documentos_fora_do_fluxo']} documento(s) estão fora do fluxo esperado.",
            }
        )

    return insights[:6]


def generate_executive_priorities(metrics: dict[str, object]) -> list[dict[str, str]]:
    priorities = []
    total_documentos = int(metrics["total_documentos"])
    total_riscos = int(metrics["total_riscos"])
    conformidade = float(metrics["conformidade"])

    if int(metrics["riscos_criticos"]):
        priorities.append(
            {
                "priority": "Alta Prioridade",
                "title": "Tratar riscos críticos ativos",
                "message": f"{metrics['riscos_criticos']} evento(s) crítico(s) exigem resposta executiva.",
            }
        )
    if int(metrics["documentos_vencidos"]):
        priorities.append(
            {
                "priority": "Alta Prioridade",
                "title": "Regularizar documentos vencidos",
                "message": f"{metrics['documentos_vencidos']} documento(s) ultrapassaram o vencimento.",
            }
        )
    if total_documentos and conformidade < 70:
        priorities.append(
            {
                "priority": "Alta Prioridade",
                "title": "Recuperar conformidade documental",
                "message": f"O índice atual de {conformidade}% está abaixo do nível executivo esperado.",
            }
        )
    if int(metrics["documentos_pendentes"]):
        priorities.append(
            {
                "priority": "Média Prioridade",
                "title": "Resolver pendências documentais",
                "message": f"{metrics['documentos_pendentes']} documento(s) aguardam conclusão do fluxo.",
            }
        )
    if total_documentos and 70 <= conformidade < 90:
        priorities.append(
            {
                "priority": "Média Prioridade",
                "title": "Elevar conformidade para faixa saudável",
                "message": f"O índice de {conformidade}% requer redução dos desvios documentais.",
            }
        )
    if not total_documentos:
        priorities.append(
            {
                "priority": "Média Prioridade",
                "title": "Estruturar cobertura documental",
                "message": "Cadastre documentos por área para habilitar conformidade e eficiência.",
            }
        )
    if not total_riscos:
        priorities.append(
            {
                "priority": "Média Prioridade",
                "title": "Estruturar matriz de riscos",
                "message": "Registre riscos por área para habilitar a leitura de exposição.",
            }
        )
    if total_documentos and conformidade >= 90:
        priorities.append(
            {
                "priority": "Baixa Prioridade",
                "title": "Preservar conformidade saudável",
                "message": f"A base documental opera com {conformidade}% de conformidade.",
            }
        )
    if total_riscos and not int(metrics["riscos_criticos"]):
        priorities.append(
            {
                "priority": "Baixa Prioridade",
                "title": "Manter exposição crítica controlada",
                "message": "Não há riscos críticos ativos na matriz atual.",
            }
        )
    if total_documentos and not int(metrics["documentos_vencidos"]):
        priorities.append(
            {
                "priority": "Baixa Prioridade",
                "title": "Manter ciclo documental em dia",
                "message": "Nenhum documento monitorado está vencido.",
            }
        )

    return priorities[:6]


def generate_positive_highlights(
    riscos_df: pd.DataFrame,
    metrics: dict[str, object],
) -> list[dict[str, str]]:
    highlights = []
    efficiency_df = metrics["organizational_efficiency"]["data"]

    if not efficiency_df.empty:
        best = efficiency_df.iloc[0]
        highlights.append(
            {
                "label": "Melhor área monitorada",
                "title": display_label(str(best["area"])),
                "message": f"Eficiência documental de {best['eficiencia']}%.",
            }
        )

    if int(metrics["total_documentos"]):
        highlights.append(
            {
                "label": "Documentos vigentes",
                "title": f"{metrics['percentual_vigentes']}%",
                "message": f"{metrics['documentos_vigentes']} de {metrics['total_documentos']} documentos estão vigentes.",
            }
        )

    if int(metrics["total_riscos"]):
        critical_share = round(
            (int(metrics["riscos_criticos"]) / int(metrics["total_riscos"])) * 100,
            1,
        )
        if critical_share <= 20:
            highlights.append(
                {
                    "label": "Concentração crítica",
                    "title": f"{critical_share}% da matriz",
                    "message": "A participação de riscos críticos permanece concentrada em até um quinto da matriz.",
                }
            )

        risk_concentration = _risk_concentration_by_area(riscos_df)
        if not risk_concentration.empty:
            top_share = round(
                (int(risk_concentration.iloc[0]["size"]) / int(metrics["total_riscos"])) * 100,
                1,
            )
            if top_share <= 30:
                highlights.append(
                    {
                        "label": "Distribuição de riscos",
                        "title": "Exposição distribuída",
                        "message": f"A área mais exposta concentra apenas {top_share}% dos riscos registrados.",
                    }
                )

    return highlights[:4]


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
require_permission("Dashboard")
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
        "Recurso em configuração administrativa.",
        title="Dados corporativos",
        kind="warning",
    )

metrics = calculate_cockpit_metrics(areas_df, documentos_df, riscos_df)
organizational_assessment = generate_organizational_assessment(metrics, riscos_df)
executive_insights = generate_executive_insights(riscos_df, metrics)
executive_priorities = generate_executive_priorities(metrics)
positive_highlights = generate_positive_highlights(riscos_df, metrics)
strategic_alerts = generate_strategic_alerts(areas_df, documentos_df, riscos_df, metrics)

render_executive_summary(organizational_assessment)

decision_cols = st.columns(3)
with decision_cols[0]:
    render_compliance_score(metrics)
with decision_cols[1]:
    render_risk_posture(metrics)
with decision_cols[2]:
    render_strategic_alerts(strategic_alerts)

st.markdown('<div class="orion-section-break"></div>', unsafe_allow_html=True)
st.markdown("## Executive Intelligence")
st.markdown(
    '<p class="orion-section">Análises automáticas baseadas nos dados atuais de conformidade, eficiência e exposição a riscos.</p>',
    unsafe_allow_html=True,
)
for offset in range(0, len(executive_insights), 3):
    insight_cols = st.columns(3)
    for column, insight in zip(insight_cols, executive_insights[offset : offset + 3]):
        with column:
            render_insight_card(insight["label"], insight["title"], insight["message"])

st.markdown("### Executive Priorities")
st.markdown(
    '<p class="orion-section">Ordem sugerida de atenção executiva conforme criticidade e condição operacional.</p>',
    unsafe_allow_html=True,
)
for offset in range(0, len(executive_priorities), 3):
    priority_cols = st.columns(3)
    for column, priority in zip(priority_cols, executive_priorities[offset : offset + 3]):
        with column:
            render_priority_card(
                priority["priority"],
                priority["title"],
                priority["message"],
            )

st.markdown("### Destaques positivos")
st.markdown(
    '<p class="orion-section">Sinais favoráveis que ajudam a preservar práticas e controles com bom desempenho.</p>',
    unsafe_allow_html=True,
)
if positive_highlights:
    for offset in range(0, len(positive_highlights), 3):
        highlight_cols = st.columns(3)
        for column, highlight in zip(
            highlight_cols,
            positive_highlights[offset : offset + 3],
        ):
            with column:
                render_insight_card(
                    highlight["label"],
                    highlight["title"],
                    highlight["message"],
                )
else:
    render_empty_state(
        "Destaques positivos ainda indisponíveis",
        "A base atual ainda não possui sinais suficientes para destacar desempenho favorável.",
        "Amplie a cobertura documental e a matriz de riscos para liberar esta leitura.",
    )

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
        riscos_area["concentracao"] = chart_risk_density_labels(riscos_area["size"])
        fig = px.bar(
            riscos_area,
            x="area",
            y="size",
            text="size",
            custom_data=["concentracao"],
            labels={"size": "Riscos", "area": "Área"},
        )
        fig.update_traces(
            marker_color=riscos_area["color"].tolist(),
            marker_line_color="rgba(255,255,255,0.18)",
            marker_line_width=1,
            textposition="outside",
            textfont=dict(color="#F4F5F7", size=12),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{x}</b><br>Riscos: %{y}"
                "<br>Concentração relativa: %{customdata[0]}<extra></extra>"
            ),
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
            textfont=dict(color="#F7F8FA", size=12),
            marker=dict(line=dict(color="rgba(5,5,5,0.92)", width=2)),
            hovertemplate=(
                "<b>%{label}</b><br>Documentos: %{value}"
                "<br>Participação: %{percent}<extra></extra>"
            ),
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
    efficiency_df["faixa"] = efficiency_df["eficiencia"].apply(chart_efficiency_label)
    fig = px.bar(
        efficiency_df,
        x="area",
        y="eficiencia",
        text="eficiencia",
        custom_data=["faixa"],
        labels={"area": "Área", "eficiencia": "Eficiência (%)"},
        range_y=[0, 100],
    )
    fig.update_traces(
        texttemplate="%{text}%",
        textposition="outside",
        textfont=dict(color="#F4F5F7", size=12),
        cliponaxis=False,
        marker_color=efficiency_df["color"].tolist(),
        marker_line_color="rgba(255,255,255,0.18)",
        marker_line_width=1,
        hovertemplate=(
            "<b>%{x}</b><br>Eficiência: %{y}%"
            "<br>Faixa: %{customdata[0]}<extra></extra>"
        ),
    )
    apply_chart_theme(fig, height=390)
    render_orion_chart(fig)
else:
    render_empty_state(
        "Eficiência ainda indisponível",
        "O indicador depende de documentos vinculados às áreas corporativas e seus respectivos status.",
        "Cadastre documentos por área para calcular a eficiência operacional estimada.",
    )
