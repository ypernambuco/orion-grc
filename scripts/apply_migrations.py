from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import psycopg2
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
MIGRATION_PATHS = [
    ROOT_DIR / "database" / "migrations" / "2026_06_risk_treatment.sql",
    ROOT_DIR / "database" / "migrations" / "2026_06_evidence_storage.sql",
]
REQUIRED_RISK_COLUMNS = {
    "plano_acao",
    "responsavel_plano",
    "prazo_plano",
    "status_plano",
}
REQUIRED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/png",
    "image/jpeg",
}


def require_database_url() -> str:
    database_url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "Variavel obrigatoria ausente: defina SUPABASE_DB_URL ou DATABASE_URL "
            "com a connection string PostgreSQL administrativa."
        )
    return database_url


def sanitize_error(message: str) -> str:
    sanitized = message
    for name in (
        "SUPABASE_DB_URL",
        "DATABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_KEY",
    ):
        secret = os.getenv(name)
        if secret:
            sanitized = sanitized.replace(secret, f"[{name}]")
            if name in {"SUPABASE_DB_URL", "DATABASE_URL"}:
                password = unquote(urlparse(secret).password or "")
                if password:
                    sanitized = sanitized.replace(password, "[DATABASE_PASSWORD]")
    return sanitized


def migration_sql(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Migration nao encontrada: {path.relative_to(ROOT_DIR)}")

    sql = path.read_text(encoding="utf-8").strip()
    lowered = sql.lower()
    if lowered.startswith("begin;"):
        sql = sql[len("begin;") :].lstrip()
    if sql.lower().endswith("commit;"):
        sql = sql[: -len("commit;")].rstrip()
    return sql


def apply_migrations(connection: Any) -> None:
    for path in MIGRATION_PATHS:
        print(f"Aplicando {path.relative_to(ROOT_DIR)}...")
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(migration_sql(path))
        except Exception as exc:
            raise RuntimeError(
                f"Falha ao aplicar {path.name}: {sanitize_error(str(exc))}"
            ) from exc
        print(f"Aplicada: {path.name}")


def validate_risk_treatment(connection: Any) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select column_name
            from information_schema.columns
            where table_schema = 'public'
              and table_name = 'riscos'
              and column_name = any(%s)
            """,
            (list(REQUIRED_RISK_COLUMNS),),
        )
        columns = {row[0] for row in cursor.fetchall()}

        cursor.execute(
            """
            select exists (
                select 1
                from pg_constraint
                where conrelid = 'public.riscos'::regclass
                  and contype = 'c'
                  and pg_get_constraintdef(oid) like '%status_plano%'
            )
            """
        )
        constraint_present = cursor.fetchone()[0]

        cursor.execute(
            """
            select exists (
                select 1
                from pg_indexes
                where schemaname = 'public'
                  and tablename = 'riscos'
                  and indexname = 'idx_riscos_status_plano'
            )
            """
        )
        index_present = cursor.fetchone()[0]

    missing = REQUIRED_RISK_COLUMNS - columns
    if missing or not constraint_present or not index_present:
        raise RuntimeError(
            "Validacao de Risk Treatment falhou: "
            f"colunas ausentes={sorted(missing)}, "
            f"constraint={constraint_present}, index={index_present}."
        )

    return {
        "columns": sorted(columns),
        "constraint_present": constraint_present,
        "index_present": index_present,
    }


def validate_storage(connection: Any) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select public, file_size_limit, allowed_mime_types
            from storage.buckets
            where id = 'evidencias'
            """
        )
        bucket = cursor.fetchone()
        if not bucket:
            raise RuntimeError("Validacao de Storage falhou: bucket evidencias ausente.")

        cursor.execute(
            """
            select schemaname, tablename, policyname, cmd
            from pg_policies
            where (
                schemaname = 'public'
                and tablename = 'evidencias'
                and policyname = 'anon_insert_evidencias'
            ) or (
                schemaname = 'storage'
                and tablename = 'objects'
                and policyname in (
                    'anon_insert_evidencias',
                    'anon_select_evidencias'
                )
            )
            """
        )
        policies = {
            (row[0], row[1], row[2], row[3])
            for row in cursor.fetchall()
        }

    is_public, file_size_limit, allowed_mime_types = bucket
    expected_policies = {
        ("public", "evidencias", "anon_insert_evidencias", "INSERT"),
        ("storage", "objects", "anon_insert_evidencias", "INSERT"),
        ("storage", "objects", "anon_select_evidencias", "SELECT"),
    }
    missing_policies = expected_policies - policies
    missing_mime_types = REQUIRED_MIME_TYPES - set(allowed_mime_types or [])
    if is_public or file_size_limit != 20 * 1024 * 1024:
        raise RuntimeError(
            "Validacao de Storage falhou: privacidade ou limite divergente."
        )
    if missing_mime_types or missing_policies:
        raise RuntimeError(
            "Validacao de Storage falhou: "
            f"tipos ausentes={sorted(missing_mime_types)}, "
            f"politicas ausentes={sorted(missing_policies)}."
        )

    return {
        "bucket_present": True,
        "private": not is_public,
        "file_size_limit": file_size_limit,
        "allowed_mime_types": sorted(allowed_mime_types),
        "policies_present": len(expected_policies),
    }


def validate_risk_persistence(connection: Any) -> bool:
    original_autocommit = connection.autocommit
    connection.autocommit = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("select id from public.riscos order by created_at limit 1")
            row = cursor.fetchone()
            if not row:
                raise RuntimeError(
                    "Validacao de persistencia requer ao menos um risco cadastrado."
                )

            cursor.execute(
                """
                update public.riscos
                set plano_acao = %s,
                    responsavel_plano = %s,
                    prazo_plano = current_date,
                    status_plano = %s
                where id = %s
                returning plano_acao, responsavel_plano, prazo_plano, status_plano
                """,
                (
                    "Validacao automatica de persistencia",
                    "ORION validation",
                    "Em andamento",
                    row[0],
                ),
            )
            persisted = cursor.fetchone()
            if not persisted or persisted[3] != "Em andamento":
                raise RuntimeError("Validacao de persistencia de Risk Treatment falhou.")
        return True
    finally:
        connection.rollback()
        connection.autocommit = original_autocommit


def validate_demo_evidence(connection: Any) -> int:
    with connection.cursor() as cursor:
        cursor.execute("select count(*) from public.evidencias")
        count = cursor.fetchone()[0]
    if count < 1:
        raise RuntimeError("Validacao falhou: nenhuma evidencia demo encontrada.")
    return count


def main() -> int:
    load_dotenv(ROOT_DIR / ".env")
    try:
        database_url = require_database_url()
        connection = psycopg2.connect(database_url, connect_timeout=20)
        try:
            apply_migrations(connection)
            risk_treatment = validate_risk_treatment(connection)
            storage = validate_storage(connection)
            persistence_ok = validate_risk_persistence(connection)
            evidence_count = validate_demo_evidence(connection)
        finally:
            connection.close()

        print("Validacao concluida.")
        print(f"Risk Treatment: {len(risk_treatment['columns'])} colunas confirmadas.")
        print(
            "Storage: bucket privado confirmado, "
            f"limite={storage['file_size_limit']} bytes, "
            f"tipos={len(storage['allowed_mime_types'])}, "
            f"politicas={storage['policies_present']}."
        )
        print(f"Persistencia de Risk Treatment: {'ok' if persistence_ok else 'falhou'}.")
        print(f"Evidencias existentes: {evidence_count}.")
        return 0
    except Exception as exc:
        print(
            f"Erro ao aplicar migrations: {sanitize_error(str(exc))}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
