import pandas as pd
import streamlit as st

from services.access_control import require_permission
from services.supabase_client import get_supabase
from services.ui import (
    apply_theme,
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


st.set_page_config(page_title="ORION GRC | Documentos", layout="wide")

STATUS_OPTIONS = ["Vigente", "Pendente", "Vencido", "Em revisao"]
CATEGORY_OPTIONS = [
    "Contrato",
    "Politica",
    "Procedimento",
    "Controle",
    "Relatorio",
    "Fluxograma",
    "KPI",
    "Auditoria",
    "Juridico",
]


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


def load_documentos() -> pd.DataFrame:
    supabase = get_supabase()
    if supabase is None:
        return pd.DataFrame()
    try:
        data = (
            supabase.table("documentos")
            .select("id, nome, categoria, responsavel, vencimento, status, areas(nome)")
            .order("vencimento")
            .execute()
            .data
        )
    except Exception:
        st.error("Não foi possível carregar os documentos no momento.")
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if not df.empty and "areas" in df:
        df["area"] = df["areas"].apply(
            lambda item: item.get("nome") if isinstance(item, dict) else "Sem área"
        )
    return filter_non_corporate_area_rows(df, "area")


def enrich_documentos(documentos_df: pd.DataFrame) -> pd.DataFrame:
    if documentos_df.empty:
        return documentos_df.copy()

    enriched = documentos_df.copy()
    status = enriched.get("status", pd.Series(index=enriched.index, dtype=str))
    vencimento = pd.to_datetime(
        enriched.get("vencimento", pd.Series(index=enriched.index, dtype=str)),
        errors="coerce",
    )
    today = pd.Timestamp.today().normalize()
    enriched["pendente"] = status.fillna("").astype(str).str.lower().eq("pendente")
    enriched["vencido"] = vencimento < today
    enriched["vigente"] = (
        status.fillna("").astype(str).str.lower().eq("vigente")
        & ~enriched["vencido"]
    )
    enriched["proximo_vencimento"] = (
        vencimento.ge(today)
        & vencimento.le(today + pd.Timedelta(days=30))
        & ~enriched["pendente"]
    )
    enriched["conforme"] = ~enriched["pendente"] & ~enriched["vencido"]
    return enriched


def calculate_document_metrics(documentos_df: pd.DataFrame) -> dict[str, object]:
    enriched = enrich_documentos(documentos_df)
    total = len(enriched)
    if not total:
        return {
            "total": 0,
            "vigentes": 0,
            "pendentes": 0,
            "vencidos": 0,
            "proximos_vencimento": 0,
            "taxa_conformidade": 0,
            "percentual_vigentes": 0,
            "data": enriched,
        }

    vigentes = int(enriched["vigente"].sum())
    conformes = int(enriched["conforme"].sum())
    return {
        "total": total,
        "vigentes": vigentes,
        "pendentes": int(enriched["pendente"].sum()),
        "vencidos": int(enriched["vencido"].sum()),
        "proximos_vencimento": int(enriched["proximo_vencimento"].sum()),
        "taxa_conformidade": round((conformes / total) * 100, 1),
        "percentual_vigentes": round((vigentes / total) * 100, 1),
        "data": enriched,
    }


def _document_area_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    if enriched.empty or "area" not in enriched:
        return pd.DataFrame()
    return (
        enriched.groupby("area", as_index=False)
        .agg(
            total_documentos=("id", "count"),
            documentos_pendentes=("pendente", "sum"),
            documentos_vencidos=("vencido", "sum"),
            documentos_conformes=("conforme", "sum"),
        )
        .assign(
            conformidade=lambda df: (
                (df["documentos_conformes"] / df["total_documentos"]) * 100
            ).round(1)
        )
    )


def generate_document_insights(metrics: dict[str, object]) -> list[dict[str, str]]:
    enriched = metrics["data"]
    if enriched.empty:
        return []

    insights = []
    area_summary = _document_area_summary(enriched)
    if not area_summary.empty:
        if int(metrics["vencidos"]):
            expired_leader = area_summary.sort_values(
                ["documentos_vencidos", "total_documentos", "area"],
                ascending=[False, False, True],
            ).iloc[0]
            insights.append(
                {
                    "label": "Documentos vencidos",
                    "title": display_label(str(expired_leader["area"])),
                    "message": f"Concentra {expired_leader['documentos_vencidos']} documento(s) vencido(s).",
                }
            )

        volume_leader = area_summary.sort_values(
            ["total_documentos", "documentos_pendentes", "area"],
            ascending=[False, False, True],
        ).iloc[0]
        insights.append(
            {
                "label": "Volume documental",
                "title": display_label(str(volume_leader["area"])),
                "message": f"Possui o maior volume, com {volume_leader['total_documentos']} documento(s).",
            }
        )

        if int(metrics["pendentes"]):
            pending_leader = area_summary.sort_values(
                ["documentos_pendentes", "total_documentos", "area"],
                ascending=[False, False, True],
            ).iloc[0]
            insights.append(
                {
                    "label": "Concentração de pendências",
                    "title": display_label(str(pending_leader["area"])),
                    "message": f"Concentra {pending_leader['documentos_pendentes']} pendência(s) documental(is).",
                }
            )

    if "responsavel" in enriched:
        owner_summary = (
            enriched.groupby("responsavel", as_index=False)
            .size()
            .sort_values(["size", "responsavel"], ascending=[False, True])
        )
        if not owner_summary.empty:
            owner = owner_summary.iloc[0]
            insights.append(
                {
                    "label": "Responsabilidade documental",
                    "title": str(owner["responsavel"]),
                    "message": f"É responsável por {owner['size']} documento(s), o maior volume atribuído.",
                }
            )
    return insights[:6]


def generate_document_priorities(metrics: dict[str, object]) -> list[dict[str, str]]:
    if not int(metrics["total"]):
        return []

    priorities = []
    if int(metrics["vencidos"]):
        priorities.append(
            {
                "priority": "Alta Prioridade",
                "title": "Regularizar documentos vencidos",
                "message": f"{metrics['vencidos']} documento(s) ultrapassaram o vencimento.",
            }
        )
    if int(metrics["pendentes"]):
        priorities.append(
            {
                "priority": "Média Prioridade",
                "title": "Resolver pendências documentais",
                "message": f"{metrics['pendentes']} documento(s) aguardam conclusão do fluxo.",
            }
        )
    if int(metrics["proximos_vencimento"]):
        priorities.append(
            {
                "priority": "Baixa Prioridade",
                "title": "Antecipar próximos vencimentos",
                "message": f"{metrics['proximos_vencimento']} documento(s) vencem nos próximos 30 dias.",
            }
        )
    if not priorities:
        priorities.append(
            {
                "priority": "Baixa Prioridade",
                "title": "Manter ciclo documental controlado",
                "message": "A base atual não possui vencimentos, pendências ou alertas próximos.",
            }
        )
    return priorities


def generate_document_positive_highlights(
    metrics: dict[str, object],
) -> list[dict[str, str]]:
    enriched = metrics["data"]
    if enriched.empty:
        return []

    highlights = [
        {
            "label": "Documentos vigentes",
            "title": f"{metrics['percentual_vigentes']}%",
            "message": f"{metrics['vigentes']} de {metrics['total']} documentos estão vigentes.",
        }
    ]
    area_summary = _document_area_summary(enriched)
    if not area_summary.empty:
        best = area_summary.sort_values(
            ["conformidade", "documentos_pendentes", "total_documentos", "area"],
            ascending=[False, True, False, True],
        ).iloc[0]
        highlights.append(
            {
                "label": "Melhor conformidade",
                "title": display_label(str(best["area"])),
                "message": f"Mantém {best['conformidade']}% de conformidade documental.",
            }
        )

        areas_without_pending = area_summary[
            area_summary["documentos_pendentes"].eq(0)
        ]
        if not areas_without_pending.empty:
            names = ", ".join(
                display_label(str(name))
                for name in areas_without_pending["area"].head(3)
            )
            highlights.append(
                {
                    "label": "Áreas sem pendências",
                    "title": str(len(areas_without_pending)),
                    "message": f"{names} não possuem documentos pendentes.",
                }
            )
    return highlights[:4]


apply_theme()
render_sidebar("Documentos")
require_permission("Documentos")
render_hero(
    "Ciclo documental",
    "Gestão documental",
    (
        "Controle contratos, políticas, relatórios, evidências e documentos "
        "de auditoria com dono, vencimento e status operacional."
    ),
)

supabase = get_supabase()
areas = load_areas()
area_options = {area["nome"]: area["id"] for area in areas}

if supabase is None:
    st.warning("Recurso em configuração administrativa.")

st.markdown("### Novo documento")
st.markdown(
    '<p class="orion-section">Registre itens que precisam de monitoramento, revisão ou evidência.</p>',
    unsafe_allow_html=True,
)
with st.form("form_documento", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    nome = col1.text_input("Nome")
    categoria = col2.selectbox("Categoria", CATEGORY_OPTIONS, format_func=display_label)
    area_nome = col3.selectbox(
        "Área",
        list(area_options.keys()) or ["Cadastre uma área primeiro"],
        format_func=display_label,
    )
    responsavel = col1.text_input("Responsável")
    vencimento = col2.date_input("Vencimento")
    status = col3.selectbox("Status", STATUS_OPTIONS, format_func=display_label)

    submitted = st.form_submit_button("Cadastrar documento")
    if submitted:
        if supabase is None:
            st.error("Recurso em configuração administrativa.")
        elif not area_options:
            st.error("Cadastre uma área antes de registrar documentos.")
        elif not nome.strip() or not responsavel.strip():
            st.error("Preencha nome e responsável.")
        else:
            try:
                supabase.table("documentos").insert(
                    {
                        "nome": nome.strip(),
                        "categoria": categoria,
                        "area_id": area_options[area_nome],
                        "responsavel": responsavel.strip(),
                        "vencimento": vencimento.isoformat(),
                        "status": status,
                    }
                ).execute()
                st.success("Documento cadastrado com sucesso.")
                st.rerun()
            except Exception:
                st.error("Não foi possível cadastrar o documento no momento.")

with st.spinner("Carregando inteligência documental..."):
    documentos_df = load_documentos()
document_metrics = calculate_document_metrics(documentos_df)
document_insights = generate_document_insights(document_metrics)
document_priorities = generate_document_priorities(document_metrics)
document_highlights = generate_document_positive_highlights(document_metrics)

st.markdown('<div class="orion-section-break"></div>', unsafe_allow_html=True)
st.markdown("## Visão executiva documental")
st.markdown(
    '<p class="orion-section">Indicadores consolidados para acompanhar saúde, conformidade e urgências do ciclo documental.</p>',
    unsafe_allow_html=True,
)
metric_cols = st.columns(5)
metric_cards = [
    ("Total de documentos", str(document_metrics["total"]), "Base documental monitorada."),
    ("Documentos vigentes", str(document_metrics["vigentes"]), "Itens vigentes e dentro da validade."),
    ("Documentos pendentes", str(document_metrics["pendentes"]), "Itens aguardando conclusão."),
    ("Documentos vencidos", str(document_metrics["vencidos"]), "Itens fora da validade."),
    ("Taxa de conformidade", f"{document_metrics['taxa_conformidade']}%", "Documentos sem pendência ou vencimento."),
]
for column, card in zip(metric_cols, metric_cards):
    with column:
        render_kpi_card(*card)

st.markdown("### Document Intelligence")
st.markdown(
    '<p class="orion-section">Leituras automáticas sobre concentração, responsabilidade e exposição documental.</p>',
    unsafe_allow_html=True,
)
if document_insights:
    insight_cols = st.columns(len(document_insights))
    for column, insight in zip(insight_cols, document_insights):
        with column:
            render_insight_card(
                insight["label"],
                insight["title"],
                insight["message"],
            )
else:
    render_empty_state(
        "Inteligência documental ainda indisponível",
        "Cadastre documentos para habilitar análises por área, responsável e status.",
        "O primeiro documento cadastrado já será incluído na leitura documental.",
    )

st.markdown("### Prioridades Documentais")
st.markdown(
    '<p class="orion-section">Ordem sugerida de atuação conforme vencimentos, pendências e proximidade do prazo.</p>',
    unsafe_allow_html=True,
)
if document_priorities:
    priority_cols = st.columns(len(document_priorities))
    for column, priority in zip(priority_cols, document_priorities):
        with column:
            render_priority_card(
                priority["priority"],
                priority["title"],
                priority["message"],
            )
else:
    render_empty_state(
        "Prioridades documentais ainda indisponíveis",
        "A base documental está vazia e ainda não permite classificar prioridades.",
        "Cadastre documentos com status e vencimento para ativar esta seção.",
    )

st.markdown("### Destaques Positivos")
st.markdown(
    '<p class="orion-section">Sinais favoráveis de conformidade e organização documental.</p>',
    unsafe_allow_html=True,
)
if document_highlights:
    highlight_cols = st.columns(len(document_highlights))
    for column, highlight in zip(highlight_cols, document_highlights):
        with column:
            render_insight_card(
                highlight["label"],
                highlight["title"],
                highlight["message"],
            )
else:
    render_empty_state(
        "Destaques positivos ainda indisponíveis",
        "A base atual ainda não possui dados suficientes para destacar desempenho documental.",
        "Cadastre documentos vigentes e conclua pendências para liberar esta leitura.",
    )

st.markdown('<div class="orion-section-break"></div>', unsafe_allow_html=True)
st.markdown("### Documentos cadastrados")
st.markdown(
    '<p class="orion-table-note">Visão operacional por área, responsável, vencimento e status.</p>',
    unsafe_allow_html=True,
)
if documentos_df.empty:
    render_empty_state(
        "Nenhum documento cadastrado",
        "O ciclo documental ainda não possui itens monitorados. Registre contratos, políticas, evidências ou relatórios para acompanhar vencimentos e responsabilidades.",
        "Priorize documentos com vencimento recorrente ou impacto direto em auditoria e conformidade.",
    )
else:
    columns = ["nome", "area", "responsavel", "vencimento", "status"]
    render_data_table(documentos_df, columns)
