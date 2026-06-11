import pandas as pd
import streamlit as st

from services.access_control import require_permission
from services.supabase_client import get_supabase
from services.ui import (
    apply_theme,
    badge_html,
    display_label,
    filter_non_corporate_area_rows,
    is_non_corporate_area_name,
    render_data_table,
    render_empty_state,
    render_hero,
    render_insight_card,
    render_kpi_card,
    render_priority_card,
    render_sidebar,
)


st.set_page_config(page_title="ORION GRC | Riscos", layout="wide")


def classify_risk(score: int) -> str:
    if score <= 4:
        return "Baixo"
    if score <= 9:
        return "Medio"
    if score <= 15:
        return "Alto"
    return "Critico"


def load_areas() -> list[dict]:
    supabase = get_supabase()
    if supabase is None:
        return []
    try:
        data = supabase.table("areas").select("id, nome").order("nome").execute().data
    except Exception as exc:
        st.error(f"Não foi possível carregar as áreas: {exc}")
        return []
    return [
        area
        for area in data
        if not is_non_corporate_area_name(area.get("nome"))
    ]


def load_riscos() -> pd.DataFrame:
    supabase = get_supabase()
    if supabase is None:
        return pd.DataFrame()
    try:
        data = (
            supabase.table("riscos")
            .select("id, descricao, probabilidade, impacto, risco, classificacao, areas(nome)")
            .order("risco", desc=True)
            .execute()
            .data
        )
    except Exception as exc:
        st.error(f"Não foi possível carregar os riscos: {exc}")
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if not df.empty and "areas" in df:
        df["area"] = df["areas"].apply(
            lambda item: item.get("nome") if isinstance(item, dict) else "Sem área"
        )
    return filter_non_corporate_area_rows(df, "area")


def enrich_riscos(riscos_df: pd.DataFrame) -> pd.DataFrame:
    if riscos_df.empty:
        return riscos_df.copy()

    enriched = riscos_df.copy()
    classification = enriched.get(
        "classificacao",
        pd.Series(index=enriched.index, dtype=str),
    )
    enriched["nivel"] = (
        classification.fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"médio": "medio", "crítico": "critico"})
    )
    enriched["score"] = pd.to_numeric(
        enriched.get("risco", pd.Series(index=enriched.index, dtype=float)),
        errors="coerce",
    ).fillna(0)
    return enriched


def calculate_risk_metrics(riscos_df: pd.DataFrame) -> dict[str, object]:
    enriched = enrich_riscos(riscos_df)
    total = len(enriched)
    if not total:
        return {
            "total": 0,
            "criticos": 0,
            "altos": 0,
            "medios": 0,
            "baixos": 0,
            "controlados": 0,
            "exposicao_media": 0,
            "data": enriched,
        }

    counts = enriched["nivel"].value_counts()
    baixos = int(counts.get("baixo", 0))
    medios = int(counts.get("medio", 0))
    return {
        "total": total,
        "criticos": int(counts.get("critico", 0)),
        "altos": int(counts.get("alto", 0)),
        "medios": medios,
        "baixos": baixos,
        "controlados": baixos + medios,
        "exposicao_media": round(float(enriched["score"].mean()), 1),
        "data": enriched,
    }


def _risk_area_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    if enriched.empty or "area" not in enriched:
        return pd.DataFrame()

    summary = (
        enriched.assign(
            critico=enriched["nivel"].eq("critico"),
            alto=enriched["nivel"].eq("alto"),
        )
        .groupby("area", as_index=False)
        .agg(
            total_riscos=("id", "count"),
            riscos_criticos=("critico", "sum"),
            riscos_altos=("alto", "sum"),
            exposicao_media=("score", "mean"),
        )
    )
    summary["exposicao_media"] = summary["exposicao_media"].round(1)
    return summary


def generate_risk_insights(metrics: dict[str, object]) -> list[dict[str, str]]:
    enriched = metrics["data"]
    if enriched.empty:
        return []

    insights = []
    area_summary = _risk_area_summary(enriched)
    if not area_summary.empty:
        concentration = area_summary.sort_values(
            ["total_riscos", "riscos_criticos", "area"],
            ascending=[False, False, True],
        ).iloc[0]
        concentration_share = round(
            (int(concentration["total_riscos"]) / int(metrics["total"])) * 100,
            1,
        )
        insights.append(
            {
                "label": "Concentração de riscos",
                "title": display_label(str(concentration["area"])),
                "message": f"Concentra {concentration_share}% da matriz, com {concentration['total_riscos']} risco(s).",
            }
        )

        if int(metrics["criticos"]):
            critical_leader = area_summary.sort_values(
                ["riscos_criticos", "total_riscos", "area"],
                ascending=[False, False, True],
            ).iloc[0]
            insights.append(
                {
                    "label": "Criticidade por área",
                    "title": display_label(str(critical_leader["area"])),
                    "message": f"Possui {critical_leader['riscos_criticos']} risco(s) crítico(s), a maior concentração atual.",
                }
            )

        lowest_exposure = area_summary.sort_values(
            ["exposicao_media", "total_riscos", "area"],
            ascending=[True, False, True],
        ).iloc[0]
        insights.append(
            {
                "label": "Menor exposição",
                "title": display_label(str(lowest_exposure["area"])),
                "message": f"Apresenta exposição média de {lowest_exposure['exposicao_media']} pontos.",
            }
        )

    distribution = (
        enriched["nivel"]
        .value_counts()
        .rename_axis("nivel")
        .reset_index(name="quantidade")
        .sort_values(["quantidade", "nivel"], ascending=[False, True])
    )
    if not distribution.empty:
        dominant = distribution.iloc[0]
        dominant_share = round(
            (int(dominant["quantidade"]) / int(metrics["total"])) * 100,
            1,
        )
        insights.append(
            {
                "label": "Distribuição da matriz",
                "title": display_label(str(dominant["nivel"]).title()),
                "message": f"É o nível predominante, representando {dominant_share}% dos riscos.",
            }
        )

    if not area_summary.empty:
        top_share = round(
            (int(area_summary["total_riscos"].max()) / int(metrics["total"])) * 100,
            1,
        )
        insights.append(
            {
                "label": "Tendência operacional",
                "title": "Concentração elevada" if top_share >= 40 else "Distribuição equilibrada",
                "message": f"A área mais exposta representa {top_share}% dos riscos registrados.",
            }
        )
    return insights[:6]


def generate_risk_priorities(metrics: dict[str, object]) -> list[dict[str, str]]:
    enriched = metrics["data"]
    if enriched.empty:
        return []

    priorities = []
    if int(metrics["criticos"]):
        priorities.append(
            {
                "priority": "Alta Prioridade",
                "title": "Tratar riscos críticos ativos",
                "message": f"{metrics['criticos']} risco(s) crítico(s) exigem resposta e acompanhamento.",
            }
        )

    area_summary = _risk_area_summary(enriched)
    if int(metrics["criticos"]) >= 2 and not area_summary.empty:
        critical_leader = area_summary.sort_values(
            ["riscos_criticos", "total_riscos", "area"],
            ascending=[False, False, True],
        ).iloc[0]
        critical_share = round(
            (int(critical_leader["riscos_criticos"]) / int(metrics["criticos"])) * 100,
            1,
        )
        if critical_share >= 50:
            priorities.append(
                {
                    "priority": "Alta Prioridade",
                    "title": f"Reduzir criticidade em {display_label(str(critical_leader['area']))}",
                    "message": f"A área concentra {critical_share}% dos riscos críticos ativos.",
                }
            )

    high_share = round((int(metrics["altos"]) / int(metrics["total"])) * 100, 1)
    if int(metrics["altos"]) and high_share >= 25:
        priorities.append(
            {
                "priority": "Média Prioridade",
                "title": "Acompanhar riscos altos",
                "message": f"{metrics['altos']} risco(s) alto(s) representam {high_share}% da matriz.",
            }
        )

    controlled_share = round(
        (int(metrics["controlados"]) / int(metrics["total"])) * 100,
        1,
    )
    if controlled_share >= 50:
        priorities.append(
            {
                "priority": "Baixa Prioridade",
                "title": "Preservar níveis controlados",
                "message": f"{controlled_share}% da matriz permanece nos níveis baixo ou médio.",
            }
        )
    if not priorities:
        priorities.append(
            {
                "priority": "Média Prioridade",
                "title": "Revisar exposição da matriz",
                "message": "A distribuição atual requer acompanhamento sem uma prioridade dominante.",
            }
        )
    return priorities[:4]


def generate_risk_positive_highlights(
    metrics: dict[str, object],
) -> list[dict[str, str]]:
    enriched = metrics["data"]
    if enriched.empty:
        return []

    highlights = []
    area_summary = _risk_area_summary(enriched)
    if not area_summary.empty:
        areas_without_critical = area_summary[area_summary["riscos_criticos"].eq(0)]
        if not areas_without_critical.empty:
            names = ", ".join(
                display_label(str(name))
                for name in areas_without_critical.sort_values("area")["area"].head(3)
            )
            highlights.append(
                {
                    "label": "Áreas sem riscos críticos",
                    "title": str(len(areas_without_critical)),
                    "message": f"{names} não possuem criticidade máxima registrada.",
                }
            )

    outside_critical = int(metrics["total"]) - int(metrics["criticos"])
    outside_critical_share = round(
        (outside_critical / int(metrics["total"])) * 100,
        1,
    )
    highlights.append(
        {
            "label": "Matriz fora da faixa crítica",
            "title": f"{outside_critical_share}%",
            "message": f"{outside_critical} de {metrics['total']} riscos estão abaixo do nível crítico.",
        }
    )

    if not area_summary.empty:
        top_share = round(
            (int(area_summary["total_riscos"].max()) / int(metrics["total"])) * 100,
            1,
        )
        if top_share <= 35:
            highlights.append(
                {
                    "label": "Distribuição entre áreas",
                    "title": "Boa distribuição",
                    "message": f"Nenhuma área concentra mais de {top_share}% da matriz.",
                }
            )

    if float(metrics["exposicao_media"]) <= 9:
        highlights.append(
            {
                "label": "Exposição média",
                "title": f"{metrics['exposicao_media']} pontos",
                "message": "A exposição média permanece dentro da faixa baixa ou média.",
            }
        )
    return highlights[:4]


apply_theme()
render_sidebar("Riscos")
require_permission("Riscos")
render_hero(
    "Registro de riscos",
    "Matriz de riscos",
    (
        "Classifique riscos por probabilidade e impacto para priorizar "
        "controles internos, evidências e planos de resposta."
    ),
)

supabase = get_supabase()
areas = load_areas()
area_options = {area["nome"]: area["id"] for area in areas}

if supabase is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env ou em st.secrets.")

st.markdown("### Novo risco")
st.markdown(
    '<p class="orion-section">Registre eventos que podem afetar continuidade, conformidade ou eficiência.</p>',
    unsafe_allow_html=True,
)
with st.form("form_risco", clear_on_submit=True):
    area_nome = st.selectbox(
        "Área",
        list(area_options.keys()) or ["Cadastre uma área primeiro"],
        format_func=display_label,
    )
    descricao = st.text_area("Descrição")
    col1, col2, col3 = st.columns(3)
    probabilidade = col1.slider("Probabilidade", min_value=1, max_value=5, value=3)
    impacto = col2.slider("Impacto", min_value=1, max_value=5, value=3)
    risco = probabilidade * impacto
    classificacao = classify_risk(risco)
    with col3:
        st.metric("Score de risco", risco, display_label(classificacao), delta_color="off")
        st.markdown(badge_html(classificacao), unsafe_allow_html=True)

    submitted = st.form_submit_button("Cadastrar risco")
    if submitted:
        if supabase is None:
            st.error("Supabase não configurado.")
        elif not area_options:
            st.error("Cadastre uma área antes de registrar riscos.")
        elif not descricao.strip():
            st.error("Informe a descrição do risco.")
        else:
            try:
                supabase.table("riscos").insert(
                    {
                        "area_id": area_options[area_nome],
                        "descricao": descricao.strip(),
                        "probabilidade": probabilidade,
                        "impacto": impacto,
                        "risco": risco,
                        "classificacao": classificacao,
                    }
                ).execute()
                st.success("Risco cadastrado com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível cadastrar o risco: {exc}")

with st.spinner("Carregando inteligência de riscos..."):
    riscos_df = load_riscos()
risk_metrics = calculate_risk_metrics(riscos_df)
risk_insights = generate_risk_insights(risk_metrics)
risk_priorities = generate_risk_priorities(risk_metrics)
risk_highlights = generate_risk_positive_highlights(risk_metrics)

st.markdown('<div class="orion-section-break"></div>', unsafe_allow_html=True)
st.markdown("## Visão executiva de riscos")
st.markdown(
    '<p class="orion-section">Indicadores consolidados para acompanhar criticidade, distribuição e exposição da matriz corporativa.</p>',
    unsafe_allow_html=True,
)
metric_cards = [
    ("Total de riscos", str(risk_metrics["total"]), "Eventos monitorados na matriz."),
    ("Riscos críticos", str(risk_metrics["criticos"]), "Eventos de criticidade máxima."),
    ("Riscos altos", str(risk_metrics["altos"]), "Eventos com exposição elevada."),
    ("Riscos médios", str(risk_metrics["medios"]), "Eventos que exigem acompanhamento."),
    ("Riscos baixos", str(risk_metrics["baixos"]), "Eventos em faixa controlada."),
    ("Exposição média", str(risk_metrics["exposicao_media"]), "Média dos scores de risco."),
]
for offset in range(0, len(metric_cards), 3):
    metric_cols = st.columns(3)
    for column, card in zip(metric_cols, metric_cards[offset : offset + 3]):
        with column:
            render_kpi_card(*card)

st.markdown("### Risk Intelligence")
st.markdown(
    '<p class="orion-section">Leituras automáticas sobre concentração, criticidade, exposição e distribuição operacional.</p>',
    unsafe_allow_html=True,
)
if risk_insights:
    for offset in range(0, len(risk_insights), 3):
        insight_cols = st.columns(3)
        for column, insight in zip(insight_cols, risk_insights[offset : offset + 3]):
            with column:
                render_insight_card(
                    insight["label"],
                    insight["title"],
                    insight["message"],
                )
else:
    render_empty_state(
        "Inteligência de riscos ainda indisponível",
        "Cadastre riscos para habilitar análises por área, criticidade e exposição.",
        "O primeiro risco cadastrado já será incluído na leitura corporativa.",
    )

st.markdown("### Risk Priorities")
st.markdown(
    '<p class="orion-section">Ordem sugerida de atuação conforme criticidade, concentração e distribuição da matriz.</p>',
    unsafe_allow_html=True,
)
if risk_priorities:
    priority_cols = st.columns(len(risk_priorities))
    for column, priority in zip(priority_cols, risk_priorities):
        with column:
            render_priority_card(
                priority["priority"],
                priority["title"],
                priority["message"],
            )
else:
    render_empty_state(
        "Prioridades de risco ainda indisponíveis",
        "A matriz está vazia e ainda não permite classificar prioridades.",
        "Cadastre riscos com probabilidade e impacto para ativar esta seção.",
    )

st.markdown("### Positive Highlights")
st.markdown(
    '<p class="orion-section">Sinais favoráveis de controle, distribuição e exposição da matriz atual.</p>',
    unsafe_allow_html=True,
)
if risk_highlights:
    highlight_cols = st.columns(len(risk_highlights))
    for column, highlight in zip(highlight_cols, risk_highlights):
        with column:
            render_insight_card(
                highlight["label"],
                highlight["title"],
                highlight["message"],
            )
else:
    render_empty_state(
        "Destaques positivos ainda indisponíveis",
        "A base atual ainda não possui dados suficientes para destacar controles de risco.",
        "Registre e trate riscos para liberar esta leitura.",
    )

st.markdown("### Risk Distribution")
st.markdown(
    '<p class="orion-section">Distribuição visual da matriz por nível de criticidade.</p>',
    unsafe_allow_html=True,
)
if int(risk_metrics["total"]):
    distribution_cols = st.columns(4)
    distribution = [
        ("Baixo", int(risk_metrics["baixos"])),
        ("Médio", int(risk_metrics["medios"])),
        ("Alto", int(risk_metrics["altos"])),
        ("Crítico", int(risk_metrics["criticos"])),
    ]
    for column, (level, count) in zip(distribution_cols, distribution):
        share = round((count / int(risk_metrics["total"])) * 100, 1)
        with column:
            render_kpi_card(level, str(count), f"{share}% da matriz de riscos.")
            st.markdown(badge_html(level), unsafe_allow_html=True)
else:
    render_empty_state(
        "Distribuição de riscos ainda indisponível",
        "A matriz não possui eventos para distribuir por criticidade.",
        "Cadastre riscos para visualizar a composição da matriz.",
    )

st.markdown('<div class="orion-section-break"></div>', unsafe_allow_html=True)
st.markdown("### Riscos cadastrados")
st.markdown(
    '<p class="orion-table-note">Visão operacional por área, probabilidade, impacto, score e classificação.</p>',
    unsafe_allow_html=True,
)
if riscos_df.empty:
    render_empty_state(
        "Nenhum risco cadastrado",
        "A matriz ainda não possui eventos registrados. Cadastre riscos por área para criar uma visão executiva de exposição e priorização.",
        "Comece pelos eventos com maior impacto operacional, contratual ou regulatório.",
    )
else:
    columns = ["area", "descricao", "probabilidade", "impacto", "risco", "classificacao"]
    render_data_table(riscos_df, columns)
