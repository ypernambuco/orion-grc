import re
from contextlib import contextmanager
from html import escape
from typing import Iterator, Optional

import streamlit as st

from services.access_control import (
    PROFILE_DESCRIPTIONS,
    get_active_profile,
    get_profiles,
    has_permission,
)


__all__ = [
    "apply_chart_theme",
    "apply_theme",
    "badge_html",
    "chart_efficiency_color",
    "chart_efficiency_label",
    "chart_risk_density_colors",
    "chart_risk_density_labels",
    "chart_status_color",
    "display_dataframe",
    "display_label",
    "filter_non_corporate_area_rows",
    "is_non_corporate_area_name",
    "orion_loading",
    "render_alert_card",
    "render_area_operational_card",
    "render_card",
    "render_compliance_score",
    "render_data_table",
    "render_empty_state",
    "render_executive_summary",
    "render_hero",
    "render_insight_card",
    "render_kpi_card",
    "render_module_card",
    "render_orion_chart",
    "render_priority_card",
    "render_risk_posture",
    "render_sidebar",
    "render_status_message",
    "render_strategic_alerts",
]


CHART_COLORS = {
    "healthy": "#43B581",
    "attention": "#E7BC54",
    "elevated": "#E08A3E",
    "critical": "#D35D5D",
    "neutral": "#D6D9E0",
    "gold_low": "#94763A",
    "gold_mid": "#D4A64A",
    "gold_high": "#D86A45",
}


NON_CORPORATE_AREA_PREFIXES = ("QA ", "Teste ", "Test ")


NAV_ITEMS = [
    ("app.py", "Início", "Visão geral do produto"),
    ("pages/dashboard.py", "Dashboard", "Indicadores executivos"),
    ("pages/areas.py", "Áreas", "Unidades de governança"),
    ("pages/documentos.py", "Documentos", "Ciclo documental"),
    ("pages/riscos.py", "Riscos", "Matriz operacional"),
    ("pages/evidencias.py", "Evidências", "Registros comprobatórios"),
]


DISPLAY_LABELS = {
    "Area": "Área",
    "Areas": "Áreas",
    "Sem area": "Sem área",
    "Medio": "Médio",
    "Critico": "Crítico",
    "Em revisao": "Em revisão",
    "Politica": "Política",
    "Relatorio": "Relatório",
    "Juridico": "Jurídico",
    "Operacoes": "Operações",
    "Tecnologia da Informacao": "Tecnologia da Informação",
}


def chart_status_color(status: str) -> str:
    semantic_colors = {
        "vigente": CHART_COLORS["healthy"],
        "pendente": CHART_COLORS["attention"],
        "vencido": CHART_COLORS["critical"],
    }
    normalized_status = str(display_label(status)).strip().casefold()
    return semantic_colors.get(normalized_status, CHART_COLORS["neutral"])


def chart_efficiency_color(value: float) -> str:
    if value >= 90:
        return CHART_COLORS["healthy"]
    if value >= 70:
        return CHART_COLORS["attention"]
    if value >= 50:
        return CHART_COLORS["elevated"]
    return CHART_COLORS["critical"]


def chart_efficiency_label(value: float) -> str:
    if value >= 90:
        return "Saudável"
    if value >= 70:
        return "Atenção"
    if value >= 50:
        return "Baixa eficiência"
    return "Crítica"


def chart_risk_density_colors(values) -> list[str]:
    values_list = [float(value) for value in values]
    if not values_list:
        return []

    minimum = min(values_list)
    maximum = max(values_list)
    if minimum == maximum:
        return [CHART_COLORS["gold_mid"] for _ in values_list]

    colors = []
    for value in values_list:
        ratio = (value - minimum) / (maximum - minimum)
        if ratio < 0.34:
            colors.append(CHART_COLORS["gold_low"])
        elif ratio < 0.67:
            colors.append(CHART_COLORS["gold_mid"])
        else:
            colors.append(CHART_COLORS["gold_high"])
    return colors


def chart_risk_density_labels(values) -> list[str]:
    values_list = [float(value) for value in values]
    if not values_list:
        return []

    minimum = min(values_list)
    maximum = max(values_list)
    if minimum == maximum:
        return ["Média" for _ in values_list]

    labels = []
    for value in values_list:
        ratio = (value - minimum) / (maximum - minimum)
        if ratio < 0.34:
            labels.append("Baixa")
        elif ratio < 0.67:
            labels.append("Média")
        else:
            labels.append("Alta")
    return labels


def is_non_corporate_area_name(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().startswith(NON_CORPORATE_AREA_PREFIXES)


def filter_non_corporate_area_rows(df, column: str = "area"):
    if df.empty or column not in df:
        return df
    return df[~df[column].apply(is_non_corporate_area_name)].copy()


DISPLAY_REPLACEMENTS = (
    ("Areas", "Áreas"),
    ("Area", "Área"),
    ("areas", "áreas"),
    ("area", "área"),
    ("Persistencia", "Persistência"),
    ("persistencia", "persistência"),
    ("Juridico", "Jurídico"),
    ("juridico", "jurídico"),
    ("Operacoes", "Operações"),
    ("operacoes", "operações"),
    ("Informacao", "Informação"),
    ("informacao", "informação"),
    ("Medio", "Médio"),
    ("medio", "médio"),
    ("Critico", "Crítico"),
    ("critico", "crítico"),
)


COLUMN_LABELS = {
    "id": "ID",
    "nome": "Nome",
    "created_at": "Criado em",
    "categoria": "Categoria",
    "area": "Área",
    "responsavel": "Responsável",
    "vencimento": "Vencimento",
    "status": "Status",
    "descricao": "Descrição",
    "probabilidade": "Probabilidade",
    "impacto": "Impacto",
    "risco": "Score",
    "classificacao": "Classificação",
    "tipo": "Tipo",
    "documento": "Documento associado",
    "risco_associado": "Risco associado",
    "data": "Data",
    "origem": "Origem",
    "total_documentos": "Documentos",
    "documentos_pendentes": "Pendentes",
    "documentos_vencidos": "Vencidos",
    "total_riscos": "Riscos",
    "riscos_criticos": "Riscos críticos",
    "eficiencia": "Eficiência (%)",
}


BADGE_STYLES = {
    "Crítico": "orion-badge-critical",
    "Alto": "orion-badge-high",
    "Médio": "orion-badge-medium",
    "Baixo": "orion-badge-low",
    "Vigente": "orion-badge-active",
    "Pendente": "orion-badge-pending",
    "Vencido": "orion-badge-expired",
    "Em revisão": "orion-badge-review",
}


def display_label(value):
    if not isinstance(value, str):
        return value
    if value in DISPLAY_LABELS:
        return DISPLAY_LABELS[value]
    label = value
    for source, target in DISPLAY_REPLACEMENTS:
        label = re.sub(rf"\b{source}\b", target, label)
    return label


def display_dataframe(df, columns):
    display_df = df[columns].copy()
    for column in display_df.columns:
        display_df[column] = display_df[column].apply(display_label)
    return display_df.rename(columns=COLUMN_LABELS)


def badge_class(value: str) -> str:
    return BADGE_STYLES.get(display_label(value), "orion-badge-neutral")


def badge_html(value: str) -> str:
    label = display_label(value)
    return f'<span class="orion-badge {badge_class(label)}">{escape(label)}</span>'


def _render_html(html: str) -> None:
    st.html(html)


def render_data_table(df, columns, height: Optional[int] = None) -> None:
    display_df = display_dataframe(df, columns)
    max_height = f' style="max-height: {height}px;"' if height else ""
    header_html = "".join(
        f"<th>{escape(str(column))}</th>" for column in display_df.columns
    )
    rows_html = []
    badge_columns = {"Status", "Classificação"}
    for _, row in display_df.iterrows():
        cells = []
        for column, value in row.items():
            if column in badge_columns:
                content = badge_html(str(value))
            else:
                content = escape("" if value is None else str(value))
            cells.append(f"<td>{content}</td>")
        rows_html.append(f"<tr>{''.join(cells)}</tr>")
    st.markdown(
        f"""
        <div class="orion-table-shell"{max_height}>
            <table class="orion-data-table">
                <thead><tr>{header_html}</tr></thead>
                <tbody>{''.join(rows_html)}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, message: str, action: Optional[str] = None) -> None:
    action_html = (
        f'<div class="orion-empty-action">{escape(action)}</div>'
        if action
        else ""
    )
    st.markdown(
        f"""
        <div class="orion-empty-state">
            <div class="orion-empty-kicker">Próximo passo</div>
            <div class="orion-empty-title">{escape(title)}</div>
            <div class="orion-empty-message">{escape(message)}</div>
            {action_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _status_message_html(message: str, title: Optional[str] = None, kind: str = "info") -> str:
    safe_kind = kind if kind in {"info", "warning", "success", "error"} else "info"
    title_html = (
        f'<div class="orion-status-title">{escape(title)}</div>'
        if title
        else ""
    )
    return f"""
    <div class="orion-status-message orion-status-message-{safe_kind}" role="status" aria-live="polite">
        {title_html}
        <p class="orion-status-text">{escape(message)}</p>
    </div>
    """


def render_status_message(message: str, title: Optional[str] = None, kind: str = "info") -> None:
    st.markdown(
        _status_message_html(message, title=title, kind=kind),
        unsafe_allow_html=True,
    )


@contextmanager
def orion_loading(message: str) -> Iterator[None]:
    placeholder = st.empty()
    placeholder.markdown(
        f'<div class="orion-loading" role="status" aria-live="polite">{escape(message)}</div>',
        unsafe_allow_html=True,
    )
    try:
        yield
    finally:
        placeholder.empty()


def _render_orion_card(label: str, value: str, note: str, variant: str, compact: bool = False) -> None:
    variant_class = f"orion-card-{variant}" if variant else ""
    compact_class = "orion-card-compact" if compact else ""
    card_class = " ".join(
        item for item in ["orion-card", variant_class, compact_class] if item
    )
    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="orion-card-label">{escape(label)}</div>
            <div class="orion-card-value">{escape(value)}</div>
            <div class="orion-card-note">{escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, note: str) -> None:
    _render_orion_card(label, value, note, "kpi")


def render_insight_card(label: str, value: str, note: str) -> None:
    _render_orion_card(label, value, note, "insight")


def render_module_card(label: str, value: str, note: str, compact: bool = False) -> None:
    _render_orion_card(label, value, note, "module", compact=compact)


def render_alert_card(label: str, value: str, note: str) -> None:
    _render_orion_card(label, value, note, "alert")


def render_area_operational_card(area: dict[str, object]) -> None:
    efficiency = float(area["eficiencia"])
    efficiency_variant = (
        "healthy"
        if efficiency >= 90
        else "attention"
        if efficiency >= 70
        else "elevated"
        if efficiency >= 50
        else "critical"
    )
    _render_html(
        f"""
        <div class="orion-area-card">
            <div class="orion-area-card-header">
                <div>
                    <div class="orion-card-label">Área monitorada</div>
                    <div class="orion-area-card-title">{escape(str(area["nome"]))}</div>
                </div>
                <div class="orion-area-efficiency orion-area-efficiency-{efficiency_variant}">{escape(str(area["eficiencia"]))}%</div>
            </div>
            <div class="orion-area-card-grid">
                <div><span>Documentos</span><strong>{escape(str(area["total_documentos"]))}</strong></div>
                <div><span>Pendentes</span><strong>{escape(str(area["documentos_pendentes"]))}</strong></div>
                <div><span>Vencidos</span><strong>{escape(str(area["documentos_vencidos"]))}</strong></div>
                <div><span>Riscos</span><strong>{escape(str(area["total_riscos"]))}</strong></div>
                <div><span>Riscos críticos</span><strong>{escape(str(area["riscos_criticos"]))}</strong></div>
                <div><span>Eficiência</span><strong>{escape(str(area["eficiencia"]))}%</strong></div>
            </div>
        </div>
        """
    )


def render_priority_card(priority: str, title: str, note: str) -> None:
    priority_variant = {
        "Alta Prioridade": "priority-high",
        "Média Prioridade": "priority-medium",
        "Baixa Prioridade": "priority-low",
    }.get(priority, "priority-medium")
    _render_orion_card(priority, title, note, priority_variant)


def render_compliance_score(metrics: dict[str, object]) -> None:
    _render_html(
        f"""
        <div class="orion-cockpit-panel orion-compliance-panel">
            <div class="orion-cockpit-kicker">Score de Conformidade</div>
            <div class="orion-score-value">{escape(str(metrics['conformidade']))}%</div>
            <div class="orion-score-row">
                {badge_html(str(metrics["compliance_badge"]))}
                <span class="orion-score-status">{escape(str(metrics["compliance_status"]))}</span>
            </div>
            <p class="orion-cockpit-text">{escape(str(metrics["compliance_description"]))}</p>
        </div>
        """
    )


def render_risk_posture(metrics: dict[str, object]) -> None:
    posture = metrics["risk_posture"]
    severity_class = {
        "Baixa": "orion-risk-posture-low",
        "Moderada": "orion-risk-posture-moderate",
        "Elevada": "orion-risk-posture-elevated",
        "Crítica": "orion-risk-posture-critical",
    }.get(str(posture["status"]), "orion-risk-posture-moderate")
    _render_html(
        f"""
        <div class="orion-cockpit-panel orion-risk-posture {severity_class}">
            <div class="orion-cockpit-kicker">Postura de Risco</div>
            <div class="orion-posture-status">{escape(str(posture["status"]))}</div>
            <div class="orion-posture-count">{escape(str(metrics['riscos_criticos']))} risco(s) crítico(s)</div>
            <p class="orion-cockpit-text">{escape(str(posture["description"]))}</p>
        </div>
        """
    )


def render_executive_summary(summary: str) -> None:
    _render_html(
        f"""
        <div class="orion-cockpit-panel orion-cockpit-panel-primary">
            <div class="orion-cockpit-kicker">Avaliação Organizacional</div>
            <div class="orion-cockpit-title">Leitura dinâmica da organização</div>
            <p class="orion-cockpit-text">{escape(summary)}</p>
        </div>
        """
    )


def render_strategic_alerts(alerts: list[dict[str, str]]) -> None:
    if not alerts:
        _render_html(
            """
            <div class="orion-cockpit-panel orion-alert-panel">
                <div class="orion-cockpit-kicker">Alertas Estratégicos</div>
                <div class="orion-cockpit-title">Sem alertas estratégicos</div>
                <p class="orion-cockpit-text">
                    A visão atual não aponta documentos vencidos, pendências relevantes,
                    riscos críticos ou áreas sem cobertura.
                </p>
            </div>
            """
        )
        return

    alerts_html = []
    for alert in alerts:
        alerts_html.append(
            f"""
            <div class="orion-alert-item">
                <div class="orion-alert-category">{escape(alert["label"])}</div>
                <div class="orion-alert-title">{escape(alert["title"])}</div>
                <div class="orion-alert-message">{escape(alert["message"])}</div>
            </div>
            """
        )

    _render_html(
        f"""
        <div class="orion-cockpit-panel orion-alert-panel">
            <div class="orion-cockpit-kicker">Alertas Estratégicos</div>
            <div class="orion-alert-list">
                {''.join(alerts_html)}
            </div>
        </div>
        """
    )


def apply_theme() -> None:
    st.markdown(
        """
        <style>
            :root {
                --orion-bg: #050505;
                --orion-bg-soft: #090a0c;
                --orion-panel: #0F1115;
                --orion-panel-raised: #13161c;
                --orion-panel-soft: #171a21;
                --orion-border: #1A1D24;
                --orion-border-strong: #2a2f3a;
                --orion-text: #D6D9E0;
                --orion-muted: #8B93A7;
                --orion-muted-strong: #b8becb;
                --orion-gold: #D4A64A;
                --orion-gold-accent: #F5C96A;
                --orion-silver: #D6D9E0;
                --orion-critical: #C45F5F;
                --orion-shadow: 0 24px 56px rgba(0, 0, 0, 0.42);
                --orion-font: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }

            .stApp {
                background:
                    linear-gradient(180deg, #0b0c0e 0%, var(--orion-bg) 42%, #020202 100%);
                color: var(--orion-text);
                font-family: var(--orion-font);
            }

            .block-container {
                padding-top: 1.45rem;
                padding-bottom: 3.4rem;
                max-width: 1280px;
            }

            [data-testid="stSidebar"] {
                background:
                    linear-gradient(180deg, #060606 0%, #090a0d 55%, #050505 100%);
                border-right: 1px solid rgba(212, 166, 74, 0.16);
                box-shadow: 18px 0 45px rgba(0, 0, 0, 0.36);
            }

            [data-testid="stSidebar"] > div:first-child {
                padding-top: 1.2rem;
            }

            [data-testid="stSidebarNav"] {
                display: none;
            }

            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3,
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] span,
            [data-testid="stSidebar"] a {
                color: var(--orion-text);
            }

            [data-testid="stSidebar"] [data-testid="stPageLink"] a,
            [data-testid="stSidebar"] a[data-testid="stPageLink"] {
                border: 1px solid transparent;
                border-radius: 8px;
                min-height: 38px;
                padding: 0.54rem 0.72rem;
                transition: background 160ms ease, border-color 160ms ease, transform 160ms ease;
            }

            [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
            [data-testid="stSidebar"] a[data-testid="stPageLink"]:hover {
                background: rgba(212, 166, 74, 0.075);
                border-color: rgba(212, 166, 74, 0.18);
                transform: translateX(2px);
            }

            [data-testid="stSidebar"] [data-testid="stPageLink"] p,
            [data-testid="stSidebar"] a[data-testid="stPageLink"] p {
                font-size: 0.9rem;
                font-weight: 720;
            }

            h1, h2, h3, p, label, span, div {
                font-family: var(--orion-font);
            }

            h1, h2, h3 {
                letter-spacing: 0;
                color: var(--orion-text);
            }

            h3 {
                font-size: 1.08rem;
                line-height: 1.25;
                margin-top: 1.35rem;
                margin-bottom: 0.2rem;
            }

            p, li {
                color: var(--orion-muted-strong);
            }

            .stMarkdown {
                margin-bottom: 0.15rem;
            }

            div[data-testid="stHorizontalBlock"] {
                gap: 1.05rem;
            }

            div[data-testid="stMetric"],
            .orion-card {
                background:
                    linear-gradient(180deg, rgba(245, 201, 106, 0.045) 0%, rgba(214, 217, 224, 0.012) 100%),
                    var(--orion-panel);
                border: 1px solid rgba(212, 166, 74, 0.14);
                border-radius: 8px;
                padding: 18px 18px 17px;
                box-shadow: var(--orion-shadow);
                min-height: 128px;
                transition: border-color 160ms ease, transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
            }

            div[data-testid="stMetric"]:hover,
            .orion-card:hover {
                border-color: rgba(245, 201, 106, 0.30);
                transform: translateY(-2px);
                box-shadow: 0 28px 62px rgba(0, 0, 0, 0.48);
            }

            div[data-testid="stMetric"] {
                border-top-color: rgba(245, 201, 106, 0.34);
                position: relative;
                overflow: hidden;
            }

            div[data-testid="stMetric"]::after {
                content: "";
                position: absolute;
                inset: 0 0 auto 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(245, 201, 106, 0.32), transparent);
            }

            div[data-testid="stMetric"] label {
                color: var(--orion-gold-accent);
                font-size: 0.74rem;
                font-weight: 780;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }

            [data-testid="stMetricLabel"],
            [data-testid="stMetricLabel"] * {
                max-width: none !important;
                overflow: visible !important;
                text-overflow: clip !important;
                white-space: normal !important;
            }

            div[data-testid="stMetricValue"] {
                color: var(--orion-silver);
                font-size: 2rem;
                font-weight: 780;
                letter-spacing: 0;
                line-height: 1.05;
                padding-top: 0.18rem;
            }

            div[data-testid="stMetricDelta"] {
                color: var(--orion-muted);
            }

            .orion-hero {
                position: relative;
                overflow: hidden;
                border: 1px solid rgba(212, 166, 74, 0.16);
                border-radius: 8px;
                background:
                    linear-gradient(120deg, rgba(212, 166, 74, 0.11), rgba(214, 217, 224, 0.035) 50%, rgba(245, 201, 106, 0.06)),
                    var(--orion-panel);
                padding: 30px 32px 31px;
                margin-bottom: 24px;
                box-shadow: var(--orion-shadow);
            }

            .orion-hero::before {
                content: "";
                position: absolute;
                inset: 0 0 auto 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(245, 201, 106, 0.45), transparent);
            }

            .orion-eyebrow {
                color: var(--orion-gold-accent);
                font-size: 0.78rem;
                font-weight: 780;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 9px;
            }

            .orion-hero h1 {
                margin: 0;
                font-size: 2.42rem;
                line-height: 1.04;
                font-weight: 820;
            }

            .orion-subtitle {
                color: var(--orion-muted-strong);
                font-size: 1.02rem;
                line-height: 1.6;
                max-width: 850px;
                margin: 13px 0 0;
            }

            .orion-card-label {
                color: var(--orion-gold-accent);
                font-size: 0.73rem;
                font-weight: 780;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                margin-bottom: 12px;
            }

            .orion-card-value {
                color: var(--orion-silver);
                font-size: 1.28rem;
                font-weight: 780;
                line-height: 1.2;
            }

            .orion-card-note {
                color: var(--orion-muted);
                font-size: 0.9rem;
                line-height: 1.5;
                margin-top: 12px;
            }

            .orion-card-kpi {
                min-height: 142px;
                border-top-color: rgba(245, 201, 106, 0.34);
                background:
                    linear-gradient(180deg, rgba(245, 201, 106, 0.055), rgba(214, 217, 224, 0.012)),
                    var(--orion-panel);
            }

            .orion-card-kpi .orion-card-value {
                font-size: 2.05rem;
                line-height: 1.05;
            }

            .orion-card-insight {
                min-height: 150px;
                background:
                    linear-gradient(135deg, rgba(212, 166, 74, 0.075), rgba(214, 217, 224, 0.018)),
                    rgba(15, 17, 21, 0.9);
            }

            .orion-card-module {
                min-height: 150px;
                background:
                    linear-gradient(180deg, rgba(214, 217, 224, 0.035), rgba(212, 166, 74, 0.018)),
                    var(--orion-panel);
            }

            .orion-card-alert {
                min-height: 0;
                padding: 14px 15px;
                box-shadow: 0 16px 34px rgba(0, 0, 0, 0.24);
            }

            .orion-card-alert .orion-card-value {
                font-size: 0.96rem;
            }

            .orion-card-alert .orion-card-note {
                font-size: 0.84rem;
                margin-top: 8px;
            }

            .orion-area-card {
                border: 1px solid rgba(212, 166, 74, 0.16);
                border-radius: 8px;
                background:
                    linear-gradient(145deg, rgba(212, 166, 74, 0.08), rgba(214, 217, 224, 0.015)),
                    var(--orion-panel);
                box-shadow: 0 20px 44px rgba(0, 0, 0, 0.30);
                min-height: 246px;
                padding: 19px;
                transition: border-color 160ms ease, transform 160ms ease, box-shadow 160ms ease;
            }

            .orion-area-card:hover {
                border-color: rgba(245, 201, 106, 0.32);
                box-shadow: 0 26px 58px rgba(0, 0, 0, 0.42);
                transform: translateY(-2px);
            }

            .orion-area-card-header {
                align-items: flex-start;
                display: flex;
                gap: 12px;
                justify-content: space-between;
                margin-bottom: 17px;
            }

            .orion-area-card-title {
                color: var(--orion-silver);
                font-size: 1.08rem;
                font-weight: 800;
                line-height: 1.25;
            }

            .orion-area-efficiency {
                border: 1px solid rgba(67, 181, 129, 0.28);
                border-radius: 999px;
                background: rgba(67, 181, 129, 0.10);
                color: #74C99B;
                flex: 0 0 auto;
                font-size: 0.82rem;
                font-weight: 820;
                padding: 6px 9px;
            }

            .orion-area-efficiency-attention {
                border-color: rgba(231, 188, 84, 0.34);
                background: rgba(231, 188, 84, 0.10);
                color: #E7BC54;
            }

            .orion-area-efficiency-elevated {
                border-color: rgba(224, 138, 62, 0.36);
                background: rgba(224, 138, 62, 0.11);
                color: #E08A3E;
            }

            .orion-area-efficiency-critical {
                border-color: rgba(211, 93, 93, 0.38);
                background: rgba(211, 93, 93, 0.12);
                color: #E48B8B;
            }

            .orion-area-card-grid {
                display: grid;
                gap: 9px;
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .orion-area-card-grid > div {
                border: 1px solid rgba(212, 166, 74, 0.10);
                border-radius: 7px;
                background: rgba(214, 217, 224, 0.025);
                padding: 9px 10px;
            }

            .orion-area-card-grid span {
                color: var(--orion-muted);
                display: block;
                font-size: 0.70rem;
                font-weight: 720;
                letter-spacing: 0.035em;
                margin-bottom: 4px;
                text-transform: uppercase;
            }

            .orion-area-card-grid strong {
                color: var(--orion-silver);
                font-size: 1.02rem;
                font-weight: 800;
            }

            .orion-card-priority-high,
            .orion-card-priority-medium,
            .orion-card-priority-low {
                min-height: 158px;
                position: relative;
                overflow: hidden;
            }

            .orion-card-priority-high {
                border-color: rgba(211, 93, 93, 0.42);
                background:
                    linear-gradient(145deg, rgba(211, 93, 93, 0.13), rgba(214, 217, 224, 0.012)),
                    var(--orion-panel);
            }

            .orion-card-priority-high .orion-card-label {
                color: #E48B8B;
            }

            .orion-card-priority-medium {
                border-color: rgba(231, 188, 84, 0.34);
                background:
                    linear-gradient(145deg, rgba(231, 188, 84, 0.10), rgba(214, 217, 224, 0.012)),
                    var(--orion-panel);
            }

            .orion-card-priority-low {
                border-color: rgba(67, 181, 129, 0.30);
                background:
                    linear-gradient(145deg, rgba(67, 181, 129, 0.09), rgba(214, 217, 224, 0.012)),
                    var(--orion-panel);
            }

            .orion-card-priority-low .orion-card-label {
                color: #74C99B;
            }

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

            .orion-cockpit-panel-primary {
                min-height: 172px;
                padding: 26px 28px;
                background:
                    linear-gradient(125deg, rgba(212, 166, 74, 0.11), rgba(214, 217, 224, 0.025) 62%, rgba(139, 147, 167, 0.04)),
                    rgba(15, 17, 21, 0.94);
            }

            .orion-cockpit-panel-primary .orion-cockpit-title {
                font-size: 1.44rem;
                margin-bottom: 12px;
            }

            .orion-cockpit-panel-primary .orion-cockpit-text {
                font-size: 1rem;
                max-width: 980px;
            }

            .orion-compliance-panel {
                border-color: rgba(245, 201, 106, 0.28);
                background:
                    linear-gradient(160deg, rgba(245, 201, 106, 0.12), rgba(214, 217, 224, 0.018)),
                    rgba(15, 17, 21, 0.94);
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
                font-size: 4.3rem;
                font-weight: 820;
                line-height: 1;
                margin: 13px 0 13px;
            }

            .orion-score-status {
                color: var(--orion-gold-accent);
                font-size: 0.84rem;
                font-weight: 820;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .orion-score-row {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
                margin-bottom: 10px;
            }

            .orion-risk-posture {
                position: relative;
                overflow: hidden;
            }

            .orion-risk-posture::after {
                content: "";
                position: absolute;
                inset: 0 0 auto 0;
                height: 3px;
                background: var(--orion-posture-color, var(--orion-gold));
            }

            .orion-risk-posture-low {
                --orion-posture-color: #67C587;
                border-color: rgba(103, 197, 135, 0.30);
            }

            .orion-risk-posture-moderate {
                --orion-posture-color: #F5C96A;
                border-color: rgba(245, 201, 106, 0.34);
            }

            .orion-risk-posture-elevated {
                --orion-posture-color: #D8954D;
                border-color: rgba(216, 149, 77, 0.34);
            }

            .orion-risk-posture-critical {
                --orion-posture-color: #C45F5F;
                border-color: rgba(196, 95, 95, 0.46);
            }

            .orion-posture-status {
                color: var(--orion-posture-color, var(--orion-gold-accent));
                font-size: 1.42rem;
                font-weight: 820;
                line-height: 1.15;
                margin: 12px 0 10px;
            }

            .orion-posture-count {
                color: var(--orion-muted);
                font-size: 0.88rem;
                line-height: 1.45;
                margin-bottom: 12px;
            }

            .orion-alert-list {
                display: grid;
                gap: 10px;
            }

            .orion-alert-panel {
                min-height: 204px;
            }

            .orion-alert-item {
                border: 1px solid rgba(212, 166, 74, 0.13);
                border-radius: 8px;
                background: rgba(214, 217, 224, 0.035);
                padding: 13px 14px;
            }

            .orion-alert-category {
                color: var(--orion-gold-accent);
                font-size: 0.68rem;
                font-weight: 820;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .orion-alert-title {
                color: var(--orion-silver);
                font-size: 0.92rem;
                font-weight: 780;
                margin: 8px 0 5px;
            }

            .orion-alert-message {
                color: var(--orion-muted);
                font-size: 0.85rem;
                line-height: 1.45;
            }

            .orion-status-message {
                border: 1px solid rgba(212, 166, 74, 0.14);
                border-radius: 8px;
                background:
                    linear-gradient(135deg, rgba(212, 166, 74, 0.06), rgba(214, 217, 224, 0.018)),
                    rgba(15, 17, 21, 0.86);
                padding: 15px 17px;
                margin: 12px 0 16px;
                box-shadow: 0 14px 32px rgba(0, 0, 0, 0.22);
            }

            .orion-status-message-warning {
                border-color: rgba(245, 201, 106, 0.32);
                background:
                    linear-gradient(135deg, rgba(212, 166, 74, 0.10), rgba(214, 217, 224, 0.018)),
                    rgba(15, 17, 21, 0.88);
            }

            .orion-status-message-success {
                border-color: rgba(139, 147, 167, 0.30);
            }

            .orion-status-message-error {
                border-color: rgba(196, 95, 95, 0.48);
                background:
                    linear-gradient(135deg, rgba(196, 95, 95, 0.12), rgba(214, 217, 224, 0.018)),
                    rgba(15, 17, 21, 0.88);
            }

            .orion-status-title {
                color: var(--orion-silver);
                font-size: 0.92rem;
                font-weight: 790;
                line-height: 1.3;
                margin-bottom: 5px;
            }

            .orion-status-text {
                color: var(--orion-muted-strong);
                font-size: 0.9rem;
                line-height: 1.48;
                margin: 0;
            }

            .orion-loading {
                position: relative;
                border: 1px solid rgba(212, 166, 74, 0.16);
                border-radius: 8px;
                background: rgba(15, 17, 21, 0.84);
                color: var(--orion-muted-strong);
                font-size: 0.9rem;
                line-height: 1.4;
                margin: 10px 0 16px;
                padding: 14px 16px 14px 42px;
                box-shadow: 0 14px 32px rgba(0, 0, 0, 0.22);
            }

            .orion-loading::before {
                content: "";
                position: absolute;
                left: 16px;
                top: 50%;
                width: 12px;
                height: 12px;
                margin-top: -6px;
                border-radius: 999px;
                border: 2px solid rgba(245, 201, 106, 0.16);
                border-top-color: var(--orion-gold-accent);
                animation: orion-spin 900ms linear infinite;
            }

            @keyframes orion-spin {
                to {
                    transform: rotate(360deg);
                }
            }

            .orion-badge {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                border-radius: 999px;
                padding: 5px 9px;
                border: 1px solid rgba(212, 166, 74, 0.18);
                background: rgba(214, 217, 224, 0.055);
                color: var(--orion-silver);
                font-size: 0.78rem;
                font-weight: 760;
                letter-spacing: 0;
                line-height: 1;
                white-space: nowrap;
            }

            .orion-badge-critical {
                border-color: rgba(196, 95, 95, 0.48);
                background: rgba(196, 95, 95, 0.15);
                color: #F0B4B4;
            }

            .orion-badge-high,
            .orion-badge-pending,
            .orion-badge-expired {
                border-color: rgba(245, 201, 106, 0.42);
                background: rgba(212, 166, 74, 0.13);
                color: var(--orion-gold-accent);
            }

            .orion-badge-medium,
            .orion-badge-review {
                border-color: rgba(214, 217, 224, 0.26);
                background: rgba(214, 217, 224, 0.075);
                color: var(--orion-silver);
            }

            .orion-badge-low,
            .orion-badge-active {
                border-color: rgba(139, 147, 167, 0.30);
                background: rgba(139, 147, 167, 0.095);
                color: var(--orion-muted-strong);
            }

            .orion-card-compact {
                min-height: 150px;
                padding: 17px 16px;
            }

            .orion-card-compact .orion-card-value {
                font-size: 1.04rem;
                line-height: 1.2;
            }

            .orion-card-compact .orion-card-note {
                font-size: 0.85rem;
                line-height: 1.45;
            }

            .orion-section {
                color: var(--orion-muted);
                font-size: 0.95rem;
                line-height: 1.55;
                margin: -4px 0 16px;
                max-width: 780px;
            }

            .orion-brand {
                border: 1px solid rgba(212, 166, 74, 0.2);
                border-radius: 8px;
                background:
                    linear-gradient(135deg, rgba(212, 166, 74, 0.13), rgba(214, 217, 224, 0.035)),
                    #0b0c0f;
                padding: 17px 16px 16px;
                margin-bottom: 16px;
                box-shadow: 0 22px 42px rgba(0, 0, 0, 0.36);
            }

            .orion-brand-kicker {
                color: var(--orion-gold-accent);
                font-size: 0.68rem;
                font-weight: 780;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                margin-bottom: 7px;
            }

            .orion-brand-title {
                color: var(--orion-text);
                font-size: 1.2rem;
                font-weight: 840;
                letter-spacing: 0;
                margin-bottom: 4px;
            }

            .orion-brand-subtitle,
            .orion-nav-caption {
                color: var(--orion-muted);
                font-size: 0.82rem;
                line-height: 1.35;
            }

            .orion-nav-caption {
                border-left: 2px solid transparent;
                margin: -0.34rem 0 0.58rem 0.26rem;
                padding: 0.1rem 0 0.1rem 0.46rem;
            }

            .orion-nav-caption-active {
                border-left-color: var(--orion-gold-accent);
                color: var(--orion-gold-accent);
                font-weight: 720;
            }

            .orion-status {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                border: 1px solid rgba(212, 166, 74, 0.28);
                background: rgba(212, 166, 74, 0.08);
                color: var(--orion-gold-accent);
                border-radius: 999px;
                padding: 6px 10px;
                font-size: 0.78rem;
                font-weight: 760;
                margin-top: 13px;
            }

            .orion-divider {
                height: 1px;
                background: linear-gradient(90deg, rgba(212, 166, 74, 0.18), rgba(214, 217, 224, 0.055));
                margin: 14px 0;
            }

            .orion-nav-section-label {
                color: var(--orion-muted);
                font-size: 0.68rem;
                font-weight: 780;
                letter-spacing: 0.09em;
                margin: 0 0 0.55rem 0.2rem;
                text-transform: uppercase;
            }

            .orion-section-break {
                margin-top: 30px;
            }

            .orion-table-note {
                color: var(--orion-muted);
                font-size: 0.9rem;
                margin-bottom: 12px;
            }

            .orion-empty-state {
                border: 1px solid rgba(212, 166, 74, 0.14);
                border-radius: 8px;
                background:
                    linear-gradient(135deg, rgba(212, 166, 74, 0.06), rgba(214, 217, 224, 0.018)),
                    rgba(15, 17, 21, 0.86);
                padding: 22px 24px;
                margin: 8px 0 18px;
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.28);
            }

            .orion-empty-kicker {
                color: var(--orion-gold-accent);
                font-size: 0.72rem;
                font-weight: 780;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 8px;
            }

            .orion-empty-title {
                color: var(--orion-silver);
                font-size: 1.08rem;
                font-weight: 790;
                line-height: 1.25;
                margin-bottom: 7px;
            }

            .orion-empty-message {
                color: var(--orion-muted-strong);
                font-size: 0.93rem;
                line-height: 1.5;
                max-width: 760px;
            }

            .orion-empty-action {
                color: var(--orion-muted);
                border-top: 1px solid rgba(212, 166, 74, 0.12);
                font-size: 0.86rem;
                line-height: 1.45;
                margin-top: 14px;
                padding-top: 12px;
            }

            div[data-testid="stForm"] {
                border: 1px solid rgba(212, 166, 74, 0.13);
                border-radius: 8px;
                background: rgba(15, 17, 21, 0.82);
                padding: 1.05rem 1.05rem 0.9rem;
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.28);
            }

            div[data-testid="stDataFrame"],
            div[data-testid="stTable"] {
                border: 1px solid rgba(212, 166, 74, 0.13);
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.26);
            }

            div[data-testid="stDataFrame"]:hover,
            div[data-testid="stTable"]:hover {
                border-color: rgba(245, 201, 106, 0.24);
            }

            .orion-table-shell {
                width: 100%;
                overflow: auto;
                border: 1px solid rgba(212, 166, 74, 0.13);
                border-radius: 8px;
                background: rgba(15, 17, 21, 0.84);
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.26);
            }

            .orion-table-shell:hover {
                border-color: rgba(245, 201, 106, 0.24);
            }

            .orion-data-table {
                width: 100%;
                border-collapse: collapse;
                min-width: 720px;
                color: var(--orion-silver);
                font-size: 0.88rem;
            }

            .orion-data-table th {
                background: #13161c;
                color: var(--orion-gold-accent);
                font-size: 0.72rem;
                font-weight: 780;
                letter-spacing: 0.06em;
                text-align: left;
                text-transform: uppercase;
                padding: 13px 14px;
                border-bottom: 1px solid rgba(212, 166, 74, 0.16);
                white-space: nowrap;
            }

            .orion-data-table td {
                padding: 13px 14px;
                border-bottom: 1px solid rgba(212, 166, 74, 0.08);
                color: var(--orion-muted-strong);
                vertical-align: middle;
            }

            .orion-data-table tbody tr {
                transition: background 140ms ease;
            }

            .orion-data-table tbody tr:hover {
                background: rgba(212, 166, 74, 0.055);
            }

            .orion-data-table tbody tr:last-child td {
                border-bottom: 0;
            }

            div[data-testid="stPlotlyChart"] {
                border: 1px solid rgba(212, 166, 74, 0.13);
                border-radius: 8px;
                background:
                    linear-gradient(180deg, rgba(245, 201, 106, 0.028), rgba(214, 217, 224, 0.008)),
                    var(--orion-panel);
                padding: 0.8rem;
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.28);
            }

            .stButton > button,
            [data-testid="stFormSubmitButton"] button {
                border-radius: 8px;
                border: 1px solid rgba(212, 166, 74, 0.42);
                background: linear-gradient(180deg, rgba(212, 166, 74, 0.18), rgba(245, 201, 106, 0.11));
                color: var(--orion-silver);
                font-weight: 760;
                min-height: 2.55rem;
                transition: border-color 160ms ease, background 160ms ease, transform 160ms ease, box-shadow 160ms ease;
            }

            .stButton > button:hover,
            [data-testid="stFormSubmitButton"] button:hover {
                border-color: rgba(245, 201, 106, 0.68);
                background: linear-gradient(180deg, rgba(212, 166, 74, 0.24), rgba(245, 201, 106, 0.16));
                color: #ffffff;
                transform: translateY(-1px);
                box-shadow: 0 12px 30px rgba(0, 0, 0, 0.24);
            }

            .stTextInput input,
            .stTextArea textarea,
            [data-baseweb="select"] > div,
            [data-testid="stDateInput"] input {
                border-radius: 8px;
                border-color: rgba(212, 166, 74, 0.16);
                background-color: rgba(214, 217, 224, 0.035);
            }

            [data-testid="stAlert"] {
                border-radius: 8px;
                border: 1px solid rgba(212, 166, 74, 0.14);
                background: rgba(15, 17, 21, 0.82);
            }

            [data-testid="stSpinner"] {
                color: var(--orion-gold-accent);
            }

            [data-testid="stSpinner"] > div {
                border-color: rgba(245, 201, 106, 0.72) rgba(245, 201, 106, 0.16) rgba(245, 201, 106, 0.16) !important;
            }

            @media (max-width: 760px) {
                .block-container {
                    padding-left: 1rem;
                    padding-right: 1rem;
                }

                .orion-hero {
                    padding: 24px 20px;
                }

                .orion-hero h1 {
                    font-size: 2rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(active: str) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="orion-brand">
                <div class="orion-brand-kicker">Vaekor Labs</div>
                <div class="orion-brand-title">ORION GRC</div>
                <div class="orion-brand-subtitle">Centro de governança</div>
                <div class="orion-status">Online em produção</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Governança, riscos e eficiência operacional para decisões executivas.")
        st.markdown('<div class="orion-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="orion-nav-section-label">Perfil ativo</div>', unsafe_allow_html=True)
        active_profile = st.selectbox(
            "Perfil Ativo",
            get_profiles(),
            index=get_profiles().index(get_active_profile()),
            key="orion_active_profile",
            label_visibility="collapsed",
        )
        st.caption(PROFILE_DESCRIPTIONS[active_profile])
        st.markdown('<div class="orion-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="orion-nav-section-label">Workspace</div>', unsafe_allow_html=True)

        for path, label, caption in NAV_ITEMS:
            if not has_permission(label, active_profile):
                continue
            st.page_link(path, label=label)
            caption_class = "orion-nav-caption orion-nav-caption-active" if label == active else "orion-nav-caption"
            st.markdown(
                f'<div class="{caption_class}">{caption}</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="orion-divider"></div>', unsafe_allow_html=True)
        st.caption("Governança corporativa, compliance e risk intelligence em uma visão integrada.")


def render_hero(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="orion-hero">
            <div class="orion-eyebrow">{eyebrow}</div>
            <h1>{title}</h1>
            <p class="orion-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_card(label: str, value: str, note: str, compact: bool = False) -> None:
    _render_orion_card(label, value, note, "", compact=compact)


def apply_chart_theme(fig, height: int = 360):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,17,21,0.86)",
        height=height,
        margin=dict(l=22, r=18, t=18, b=28),
        font=dict(family="Inter, Segoe UI, sans-serif", color="#D6D9E0", size=12),
        dragmode=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor="#0F1115",
            bordercolor="#D4A64A",
            font_size=12,
            font_color="#F4F5F7",
            font_family="Inter, Segoe UI, sans-serif",
        ),
    )
    fig.update_xaxes(
        gridcolor="rgba(214,217,224,0.04)",
        zerolinecolor="rgba(212,166,74,0.16)",
        linecolor="rgba(212,166,74,0.16)",
        showline=False,
        tickfont=dict(color="#AAB0BE"),
        title_font=dict(color="#AAB0BE"),
    )
    fig.update_yaxes(
        gridcolor="rgba(214,217,224,0.04)",
        zerolinecolor="rgba(212,166,74,0.16)",
        linecolor="rgba(212,166,74,0.16)",
        showline=False,
        tickfont=dict(color="#AAB0BE"),
        title_font=dict(color="#AAB0BE"),
    )
    return fig


def render_orion_chart(fig) -> None:
    st.plotly_chart(
        fig,
        width="stretch",
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )
