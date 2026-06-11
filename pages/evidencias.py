import json
import mimetypes
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

from services.access_control import require_permission
from services.supabase_client import get_supabase
from services.ui import (
    apply_theme,
    display_label,
    is_non_corporate_area_name,
    render_data_table,
    render_empty_state,
    render_hero,
    render_insight_card,
    render_kpi_card,
    render_sidebar,
    render_status_message,
)


st.set_page_config(page_title="ORION GRC | Evidências", layout="wide")

EVIDENCE_BUCKET = "evidencias"
SESSION_EVIDENCES_KEY = "orion_session_evidences"
SUPPORTED_UPLOAD_TYPES = ["pdf", "docx", "xlsx", "png", "jpg", "jpeg"]
EVIDENCE_TYPES = ["PDF", "DOCX", "XLSX", "PNG", "JPG", "Registro"]
METADATA_VERSION = 1


def load_reference_data() -> tuple[list[dict], list[dict]]:
    supabase = get_supabase()
    if supabase is None:
        return [], []
    try:
        documentos = (
            supabase.table("documentos")
            .select("id, nome, areas(nome)")
            .order("nome")
            .execute()
            .data
        )
        riscos = (
            supabase.table("riscos")
            .select("id, descricao, risco, areas(nome)")
            .order("risco", desc=True)
            .execute()
            .data
        )
    except Exception as exc:
        st.error(f"Não foi possível carregar documentos e riscos relacionados: {exc}")
        return [], []
    documentos = [
        item
        for item in documentos
        if not is_non_corporate_area_name((item.get("areas") or {}).get("nome"))
    ]
    riscos = [
        item
        for item in riscos
        if not is_non_corporate_area_name((item.get("areas") or {}).get("nome"))
    ]
    return documentos, riscos


def serialize_evidence_metadata(
    tipo: str,
    responsavel: str,
    data: str,
    observacoes: str,
) -> str:
    return json.dumps(
        {
            "orion_evidence_metadata": METADATA_VERSION,
            "tipo": tipo,
            "responsavel": responsavel,
            "data": data,
            "observacoes": observacoes,
        },
        ensure_ascii=False,
    )


def parse_evidence_metadata(description: object) -> dict[str, str]:
    fallback = {
        "tipo": "Registro",
        "responsavel": "Não informado",
        "data": "",
        "observacoes": str(description or ""),
    }
    if not isinstance(description, str):
        return fallback
    try:
        metadata = json.loads(description)
    except json.JSONDecodeError:
        return fallback
    if not isinstance(metadata, dict) or not metadata.get("orion_evidence_metadata"):
        return fallback
    return {
        "tipo": str(metadata.get("tipo") or "Registro"),
        "responsavel": str(metadata.get("responsavel") or "Não informado"),
        "data": str(metadata.get("data") or ""),
        "observacoes": str(metadata.get("observacoes") or ""),
    }


def _session_evidences() -> list[dict]:
    if SESSION_EVIDENCES_KEY not in st.session_state:
        st.session_state[SESSION_EVIDENCES_KEY] = []
    return st.session_state[SESSION_EVIDENCES_KEY]


def storage_bucket_available(supabase) -> bool:
    if supabase is None:
        return False
    try:
        return any(
            getattr(bucket, "name", None) == EVIDENCE_BUCKET
            or (isinstance(bucket, dict) and bucket.get("name") == EVIDENCE_BUCKET)
            for bucket in supabase.storage.list_buckets()
        )
    except Exception:
        return False


def upload_evidence_file(supabase, uploaded_file) -> tuple[str | None, bytes | None]:
    if uploaded_file is None:
        return None, None

    file_bytes = uploaded_file.getvalue()
    if not storage_bucket_available(supabase):
        return f"session://{uploaded_file.name}", file_bytes

    safe_name = Path(uploaded_file.name).name.replace(" ", "_")
    storage_path = f"{uuid.uuid4()}/{safe_name}"
    content_type = uploaded_file.type or mimetypes.guess_type(safe_name)[0]
    options = {"content-type": content_type} if content_type else {}
    try:
        supabase.storage.from_(EVIDENCE_BUCKET).upload(storage_path, file_bytes, options)
        return storage_path, file_bytes
    except Exception:
        return f"session://{uploaded_file.name}", file_bytes


def stage_evidence(payload: dict, file_bytes: bytes | None) -> None:
    metadata = parse_evidence_metadata(payload.get("descricao"))
    _session_evidences().append(
        {
            "id": f"session-{uuid.uuid4()}",
            **payload,
            "created_at": pd.Timestamp.now().isoformat(),
            "arquivo_bytes": file_bytes,
            "arquivo_nome": (
                str(payload.get("url_arquivo", "")).removeprefix("session://")
                if payload.get("url_arquivo")
                else ""
            ),
            **metadata,
            "origem": "Sessão atual",
        }
    )


def register_evidence(payload: dict, file_bytes: bytes | None) -> bool:
    supabase = get_supabase()
    if supabase is not None and not str(payload.get("url_arquivo", "")).startswith(
        "session://"
    ):
        try:
            supabase.table("evidencias").insert(payload).execute()
            st.success("Evidência cadastrada com sucesso.")
            return True
        except Exception:
            pass

    stage_evidence(payload, file_bytes)
    st.warning(
        "Evidência adicionada à sessão atual. A persistência permanente depende "
        "de permissão de inserção e do bucket de evidências no Supabase."
    )
    return True


def load_evidences(
    documentos: list[dict],
    riscos: list[dict],
) -> pd.DataFrame:
    document_names = {item["id"]: item["nome"] for item in documentos}
    risk_names = {item["id"]: item["descricao"] for item in riscos}
    records = []
    supabase = get_supabase()
    if supabase is not None:
        try:
            records = (
                supabase.table("evidencias")
                .select(
                    "id, documento_id, risco_id, nome, descricao, url_arquivo, created_at"
                )
                .order("created_at", desc=True)
                .execute()
                .data
            )
        except Exception as exc:
            st.error(f"Não foi possível carregar as evidências: {exc}")

    normalized = []
    for record in [*records, *_session_evidences()]:
        metadata = parse_evidence_metadata(record.get("descricao"))
        created_date = pd.to_datetime(record.get("created_at"), errors="coerce")
        normalized.append(
            {
                **record,
                "tipo": record.get("tipo") or metadata["tipo"],
                "responsavel": record.get("responsavel") or metadata["responsavel"],
                "data": (
                    record.get("data")
                    or metadata["data"]
                    or (
                        created_date.strftime("%Y-%m-%d")
                        if not pd.isna(created_date)
                        else ""
                    )
                ),
                "observacoes": record.get("observacoes") or metadata["observacoes"],
                "documento": document_names.get(record.get("documento_id"), "Não vinculado"),
                "risco_associado": risk_names.get(record.get("risco_id"), "Não vinculado"),
                "origem": record.get("origem", "Supabase"),
            }
        )
    return pd.DataFrame(normalized)


def calculate_evidence_metrics(evidencias_df: pd.DataFrame) -> dict[str, object]:
    if evidencias_df.empty:
        return {
            "total": 0,
            "por_tipo": {},
            "vinculadas_documentos": 0,
            "vinculadas_riscos": 0,
        }
    return {
        "total": len(evidencias_df),
        "por_tipo": evidencias_df["tipo"].value_counts().to_dict(),
        "vinculadas_documentos": int(evidencias_df["documento_id"].notna().sum()),
        "vinculadas_riscos": int(evidencias_df["risco_id"].notna().sum()),
    }


apply_theme()
render_sidebar("Evidências")
require_permission("Evidências")
render_hero(
    "Rastreabilidade e auditoria",
    "Gestão de evidências",
    (
        "Centralize registros comprobatórios vinculados a documentos e riscos "
        "para fortalecer auditorias, controles e prestação de contas."
    ),
)

supabase = get_supabase()
documentos, riscos = load_reference_data()
document_options = {"Não vincular": None, **{item["nome"]: item["id"] for item in documentos}}
risk_options = {
    "Não vincular": None,
    **{
        f"{item['descricao'][:90]}{'...' if len(item['descricao']) > 90 else ''}": item["id"]
        for item in riscos
    },
}
permanent_upload_available = storage_bucket_available(supabase)

if supabase is None:
    st.warning("Configure SUPABASE_URL e SUPABASE_KEY para ler evidências persistidas.")
elif not permanent_upload_available:
    render_status_message(
        "O bucket 'evidencias' não existe no ambiente atual. Cadastros e uploads novos "
        "ficarão disponíveis durante a sessão, sem alterar Supabase ou RLS.",
        title="Fundação em modo de sessão",
        kind="warning",
    )

st.markdown("### Nova evidência")
st.markdown(
    '<p class="orion-section">Registre a evidência e vincule pelo menos um documento ou risco, conforme a regra atual do banco.</p>',
    unsafe_allow_html=True,
)
with st.form("form_evidencia", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    nome = col1.text_input("Nome")
    tipo = col2.selectbox("Tipo", EVIDENCE_TYPES, format_func=display_label)
    responsavel = col3.text_input("Responsável")
    documento_nome = col1.selectbox("Documento relacionado (opcional)", document_options)
    risco_nome = col2.selectbox("Risco relacionado (opcional)", risk_options)
    data_evidencia = col3.date_input("Data")
    observacoes = st.text_area("Observações")
    uploaded_file = st.file_uploader(
        "Arquivo de evidência",
        type=SUPPORTED_UPLOAD_TYPES,
        help="Formatos suportados: PDF, DOCX, XLSX, PNG e JPG.",
    )

    submitted = st.form_submit_button("Cadastrar evidência")
    if submitted:
        documento_id = document_options[documento_nome]
        risco_id = risk_options[risco_nome]
        if not nome.strip() or not responsavel.strip():
            st.error("Preencha nome e responsável.")
        elif not documento_id and not risco_id:
            st.error("Vincule pelo menos um documento ou risco.")
        else:
            try:
                url_arquivo, file_bytes = upload_evidence_file(supabase, uploaded_file)
                payload = {
                    "nome": nome.strip(),
                    "documento_id": documento_id,
                    "risco_id": risco_id,
                    "descricao": serialize_evidence_metadata(
                        tipo,
                        responsavel.strip(),
                        data_evidencia.isoformat(),
                        observacoes.strip(),
                    ),
                    "url_arquivo": url_arquivo,
                }
                if register_evidence(payload, file_bytes):
                    st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível processar a evidência: {exc}")

evidencias_df = load_evidences(documentos, riscos)
evidence_metrics = calculate_evidence_metrics(evidencias_df)

st.markdown('<div class="orion-section-break"></div>', unsafe_allow_html=True)
st.markdown("## Visão executiva de evidências")
st.markdown(
    '<p class="orion-section">Indicadores de cobertura e vinculação da base comprobatória atual.</p>',
    unsafe_allow_html=True,
)
metric_cols = st.columns(3)
metric_cards = [
    ("Total de evidências", str(evidence_metrics["total"]), "Registros comprobatórios monitorados."),
    (
        "Vinculadas a documentos",
        str(evidence_metrics["vinculadas_documentos"]),
        "Evidências associadas ao ciclo documental.",
    ),
    (
        "Vinculadas a riscos",
        str(evidence_metrics["vinculadas_riscos"]),
        "Evidências associadas à matriz de riscos.",
    ),
]
for column, card in zip(metric_cols, metric_cards):
    with column:
        render_kpi_card(*card)

st.markdown("### Evidências por tipo")
st.markdown(
    '<p class="orion-section">Distribuição dos registros conforme o tipo de evidência informado.</p>',
    unsafe_allow_html=True,
)
if evidence_metrics["por_tipo"]:
    type_items = list(evidence_metrics["por_tipo"].items())
    for offset in range(0, len(type_items), 4):
        type_cols = st.columns(4)
        for column, (evidence_type, count) in zip(type_cols, type_items[offset : offset + 4]):
            with column:
                render_insight_card(
                    display_label(str(evidence_type)),
                    str(count),
                    "Evidência(s) deste tipo na base atual.",
                )
else:
    render_empty_state(
        "Distribuição ainda indisponível",
        "Cadastre evidências para visualizar a composição por tipo.",
        "Os formatos de arquivo enviados também apoiam esta classificação.",
    )

st.markdown('<div class="orion-section-break"></div>', unsafe_allow_html=True)
st.markdown("### Evidências cadastradas")
st.markdown(
    '<p class="orion-table-note">Visão operacional por vínculo, responsável, data e origem do registro.</p>',
    unsafe_allow_html=True,
)
if evidencias_df.empty:
    render_empty_state(
        "Nenhuma evidência cadastrada",
        "A base ainda não possui evidências vinculadas a documentos ou riscos.",
        "Comece pelos controles e eventos com maior relevância para auditoria.",
    )
else:
    render_data_table(
        evidencias_df,
        ["nome", "tipo", "documento", "risco_associado", "responsavel", "data", "origem"],
    )

session_files = [
    item
    for item in _session_evidences()
    if item.get("arquivo_bytes") and item.get("arquivo_nome")
]
if session_files:
    st.markdown("### Arquivos enviados nesta sessão")
    st.markdown(
        '<p class="orion-section">Downloads temporários disponíveis enquanto esta sessão permanecer ativa.</p>',
        unsafe_allow_html=True,
    )
    for item in session_files:
        st.download_button(
            f"Baixar {item['arquivo_nome']}",
            item["arquivo_bytes"],
            file_name=item["arquivo_nome"],
            key=f"download-{item['id']}",
        )
