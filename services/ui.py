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
                min-height: 42px;
                padding: 0.62rem 0.72rem;
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
                font-size: 0.94rem;
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
            }

            div[data-testid="stMetric"] {
                border-top-color: rgba(245, 201, 106, 0.34);
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
                margin: -0.34rem 0 0.78rem 0.72rem;
            }

            .orion-nav-caption-active {
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
                margin: 16px 0;
            }

            .orion-table-note {
                color: var(--orion-muted);
                font-size: 0.9rem;
                margin-bottom: 12px;
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
            }

            .stButton > button:hover,
            [data-testid="stFormSubmitButton"] button:hover {
                border-color: rgba(245, 201, 106, 0.68);
                background: linear-gradient(180deg, rgba(212, 166, 74, 0.24), rgba(245, 201, 106, 0.16));
                color: #ffffff;
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
                <div class="orion-brand-subtitle">Governance command center</div>
                <div class="orion-status">Online em producao</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Governanca, riscos e eficiencia operacional para pequenas empresas.")
        st.markdown('<div class="orion-divider"></div>', unsafe_allow_html=True)

        for path, label, caption in NAV_ITEMS:
            st.page_link(path, label=label)
            caption_class = "orion-nav-caption orion-nav-caption-active" if label == active else "orion-nav-caption"
            st.markdown(
                f'<div class="{caption_class}">{caption}</div>',
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


def render_card(label: str, value: str, note: str, compact: bool = False) -> None:
    card_class = "orion-card orion-card-compact" if compact else "orion-card"
    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="orion-card-label">{label}</div>
            <div class="orion-card-value">{value}</div>
            <div class="orion-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_chart_theme(fig, height: int = 360):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,17,21,0.86)",
        height=height,
        margin=dict(l=22, r=18, t=28, b=28),
        font=dict(family="Inter, Segoe UI, sans-serif", color="#D6D9E0", size=12),
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
            font_family="Inter, Segoe UI, sans-serif",
        ),
    )
    fig.update_xaxes(
        gridcolor="rgba(214,217,224,0.055)",
        zerolinecolor="rgba(212,166,74,0.16)",
        linecolor="rgba(212,166,74,0.16)",
        tickfont=dict(color="#8B93A7"),
        title_font=dict(color="#8B93A7"),
    )
    fig.update_yaxes(
        gridcolor="rgba(214,217,224,0.055)",
        zerolinecolor="rgba(212,166,74,0.16)",
        linecolor="rgba(212,166,74,0.16)",
        tickfont=dict(color="#8B93A7"),
        title_font=dict(color="#8B93A7"),
    )
    return fig
