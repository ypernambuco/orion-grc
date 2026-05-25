import streamlit as st

from services.ui import apply_theme, render_card, render_hero, render_sidebar


st.set_page_config(
    page_title="ORION GRC",
    layout="wide",
    initial_sidebar_state="expanded",
)


apply_theme()
render_sidebar("Inicio")
render_hero(
    "Vaekor Labs | Product Demo",
    "ORION GRC",
    (
        "Centralize documentos, riscos e pendencias operacionais em uma visao "
        "executiva para governanca, auditoria e tomada de decisao."
    ),
)

col1, col2, col3 = st.columns(3)
with col1:
    render_card(
        "Produto",
        "Governanca operacional",
        "Demo SaaS para pequenas empresas acompanharem controles, vencimentos e riscos.",
    )
with col2:
    render_card(
        "Base tecnica",
        "Streamlit + Supabase",
        "Arquitetura simples, online e pronta para evoluir para acesso por perfil.",
    )
with col3:
    render_card(
        "Status",
        "Produzido sem login",
        "Versao apresentavel do MVP, sem autenticacao, IA ou controle de acesso.",
    )

st.markdown("### Visao do produto")
st.markdown(
    '<p class="orion-section">'
    "O ORION GRC ajuda empresas pequenas a organizar rotinas de governanca sem "
    "depender de planilhas soltas, pastas desconectadas e controles manuais."
    "</p>",
    unsafe_allow_html=True,
)

vision_cols = st.columns(5)
vision_items = [
    ("Documentos", "Contratos, politicas, relatorios e evidencias em um fluxo unico."),
    ("Riscos", "Priorizacao por impacto, probabilidade e classificacao operacional."),
    ("Pendencias", "Acompanhamento de vencimentos e itens fora do fluxo esperado."),
    ("Areas", "Visao por Financeiro, Juridico, RH, TI e Operacoes."),
    ("Auditoria", "Base preparada para evidencias, historico e trilhas futuras."),
]
for column, (label, note) in zip(vision_cols, vision_items):
    with column:
        render_card(label, label, note)

st.info("Use o menu lateral para acessar Dashboard, Areas, Documentos e Riscos.")
