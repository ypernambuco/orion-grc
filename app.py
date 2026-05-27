import streamlit as st

from services.ui import apply_theme, render_card, render_hero, render_sidebar


st.set_page_config(
    page_title="ORION GRC",
    layout="wide",
    initial_sidebar_state="expanded",
)


apply_theme()
render_sidebar("Início")
render_hero(
    "Vaekor Labs | Demonstração",
    "ORION GRC",
    (
        "Centralize documentos, riscos e pendências operacionais em uma visão "
        "executiva para governança, auditoria e tomada de decisão."
    ),
)

col1, col2, col3 = st.columns(3)
with col1:
    render_card(
        "Produto",
        "Governança operacional",
        "Demonstração SaaS para pequenas empresas acompanharem controles, vencimentos e riscos.",
    )
with col2:
    render_card(
        "Base técnica",
        "Streamlit + Supabase",
        "Arquitetura simples, online e pronta para evoluir para acesso por perfil.",
    )
with col3:
    render_card(
        "Status",
        "Demonstração sem login",
        "Versão executiva do MVP, sem autenticação, IA ou controle de acesso.",
    )

st.markdown("### Visão do produto")
st.markdown(
    '<p class="orion-section">'
    "O ORION GRC ajuda empresas pequenas a organizar rotinas de governança sem "
    "depender de planilhas soltas, pastas desconectadas e controles manuais."
    "</p>",
    unsafe_allow_html=True,
)

vision_cols = st.columns(5)
vision_items = [
    ("Documentos", "Contratos, políticas, relatórios e evidências em um fluxo único."),
    ("Riscos", "Priorização por impacto, probabilidade e classificação operacional."),
    ("Pendências", "Acompanhamento de vencimentos e itens fora do fluxo esperado."),
    ("Áreas", "Visão por Financeiro, Jurídico, RH, TI e Operações."),
    ("Auditoria", "Base preparada para evidências, histórico e trilhas futuras."),
]
for column, (label, note) in zip(vision_cols, vision_items):
    with column:
        render_card(label, label, note, compact=True)

st.info("Use o menu lateral para acessar Dashboard, Áreas, Documentos e Riscos.")
