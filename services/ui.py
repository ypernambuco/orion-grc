import streamlit as st


NAV_ITEMS = [
    ("app.py", "Inicio", "Visao geral do produto"),
    ("pages/dashboard.py", "Dashboard", "Indicadores executivos"),
    ("pages/areas.py", "Areas", "Unidades de governanca"),
    ("pages/documentos.py", "Documentos", "Ciclo documental"),
    ("pages/riscos.py", "Riscos", "Matriz operacional"),
]


def apply_theme() -> None:
    st.markdown(
        """
        <style>
            :root {
                --orion-bg: #0b1120;
                --orion-panel: #111827;
                --orion-panel-soft: #162033;
                --orion-border: #233047;
                --orion-text: #f8fafc;
                --orion-muted: #94a3b8;
                --orion-blue: #38bdf8;
                --orion-green: #22c55e;
                --orion-amber: #f59e0b;
            }

            .stApp {
                background: var(--orion-bg);
                color: var(--orion-text);
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1240px;
            }

            [data-testid="stSidebar"] {
                background: #060b16;
                border-right: 1px solid var(--orion-border);
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

            h1, h2, h3 {
                letter-spacing: 0;
            }

            div[data-testid="stMetric"],
            .orion-card {
                background: linear-gradient(180deg, #121b2e 0%, #0f172a 100%);
                border: 1px solid var(--orion-border);
                border-radius: 8px;
                padding: 18px;
                box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
            }

            div[data-testid="stMetric"] label {
                color: var(--orion-muted);
            }

            div[data-testid="stMetricValue"] {
                color: var(--orion-text);
            }

            .orion-hero {
                border: 1px solid var(--orion-border);
                border-radius: 8px;
                background:
                    linear-gradient(120deg, rgba(56, 189, 248, 0.12), rgba(34, 197, 94, 0.07)),
                    #0f172a;
                padding: 26px 28px;
                margin-bottom: 22px;
            }

            .orion-eyebrow {
                color: var(--orion-blue);
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 8px;
            }

            .orion-hero h1 {
                margin: 0;
                font-size: 2.3rem;
                line-height: 1.1;
            }

            .orion-subtitle {
                color: #cbd5e1;
                font-size: 1rem;
                line-height: 1.55;
                max-width: 820px;
                margin: 12px 0 0;
            }

            .orion-card-label {
                color: var(--orion-muted);
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                margin-bottom: 10px;
            }

            .orion-card-value {
                color: var(--orion-text);
                font-size: 1.35rem;
                font-weight: 750;
                line-height: 1.25;
            }

            .orion-card-note {
                color: var(--orion-muted);
                font-size: 0.9rem;
                line-height: 1.45;
                margin-top: 10px;
            }

            .orion-section {
                color: var(--orion-muted);
                font-size: 0.95rem;
                margin: -8px 0 16px;
            }

            .orion-brand {
                border: 1px solid var(--orion-border);
                border-radius: 8px;
                background: #0b1220;
                padding: 16px;
                margin-bottom: 14px;
            }

            .orion-brand-title {
                color: var(--orion-text);
                font-size: 1.15rem;
                font-weight: 800;
                margin-bottom: 4px;
            }

            .orion-brand-subtitle,
            .orion-nav-caption {
                color: var(--orion-muted);
                font-size: 0.84rem;
                line-height: 1.35;
            }

            .orion-status {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                border: 1px solid rgba(34, 197, 94, 0.28);
                background: rgba(34, 197, 94, 0.08);
                color: #bbf7d0;
                border-radius: 999px;
                padding: 6px 10px;
                font-size: 0.78rem;
                font-weight: 700;
                margin-top: 12px;
            }

            .orion-divider {
                height: 1px;
                background: var(--orion-border);
                margin: 14px 0;
            }

            .orion-table-note {
                color: var(--orion-muted);
                font-size: 0.9rem;
                margin-bottom: 12px;
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
                <div class="orion-brand-title">ORION GRC</div>
                <div class="orion-brand-subtitle">Vaekor Labs</div>
                <div class="orion-status">Online em producao</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Governanca, riscos e eficiencia operacional para pequenas empresas.")
        st.markdown('<div class="orion-divider"></div>', unsafe_allow_html=True)

        for path, label, caption in NAV_ITEMS:
            prefix = "> " if label == active else ""
            st.page_link(path, label=f"{prefix}{label}")
            st.markdown(
                f'<div class="orion-nav-caption">{caption}</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="orion-divider"></div>', unsafe_allow_html=True)
        st.caption("Demo SaaS sem autenticacao nesta versao.")


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


def render_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="orion-card">
            <div class="orion-card-label">{label}</div>
            <div class="orion-card-value">{value}</div>
            <div class="orion-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
