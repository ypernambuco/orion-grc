import pandas as pd
import streamlit as st

from services.access_control import require_permission
from services.supabase_client import get_supabase
from services.ui import (
    apply_theme,
    display_label,
    filter_non_corporate_area_rows,
    render_area_operational_card,
    render_data_table,
    render_empty_state,
    render_hero,
    render_insight_card,
    render_priority_card,
    render_sidebar,
)


st.set_page_config(page_title="ORION GRC | Áreas", layout="wide")


def load_areas() -> pd.DataFrame:
    supabase = get_supabase()
    if supabase is None:
        return pd.DataFrame()
    try:
        data = supabase.table("areas").select("*").order("nome").execute().data
    except Exception as exc:
        st.error(f"Não foi possível carregar as áreas: {exc}")
        return pd.DataFrame()
    return filter_non_corporate_area_rows(pd.DataFrame(data), "nome")


def load_area_operational_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    supabase = get_supabase()
    if supabase is None:
        return pd.DataFrame(), pd.DataFrame()
    try:
        documentos = (
            supabase.table("documentos")
            .select("id, area_id, status, vencimento")
            .execute()
            .data
        )
        riscos = (
            supabase.table("riscos")
            .select("id, area_id, classificacao")
            .execute()
            .data
        )
    except Exception as exc:
        st.error(f"Não foi possível carregar os indicadores por área: {exc}")
        return pd.DataFrame(), pd.DataFrame()
    return pd.DataFrame(documentos), pd.DataFrame(riscos)


def build_area_intelligence(
    areas_df: pd.DataFrame,
    documentos_df: pd.DataFrame,
    riscos_df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "nome",
        "total_documentos",
        "documentos_pendentes",
        "documentos_vencidos",
        "total_riscos",
        "riscos_criticos",
        "eficiencia",
    ]
    if areas_df.empty or "id" not in areas_df or "nome" not in areas_df:
        return pd.DataFrame(columns=columns)

    document_metrics = pd.DataFrame(
        columns=[
            "area_id",
            "total_documentos",
            "documentos_pendentes",
            "documentos_vencidos",
            "documentos_fora_do_fluxo",
        ]
    )
    if not documentos_df.empty and "area_id" in documentos_df:
        docs = documentos_df.copy()
        status = docs.get("status", pd.Series(index=docs.index, dtype=str))
        vencimento = docs.get("vencimento", pd.Series(index=docs.index, dtype=str))
        docs["pendente"] = status.fillna("").astype(str).str.lower().eq("pendente")
        docs["vencido"] = (
            pd.to_datetime(vencimento, errors="coerce").dt.date
            < pd.Timestamp.today().date()
        )
        docs["fora_do_fluxo"] = docs["pendente"] | docs["vencido"]
        document_metrics = (
            docs.groupby("area_id", as_index=False)
            .agg(
                total_documentos=("id", "count"),
                documentos_pendentes=("pendente", "sum"),
                documentos_vencidos=("vencido", "sum"),
                documentos_fora_do_fluxo=("fora_do_fluxo", "sum"),
            )
        )

    risk_metrics = pd.DataFrame(
        columns=["area_id", "total_riscos", "riscos_criticos"]
    )
    if not riscos_df.empty and "area_id" in riscos_df:
        risks = riscos_df.copy()
        classificacao = risks.get(
            "classificacao",
            pd.Series(index=risks.index, dtype=str),
        )
        risks["critico"] = (
            classificacao.fillna("").astype(str).str.lower().eq("critico")
        )
        risk_metrics = (
            risks.groupby("area_id", as_index=False)
            .agg(
                total_riscos=("id", "count"),
                riscos_criticos=("critico", "sum"),
            )
        )

    intelligence = (
        areas_df[["id", "nome"]]
        .merge(document_metrics, left_on="id", right_on="area_id", how="left")
        .drop(columns=["area_id"], errors="ignore")
        .merge(risk_metrics, left_on="id", right_on="area_id", how="left")
        .drop(columns=["area_id"], errors="ignore")
    )
    metric_columns = [
        "total_documentos",
        "documentos_pendentes",
        "documentos_vencidos",
        "documentos_fora_do_fluxo",
        "total_riscos",
        "riscos_criticos",
    ]
    intelligence[metric_columns] = (
        intelligence[metric_columns].fillna(0).astype(int)
    )
    intelligence["eficiencia"] = (
        (
            (
                intelligence["total_documentos"]
                - intelligence["documentos_fora_do_fluxo"]
            )
            / intelligence["total_documentos"].replace(0, pd.NA)
        )
        * 100
    ).fillna(0).round(1)
    intelligence["nome"] = intelligence["nome"].apply(display_label)
    return intelligence[columns].sort_values(
        ["eficiencia", "documentos_pendentes", "nome"],
        ascending=[False, True, True],
    )


def generate_area_rankings(area_intelligence: pd.DataFrame) -> list[dict[str, str]]:
    if area_intelligence.empty:
        return []

    best = area_intelligence.sort_values(
        ["eficiencia", "documentos_pendentes", "riscos_criticos"],
        ascending=[False, True, True],
    ).iloc[0]
    attention = area_intelligence.sort_values(
        ["eficiencia", "riscos_criticos", "documentos_pendentes"],
        ascending=[True, False, False],
    ).iloc[0]
    critical_risk = area_intelligence.sort_values(
        ["riscos_criticos", "total_riscos", "eficiencia"],
        ascending=[False, False, True],
    ).iloc[0]
    attention_priority = (
        "Alta Prioridade"
        if float(attention["eficiencia"]) < 70
        or int(attention["riscos_criticos"])
        or int(attention["documentos_vencidos"])
        else "Média Prioridade"
        if float(attention["eficiencia"]) < 90
        or int(attention["documentos_pendentes"])
        else "Baixa Prioridade"
    )

    return [
        {
            "priority": "Baixa Prioridade",
            "title": f"Melhor desempenho: {best['nome']}",
            "message": f"{best['eficiencia']}% de eficiência e {best['documentos_pendentes']} pendência(s).",
        },
        {
            "priority": attention_priority,
            "title": f"Maior atenção: {attention['nome']}",
            "message": f"{attention['eficiencia']}% de eficiência, {attention['documentos_pendentes']} pendência(s) e {attention['documentos_vencidos']} vencido(s).",
        },
        {
            "priority": (
                "Alta Prioridade"
                if int(critical_risk["riscos_criticos"])
                else "Baixa Prioridade"
            ),
            "title": f"Exposição crítica: {critical_risk['nome']}",
            "message": f"{critical_risk['riscos_criticos']} risco(s) crítico(s) entre {critical_risk['total_riscos']} risco(s).",
        },
    ]


def generate_area_insights(area_intelligence: pd.DataFrame) -> list[dict[str, str]]:
    if area_intelligence.empty:
        return []

    lowest = area_intelligence.sort_values("eficiencia").iloc[0]
    risk_leader = area_intelligence.sort_values(
        ["total_riscos", "riscos_criticos"],
        ascending=False,
    ).iloc[0]
    best = area_intelligence.sort_values(
        ["eficiencia", "documentos_pendentes"],
        ascending=[False, True],
    ).iloc[0]
    pending = area_intelligence.sort_values(
        ["documentos_pendentes", "documentos_vencidos"],
        ascending=False,
    ).iloc[0]

    insights = [
        {
            "label": "Eficiência operacional",
            "title": str(lowest["nome"]),
            "message": f"Apresenta a menor eficiência operacional, com {lowest['eficiencia']}%.",
        },
        {
            "label": "Concentração de riscos",
            "title": str(risk_leader["nome"]),
            "message": f"Concentra a maior quantidade de riscos, com {risk_leader['total_riscos']} registro(s).",
        },
        {
            "label": "Melhor desempenho",
            "title": str(best["nome"]),
            "message": f"Mantém {best['eficiencia']}% de eficiência e {best['documentos_pendentes']} pendência(s).",
        },
    ]
    if int(pending["documentos_pendentes"]):
        insights.append(
            {
                "label": "Pendências documentais",
                "title": str(pending["nome"]),
                "message": f"Possui {pending['documentos_pendentes']} documento(s) pendente(s) que exigem acompanhamento.",
            }
        )
    return insights[:6]


def generate_area_positive_highlights(
    area_intelligence: pd.DataFrame,
) -> list[dict[str, str]]:
    if area_intelligence.empty:
        return []

    highlights = []
    highlighted_areas = set()
    for _, area in area_intelligence[
        area_intelligence["eficiencia"].eq(100)
    ].head(2).iterrows():
        highlights.append(
            {
                "label": "Desempenho máximo",
                "title": str(area["nome"]),
                "message": "Mantém 100% de eficiência documental.",
            }
        )
        highlighted_areas.add(str(area["nome"]))

    no_critical_risks = area_intelligence[
        area_intelligence["riscos_criticos"].eq(0)
        & area_intelligence["total_riscos"].gt(0)
        & ~area_intelligence["nome"].isin(highlighted_areas)
    ].sort_values(["eficiencia", "nome"], ascending=[False, True])
    if not no_critical_risks.empty:
        area = no_critical_risks.iloc[0]
        highlights.append(
            {
                "label": "Riscos críticos controlados",
                "title": str(area["nome"]),
                "message": f"Não possui riscos críticos entre {area['total_riscos']} risco(s) registrado(s).",
            }
        )
        highlighted_areas.add(str(area["nome"]))

    healthy_documents = area_intelligence[
        area_intelligence["eficiencia"].ge(70)
        & area_intelligence["total_documentos"].gt(0)
        & area_intelligence["documentos_pendentes"].eq(0)
        & area_intelligence["documentos_vencidos"].eq(0)
        & ~area_intelligence["nome"].isin(highlighted_areas)
    ].sort_values(["documentos_pendentes", "nome"])
    if not healthy_documents.empty:
        area = healthy_documents.iloc[0]
        highlights.append(
            {
                "label": "Saúde documental",
                "title": str(area["nome"]),
                "message": f"Opera com {area['eficiencia']}% de eficiência documental.",
            }
        )
    return highlights[:4]


apply_theme()
render_sidebar("Áreas")
require_permission("Áreas")
render_hero(
    "Unidades de governança",
    "Áreas corporativas",
    "Cadastre e acompanhe as áreas responsáveis por documentos, controles, riscos e pendências.",
)

supabase = get_supabase()
if supabase is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env ou em st.secrets.")

form_col, insight_col = st.columns([1.1, 0.9])
with form_col:
    st.markdown("### Nova área")
    st.markdown(
        '<p class="orion-section">Use áreas como responsáveis operacionais por documentos, controles e riscos.</p>',
        unsafe_allow_html=True,
    )
    with st.form("form_area", clear_on_submit=True):
        nome = st.text_input("Nome da área")
        submitted = st.form_submit_button("Cadastrar área")

        if submitted:
            if supabase is None:
                st.error("Supabase não configurado.")
            elif not nome.strip():
                st.error("Informe o nome da área.")
            else:
                try:
                    supabase.table("areas").insert({"nome": nome.strip()}).execute()
                    st.success("Área cadastrada com sucesso.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Não foi possível cadastrar a área: {exc}")

with insight_col:
    st.markdown("### Gestão por área")
    st.markdown(
        '<p class="orion-section">'
        "Acompanhe eficiência documental, pendências e exposição a riscos de cada unidade "
        "para orientar prioridades operacionais."
        "</p>",
        unsafe_allow_html=True,
    )

with st.spinner("Carregando inteligência operacional por área..."):
    areas_df = load_areas()
    documentos_df, riscos_df = load_area_operational_data()
area_intelligence = build_area_intelligence(areas_df, documentos_df, riscos_df)
area_rankings = generate_area_rankings(area_intelligence)
area_insights = generate_area_insights(area_intelligence)
area_highlights = generate_area_positive_highlights(area_intelligence)

st.markdown('<div class="orion-section-break"></div>', unsafe_allow_html=True)
st.markdown("## Visão operacional por área")
st.markdown(
    '<p class="orion-section">Indicadores consolidados para comparar cobertura documental, pendências e exposição a riscos.</p>',
    unsafe_allow_html=True,
)
if area_intelligence.empty:
    render_empty_state(
        "Inteligência por área ainda indisponível",
        "Cadastre áreas para habilitar indicadores, ranking operacional e insights automáticos.",
        "A primeira área cadastrada já será incluída na visão operacional.",
    )
else:
    for offset in range(0, len(area_intelligence), 3):
        area_cols = st.columns(3)
        for column, (_, area) in zip(
            area_cols,
            area_intelligence.iloc[offset : offset + 3].iterrows(),
        ):
            with column:
                render_area_operational_card(area.to_dict())

    st.markdown("### Ranking operacional")
    st.markdown(
        '<p class="orion-section">Comparação entre melhor desempenho, maior necessidade de atenção e exposição crítica.</p>',
        unsafe_allow_html=True,
    )
    ranking_cols = st.columns(3)
    for column, ranking in zip(ranking_cols, area_rankings):
        with column:
            render_priority_card(
                ranking["priority"],
                ranking["title"],
                ranking["message"],
            )

    st.markdown("### Area Intelligence")
    st.markdown(
        '<p class="orion-section">Leituras automáticas geradas a partir dos indicadores atuais de cada área.</p>',
        unsafe_allow_html=True,
    )
    insight_cols = st.columns(len(area_insights))
    for column, insight in zip(insight_cols, area_insights):
        with column:
            render_insight_card(
                insight["label"],
                insight["title"],
                insight["message"],
            )

    st.markdown("### Destaques positivos")
    st.markdown(
        '<p class="orion-section">Práticas e unidades com sinais favoráveis para preservação e referência interna.</p>',
        unsafe_allow_html=True,
    )
    if area_highlights:
        highlight_cols = st.columns(len(area_highlights))
        for column, highlight in zip(highlight_cols, area_highlights):
            with column:
                render_insight_card(
                    highlight["label"],
                    highlight["title"],
                    highlight["message"],
                )
    else:
        render_empty_state(
            "Destaques positivos ainda indisponíveis",
            "Nenhuma área atingiu os critérios atuais de destaque operacional.",
            "Regularize pendências, documentos vencidos e riscos críticos para elevar o desempenho.",
        )

st.markdown('<div class="orion-section-break"></div>', unsafe_allow_html=True)
st.markdown("### Áreas cadastradas")
st.markdown(
    '<p class="orion-table-note">Resumo operacional das áreas usadas nos filtros, formulários e indicadores.</p>',
    unsafe_allow_html=True,
)
if area_intelligence.empty:
    render_empty_state(
        "Nenhuma área cadastrada",
        "A base de governança ainda não possui áreas responsáveis. Cadastre as unidades operacionais para estruturar documentos, riscos e indicadores.",
        "Comece pela área responsável pelo maior volume de controles ou documentos críticos.",
    )
else:
    render_data_table(
        area_intelligence,
        [
            "nome",
            "total_documentos",
            "documentos_pendentes",
            "documentos_vencidos",
            "total_riscos",
            "riscos_criticos",
            "eficiencia",
        ],
    )
