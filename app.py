import streamlit as st


st.set_page_config(
    page_title="ORION GRC",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_theme() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: #0f172a;
                color: #e5e7eb;
            }
            [data-testid="stSidebar"] {
                background: #020617;
                border-right: 1px solid #1e293b;
            }
            [data-testid="stSidebarNav"] {
                display: none;
            }
            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3,
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] span {
                color: #e5e7eb;
            }
            .orion-card {
                background: #111827;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 20px;
                min-height: 116px;
            }
            .orion-card-label {
                color: #94a3b8;
                font-size: 0.85rem;
                margin-bottom: 10px;
            }
            .orion-card-value {
                color: #f8fafc;
                font-size: 1.35rem;
                font-weight: 700;
                line-height: 1.25;
            }
            .orion-hero {
                border-bottom: 1px solid #1e293b;
                padding: 10px 0 24px;
                margin-bottom: 18px;
            }
            .orion-subtitle {
                color: #94a3b8;
                font-size: 1rem;
                margin-top: -8px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_theme()

with st.sidebar:
    st.title("Vaekor Labs")
    st.caption("Governanca, riscos e eficiencia operacional")
    st.divider()
    st.page_link("app.py", label="Inicio")
    st.page_link("pages/dashboard.py", label="Dashboard")
    st.page_link("pages/areas.py", label="Areas")
    st.page_link("pages/documentos.py", label="Documentos")
    st.page_link("pages/riscos.py", label="Riscos")

st.markdown(
    """
    <div class="orion-hero">
        <h1>ORION GRC</h1>
        <p class="orion-subtitle">
            Sistema web para governanca, riscos, documentos e eficiencia operacional.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
col1.markdown(
    '<div class="orion-card"><div class="orion-card-label">Modulo</div>'
    '<div class="orion-card-value">Governanca</div></div>',
    unsafe_allow_html=True,
)
col2.markdown(
    '<div class="orion-card"><div class="orion-card-label">Base</div>'
    '<div class="orion-card-value">Supabase/PostgreSQL</div></div>',
    unsafe_allow_html=True,
)
col3.markdown(
    '<div class="orion-card"><div class="orion-card-label">Status</div>'
    '<div class="orion-card-value">Sem autenticacao</div></div>',
    unsafe_allow_html=True,
)

st.info("Use o menu lateral para acessar o Dashboard, Areas, Documentos e Riscos.")
