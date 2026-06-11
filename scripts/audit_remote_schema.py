from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from supabase import create_client


ROOT_DIR = Path(__file__).resolve().parents[1]

EXPECTED_COLUMNS = {
    "areas": ["id", "nome", "created_at"],
    "perfis": ["codigo", "nome", "descricao", "created_at"],
    "usuarios": [
        "id",
        "auth_user_id",
        "nome",
        "email",
        "perfil_codigo",
        "area_id",
        "ativo",
        "created_at",
    ],
    "documentos": [
        "id",
        "nome",
        "categoria",
        "area_id",
        "responsavel",
        "vencimento",
        "status",
        "escopo_acesso",
        "created_by",
        "created_at",
    ],
    "riscos": [
        "id",
        "area_id",
        "descricao",
        "probabilidade",
        "impacto",
        "risco",
        "classificacao",
        "plano_acao",
        "responsavel_plano",
        "prazo_plano",
        "status_plano",
        "escopo_acesso",
        "created_by",
        "created_at",
    ],
    "evidencias": [
        "id",
        "documento_id",
        "risco_id",
        "nome",
        "descricao",
        "url_arquivo",
        "created_by",
        "created_at",
    ],
    "historico_eventos": [
        "id",
        "entidade",
        "entidade_id",
        "acao",
        "detalhes",
        "usuario_id",
        "created_at",
    ],
}


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")
    return value


def audit_remote_schema() -> dict[str, Any]:
    load_dotenv(ROOT_DIR / ".env")
    supabase = create_client(require_env("SUPABASE_URL"), require_env("SUPABASE_KEY"))
    tables: dict[str, Any] = {}

    for table_name, columns in EXPECTED_COLUMNS.items():
        try:
            supabase.table(table_name).select("*").limit(0).execute()
            table_present = True
        except Exception as exc:
            tables[table_name] = {
                "present": False,
                "missing_columns": columns,
                "error": str(exc),
            }
            continue

        missing_columns = []
        for column in columns:
            try:
                supabase.table(table_name).select(column).limit(0).execute()
            except Exception:
                missing_columns.append(column)

        tables[table_name] = {
            "present": table_present,
            "missing_columns": missing_columns,
        }

    try:
        buckets = [
            getattr(bucket, "name", None)
            or (bucket.get("name") if isinstance(bucket, dict) else None)
            for bucket in supabase.storage.list_buckets()
        ]
    except Exception as exc:
        buckets = []
        storage_error = str(exc)
    else:
        storage_error = None

    missing_risk_columns = tables.get("riscos", {}).get("missing_columns", [])
    treatment_status_missing = "status_plano" in missing_risk_columns
    return {
        "tables": tables,
        "confirmed_missing_database_objects": {
            "constraints": (
                ["riscos_status_plano_check"] if treatment_status_missing else []
            ),
            "indexes": (
                ["idx_riscos_status_plano"] if treatment_status_missing else []
            ),
        },
        "storage": {
            "evidencias_bucket_present": "evidencias" in buckets,
            "visible_buckets": [bucket for bucket in buckets if bucket],
            "error": storage_error,
        },
        "catalog_limitations": (
            "Constraints and indexes are not exposed by the public PostgREST API. "
            "Objects unrelated to confirmed missing columns remain unverified. "
            "Run the idempotent production migration in Supabase SQL Editor to "
            "verify and add them safely."
        ),
    }


def main() -> int:
    try:
        print(json.dumps(audit_remote_schema(), indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"Erro ao auditar schema remoto: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
