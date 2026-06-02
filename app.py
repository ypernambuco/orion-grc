import streamlit as st

from services.ui import (
    apply_theme,
    render_hero,
    render_insight_card,
    render_module_card,
    render_sidebar,
    render_status_message,
)


st.set_page_config(
    page_title="ORION GRC",
    layout="wide",
    initial_sidebar_state="expanded",
)


apply_theme()
render_sidebar("Início")
render_hero(
    "Vaekor Labs | Governança Corporativa",
    "ORION GRC",
    (
        "Centralize governança, riscos, conformidade e eficiência operacional "
        "em uma visão executiva para tomada de decisão estratégica."
    ),
)

col1, col2, col3 = st.columns(3)
with col1:
    render_insight_card(
        "Governança",
        "Controle corporativo",
        "Centralize controles, responsabilidades e obrigações corporativas em uma visão única de governança.",
    )
with col2:
    render_insight_card(
        "Risk Intelligence",
        "Gestão estratégica",
        "Priorize decisões com base em exposição a riscos, conformidade e impacto operacional.",
    )
with col3:
    render_insight_card(
        "Compliance",
        "Visão executiva",
        "Acompanhe pendências, vencimentos e pontos críticos com clareza para a liderança.",
    )

st.markdown("### Governança integrada")
st.markdown(
    '<p class="orion-section">'
    "O ORION GRC consolida documentos, riscos, responsabilidades e obrigações "
    "em uma estrutura orientada a controle, eficiência operacional e visão executiva."
    "</p>",
    unsafe_allow_html=True,
)

vision_cols = st.columns(5)
vision_items = [
    ("Documentos", "Contratos, políticas, relatórios e evidências em um fluxo corporativo único."),
    ("Riscos", "Priorização estratégica por impacto, probabilidade e criticidade operacional."),
    ("Pendências", "Acompanhamento de vencimentos, responsabilidades e obrigações em aberto."),
    ("Áreas", "Visão por unidades responsáveis, controles e compromissos organizacionais."),
    ("Auditoria", "Rastreabilidade de evidências, histórico e conformidade para governança contínua."),
]
for column, (label, note) in zip(vision_cols, vision_items):
    with column:
        render_module_card(label, label, note, compact=True)

render_status_message(
    "Governança, compliance e riscos conectados em uma leitura executiva única.",
    title="Visão integrada",
    kind="success",
)
