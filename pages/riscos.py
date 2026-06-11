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
    render_status_message,
)


st.set_page_config(page_title="ORION GRC | Riscos", layout="wide")

ACTION_PLAN_STATUS_OPTIONS = ["Nao iniciado", "Em andamento", "Concluido", "Atrasado"]
ACTION_PLAN_COLUMNS = [
    "plano_acao",
    "responsavel_plano",
    "prazo_plano",
    "status_plano",
]


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
    except Exception:
        st.error("Não foi possível carregar as áreas no momento.")
        return []
    return [
        area
        for area in data
        if not is_non_corporate_area_name(area.get("nome"))
    ]


def load_riscos() -> tuple[pd.DataFrame, bool]:
    supabase = get_supabase()
    if supabase is None:
        return pd.DataFrame(), False
    try:
        data = (
            supabase.table("riscos")
            .select(
                "id, descricao, probabilidade, impacto, risco, classificacao, "
                "plano_acao, responsavel_plano, prazo_plano, status_plano, areas(nome)"
            )
            .order("risco", desc=True)
            .execute()
            .data
        )
        treatment_available = True
    except Exception:
        try:
            data = (
                supabase.table("riscos")
                .select("id, descricao, probabilidade, impacto, risco, classificacao, areas(nome)")
                .order("risco", desc=True)
                .execute()
                .data
            )
            treatment_available = False
        except Exception:
            st.error("Não foi possível carregar os riscos no momento.")
            return pd.DataFrame(), False
    df = pd.DataFrame(data)
    for column in ACTION_PLAN_COLUMNS:
        if column not in df:
            df[column] = None
    if not df.empty and "areas" in df:
        df["area"] = df["areas"].apply(
            lambda item: item.get("nome") if isinstance(item, dict) else "Sem área"
        )
    return filter_non_corporate_area_rows(df, "area"), treatment_available


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
    plan = enriched.get("plano_acao", pd.Series(index=enriched.index, dtype=str))
    owner = enriched.get(
        "responsavel_plano",
        pd.Series(index=enriched.index, dtype=str),
    )
    status_plan = enriched.get(
        "status_plano",
        pd.Series(index=enriched.index, dtype=str),
    )
    deadline = pd.to_datetime(
        enriched.get("prazo_plano", pd.Series(index=enriched.index, dtype=str)),
        errors="coerce",
    )
    today = pd.Timestamp.today().normalize()
    enriched["com_plano"] = plan.fillna("").astype(str).str.strip().ne("")
    enriched["sem_responsavel_plano"] = (
        enriched["com_plano"] & owner.fillna("").astype(str).str.strip().eq("")
    )
    enriched["status_plano_normalizado"] = (
        status_plan.fillna("").astype(str).str.strip().str.lower()
    )
    enriched["plano_em_andamento"] = enriched["status_plano_normalizado"].eq(
        "em andamento"
    )
    enriched["plano_concluido"] = enriched["status_plano_normalizado"].isin(
        ["concluido", "concluído"]
    )
    enriched["plano_atrasado"] = (
        enriched["status_plano_normalizado"].eq("atrasado")
        | (enriched["com_plano"] & deadline.lt(today) & ~enriched["plano_concluido"])
    )
    enriched["plano_em_andamento"] = (
        enriched["plano_em_andamento"] & ~enriched["plano_atrasado"]
    )
    enriched["plano_proximo_prazo"] = (
        enriched["plano_em_andamento"]
        & deadline.ge(today)
        & deadline.le(today + pd.Timedelta(days=30))
    )
    enriched["status_plano"] = status_plan.where(enriched["com_plano"], "Sem plano")
    enriched.loc[enriched["plano_atrasado"], "status_plano"] = "Atrasado"
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
            "com_plano": 0,
            "sem_plano": 0,
            "planos_em_andamento": 0,
            "planos_concluidos": 0,
            "planos_atrasados": 0,
            "planos_proximos_prazo": 0,
            "criticos_sem_plano": 0,
            "criticos_com_plano": 0,
            "sem_responsavel_plano": 0,
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
        "com_plano": int(enriched["com_plano"].sum()),
        "sem_plano": int((~enriched["com_plano"]).sum()),
        "planos_em_andamento": int(enriched["plano_em_andamento"].sum()),
        "planos_concluidos": int(enriched["plano_concluido"].sum()),
        "planos_atrasados": int(enriched["plano_atrasado"].sum()),
        "planos_proximos_prazo": int(enriched["plano_proximo_prazo"].sum()),
        "criticos_sem_plano": int(
            (enriched["nivel"].eq("critico") & ~enriched["com_plano"]).sum()
        ),
        "criticos_com_plano": int(
            (enriched["nivel"].eq("critico") & enriched["com_plano"]).sum()
        ),
        "sem_responsavel_plano": int(enriched["sem_responsavel_plano"].sum()),
        "data": enriched,
    }


def generate_treatment_insights(metrics: dict[str, object]) -> list[dict[str, str]]:
    if not int(metrics["total"]):
        return []

    insights = []
    if int(metrics["criticos_sem_plano"]):
        insights.append(
            {
                "label": "Criticidade sem tratamento",
                "title": f"{metrics['criticos_sem_plano']} risco(s) crítico(s)",
                "message": "Existem riscos críticos sem plano de ação definido.",
            }
        )
    if int(metrics["planos_atrasados"]):
        insights.append(
            {
                "label": "Planos atrasados",
                "title": str(metrics["planos_atrasados"]),
                "message": "Existem planos fora do prazo que exigem acompanhamento.",
            }
        )
    critical_total = int(metrics["criticos"])
    if critical_total:
        treated_share = round(
            (int(metrics["criticos_com_plano"]) / critical_total) * 100,
            1,
        )
        insights.append(
            {
                "label": "Tratamento de riscos críticos",
                "title": f"{treated_share}%",
                "message": (
                    "A maior parte dos riscos críticos possui tratamento definido."
                    if treated_share >= 50
                    else "Menos da metade dos riscos críticos possui tratamento definido."
                ),
            }
        )
    if int(metrics["sem_responsavel_plano"]):
        insights.append(
            {
                "label": "Responsabilidade",
                "title": f"{metrics['sem_responsavel_plano']} plano(s)",
                "message": "Existem planos de ação sem responsável definido.",
            }
        )
    if not insights and int(metrics["com_plano"]):
        insights.append(
            {
                "label": "Tratamento monitorado",
                "title": f"{metrics['com_plano']} plano(s)",
                "message": "Os planos atuais possuem responsáveis e não apresentam atrasos.",
            }
        )
    return insights[:4]


def generate_treatment_priorities(metrics: dict[str, object]) -> list[dict[str, str]]:
    if not int(metrics["total"]):
        return []

    priorities = []
    if int(metrics["criticos_sem_plano"]):
        priorities.append(
            {
                "priority": "Alta Prioridade",
                "title": "Definir planos para riscos críticos",
                "message": f"{metrics['criticos_sem_plano']} risco(s) crítico(s) ainda não possuem tratamento.",
            }
        )
    if int(metrics["planos_atrasados"]):
        priorities.append(
            {
                "priority": "Alta Prioridade",
                "title": "Regularizar planos atrasados",
                "message": f"{metrics['planos_atrasados']} plano(s) ultrapassaram o prazo.",
            }
        )
    if int(metrics["planos_proximos_prazo"]):
        priorities.append(
            {
                "priority": "Média Prioridade",
                "title": "Acompanhar próximos prazos",
                "message": f"{metrics['planos_proximos_prazo']} plano(s) em andamento vencem nos próximos 30 dias.",
            }
        )
    if int(metrics["planos_concluidos"]):
        priorities.append(
            {
                "priority": "Baixa Prioridade",
                "title": "Preservar tratamentos concluídos",
                "message": f"{metrics['planos_concluidos']} plano(s) foram concluídos.",
            }
        )
    if not priorities:
        priorities.append(
            {
                "priority": "Média Prioridade",
                "title": "Estruturar tratamento de riscos",
                "message": f"{metrics['sem_plano']} risco(s) ainda não possuem plano de ação.",
            }
        )
    return priorities[:4]


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
    st.warning("Recurso em configuração administrativa.")

with st.spinner("Carregando inteligência de riscos..."):
    riscos_df, treatment_available = load_riscos()
if supabase is not None and not treatment_available:
    render_status_message(
        "Planos de ação disponíveis para acompanhamento operacional. "
        "Novos registros de tratamento estão em configuração administrativa.",
        title="Acompanhamento de planos",
        kind="info",
    )

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

    adicionar_plano = st.checkbox(
        "Adicionar plano de ação",
        disabled=not treatment_available,
        help=(
            "Recurso em configuração administrativa."
            if not treatment_available
            else "Inclua o tratamento inicial junto ao cadastro do risco."
        ),
    )
    plano_acao = ""
    responsavel_plano = ""
    prazo_plano = None
    status_plano = None
    if adicionar_plano:
        st.markdown("#### Tratamento inicial")
        plano_acao = st.text_area("Plano de ação")
        plan_col1, plan_col2, plan_col3 = st.columns(3)
        responsavel_plano = plan_col1.text_input("Responsável pelo plano")
        prazo_plano = plan_col2.date_input("Prazo do plano")
        status_plano = plan_col3.selectbox(
            "Status do plano",
            ACTION_PLAN_STATUS_OPTIONS,
            format_func=display_label,
        )

    submitted = st.form_submit_button("Cadastrar risco")
    if submitted:
        if supabase is None:
            st.error("Recurso em configuração administrativa.")
        elif not area_options:
            st.error("Cadastre uma área antes de registrar riscos.")
        elif not descricao.strip():
            st.error("Informe a descrição do risco.")
        elif adicionar_plano and not plano_acao.strip():
            st.error("Informe o plano de ação.")
        else:
            try:
                payload = {
                    "area_id": area_options[area_nome],
                    "descricao": descricao.strip(),
                    "probabilidade": probabilidade,
                    "impacto": impacto,
                    "risco": risco,
                    "classificacao": classificacao,
                }
                if adicionar_plano:
                    payload.update(
                        {
                            "plano_acao": plano_acao.strip(),
                            "responsavel_plano": responsavel_plano.strip() or None,
                            "prazo_plano": prazo_plano.isoformat(),
                            "status_plano": status_plano,
                        }
                    )
                supabase.table("riscos").insert(payload).execute()
                st.success("Risco cadastrado com sucesso.")
                st.rerun()
            except Exception:
                st.error("Não foi possível cadastrar o risco no momento.")

risk_metrics = calculate_risk_metrics(riscos_df)
risk_insights = generate_risk_insights(risk_metrics)
risk_priorities = generate_risk_priorities(risk_metrics)
risk_highlights = generate_risk_positive_highlights(risk_metrics)
treatment_insights = generate_treatment_insights(risk_metrics)
treatment_priorities = generate_treatment_priorities(risk_metrics)

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

st.markdown("### Risk Treatment")
st.markdown(
    '<p class="orion-section">Indicadores executivos sobre cobertura, andamento e cumprimento dos planos de ação.</p>',
    unsafe_allow_html=True,
)
treatment_cards = [
    ("Riscos com plano", str(risk_metrics["com_plano"]), "Riscos com tratamento definido."),
    ("Riscos sem plano", str(risk_metrics["sem_plano"]), "Riscos ainda sem tratamento."),
    (
        "Planos em andamento",
        str(risk_metrics["planos_em_andamento"]),
        "Tratamentos em execução.",
    ),
    (
        "Planos concluídos",
        str(risk_metrics["planos_concluidos"]),
        "Tratamentos finalizados.",
    ),
    (
        "Planos atrasados",
        str(risk_metrics["planos_atrasados"]),
        "Tratamentos fora do prazo.",
    ),
]
for offset in range(0, len(treatment_cards), 3):
    treatment_cols = st.columns(3)
    for column, card in zip(treatment_cols, treatment_cards[offset : offset + 3]):
        with column:
            render_kpi_card(*card)

st.markdown("### Risk Treatment Intelligence")
st.markdown(
    '<p class="orion-section">Leituras automáticas sobre cobertura de tratamento, atrasos e responsabilidades.</p>',
    unsafe_allow_html=True,
)
if treatment_insights:
    treatment_insight_cols = st.columns(len(treatment_insights))
    for column, insight in zip(treatment_insight_cols, treatment_insights):
        with column:
            render_insight_card(
                insight["label"],
                insight["title"],
                insight["message"],
            )
else:
    render_empty_state(
        "Inteligência de tratamento ainda indisponível",
        "Cadastre riscos e planos de ação para habilitar análises de tratamento.",
        "Riscos críticos com tratamento definido melhoram a cobertura da matriz.",
    )

st.markdown("### Treatment Priorities")
st.markdown(
    '<p class="orion-section">Priorização automática conforme criticidade, atraso, prazo e conclusão dos planos.</p>',
    unsafe_allow_html=True,
)
if treatment_priorities:
    treatment_priority_cols = st.columns(len(treatment_priorities))
    for column, priority in zip(treatment_priority_cols, treatment_priorities):
        with column:
            render_priority_card(
                priority["priority"],
                priority["title"],
                priority["message"],
            )
else:
    render_empty_state(
        "Prioridades de tratamento ainda indisponíveis",
        "A matriz está vazia e ainda não permite priorizar planos de ação.",
        "Cadastre riscos para estruturar o tratamento.",
    )

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
    columns = [
        "area",
        "descricao",
        "probabilidade",
        "impacto",
        "risco",
        "classificacao",
        "responsavel_plano",
        "prazo_plano",
        "status_plano",
    ]
    render_data_table(risk_metrics["data"], columns)
