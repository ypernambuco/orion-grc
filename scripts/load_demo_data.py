from __future__ import annotations

import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from supabase import create_client


ROOT_DIR = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT_DIR / "database" / "seed_demo.sql"


def sanitize_error(message: str, secret: str | None) -> str:
    if not secret:
        return message
    return message.replace(secret, "[SUPABASE_SERVICE_ROLE_KEY]")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")
    return value


def parse_sql_value(raw_value: str) -> Any:
    raw_value = raw_value.strip()
    if raw_value.lower() == "null":
        return None
    if raw_value.startswith("'") and raw_value.endswith("'"):
        return raw_value[1:-1].replace("''", "'")
    if re.fullmatch(r"-?\d+", raw_value):
        return int(raw_value)
    return raw_value


def split_tuple_values(tuple_body: str) -> list[Any]:
    values: list[str] = []
    current: list[str] = []
    in_string = False
    index = 0

    while index < len(tuple_body):
        char = tuple_body[index]

        if char == "'":
            current.append(char)
            if in_string and index + 1 < len(tuple_body) and tuple_body[index + 1] == "'":
                current.append(tuple_body[index + 1])
                index += 2
                continue
            in_string = not in_string
            index += 1
            continue

        if char == "," and not in_string:
            values.append("".join(current).strip())
            current = []
            index += 1
            continue

        current.append(char)
        index += 1

    if current:
        values.append("".join(current).strip())

    return [parse_sql_value(value) for value in values]


def parse_values_block(sql: str, cte_name: str) -> list[list[Any]]:
    cte_match = re.search(rf"\b{re.escape(cte_name)}\s*\(", sql)
    if not cte_match:
        raise RuntimeError(f"Bloco {cte_name} nao encontrado em {SEED_PATH}")

    values_match = re.search(r"\bvalues\b", sql[cte_match.end() :], flags=re.IGNORECASE)
    if not values_match:
        raise RuntimeError(f"Secao values nao encontrada para {cte_name}")

    index = cte_match.end() + values_match.end()
    rows: list[list[Any]] = []

    while index < len(sql):
        while index < len(sql) and sql[index].isspace():
            index += 1

        if index >= len(sql) or sql[index] != "(":
            break

        start = index + 1
        index += 1
        in_string = False
        depth = 1

        while index < len(sql) and depth > 0:
            char = sql[index]

            if char == "'":
                if in_string and index + 1 < len(sql) and sql[index + 1] == "'":
                    index += 2
                    continue
                in_string = not in_string
                index += 1
                continue

            if not in_string:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        break

            index += 1

        if depth != 0:
            raise RuntimeError(f"Tupla incompleta no bloco {cte_name}")

        rows.append(split_tuple_values(sql[start:index]))
        index += 1

        while index < len(sql) and sql[index].isspace():
            index += 1

        if index < len(sql) and sql[index] == ",":
            index += 1
            continue

        break

    return rows


def parse_seed(sql: str) -> dict[str, list[dict[str, Any]]]:
    area_rows = parse_values_block(sql, "seed_areas")
    document_rows = parse_values_block(sql, "documentos_demo")
    risk_rows = parse_values_block(sql, "riscos_demo")
    evidence_rows = parse_values_block(sql, "evidencias_demo")

    document_columns = [
        "id",
        "nome",
        "categoria",
        "area_nome",
        "responsavel",
        "dias_vencimento",
        "status",
        "escopo_acesso",
    ]
    risk_columns = [
        "id",
        "area_nome",
        "descricao",
        "probabilidade",
        "impacto",
        "risco",
        "classificacao",
        "escopo_acesso",
    ]
    evidence_columns = [
        "id",
        "documento_id",
        "risco_id",
        "nome",
        "descricao",
        "url_arquivo",
    ]

    return {
        "areas": [{"nome": row[0]} for row in area_rows],
        "documentos": [dict(zip(document_columns, row)) for row in document_rows],
        "riscos": [dict(zip(risk_columns, row)) for row in risk_rows],
        "evidencias": [dict(zip(evidence_columns, row)) for row in evidence_rows],
    }


def normalize_legacy_area_names(supabase: Any) -> None:
    existing = supabase.table("areas").select("nome").execute().data or []
    area_names = {area["nome"] for area in existing}

    if "RH" in area_names and "Recursos Humanos" not in area_names:
        supabase.table("areas").update({"nome": "Recursos Humanos"}).eq("nome", "RH").execute()

    if "TI" in area_names and "Tecnologia da Informacao" not in area_names:
        supabase.table("areas").update({"nome": "Tecnologia da Informacao"}).eq("nome", "TI").execute()


def count_rows(supabase: Any, table_name: str) -> int:
    data = supabase.table(table_name).select("id").execute().data or []
    return len(data)


def load_demo_data() -> None:
    load_dotenv(ROOT_DIR / ".env")

    supabase_url = require_env("SUPABASE_URL")
    service_role_key = require_env("SUPABASE_SERVICE_ROLE_KEY")

    if not SEED_PATH.exists():
        raise RuntimeError(f"Arquivo de seed nao encontrado: {SEED_PATH}")

    sql = SEED_PATH.read_text(encoding="utf-8")
    seed = parse_seed(sql)
    supabase = create_client(supabase_url, service_role_key)

    normalize_legacy_area_names(supabase)

    supabase.table("areas").upsert(seed["areas"], on_conflict="nome").execute()
    areas = supabase.table("areas").select("id, nome").execute().data or []
    area_map = {area["nome"]: area["id"] for area in areas}

    today = date.today()
    documentos = []
    for document in seed["documentos"]:
        documentos.append(
            {
                "id": document["id"],
                "nome": document["nome"],
                "categoria": document["categoria"],
                "area_id": area_map[document["area_nome"]],
                "responsavel": document["responsavel"],
                "vencimento": (today + timedelta(days=document["dias_vencimento"])).isoformat(),
                "status": document["status"],
                "escopo_acesso": document["escopo_acesso"],
            }
        )

    riscos = []
    for risk in seed["riscos"]:
        riscos.append(
            {
                "id": risk["id"],
                "area_id": area_map[risk["area_nome"]],
                "descricao": risk["descricao"],
                "probabilidade": risk["probabilidade"],
                "impacto": risk["impacto"],
                "risco": risk["risco"],
                "classificacao": risk["classificacao"],
                "escopo_acesso": risk["escopo_acesso"],
            }
        )

    supabase.table("documentos").upsert(documentos, on_conflict="id").execute()
    supabase.table("riscos").upsert(riscos, on_conflict="id").execute()
    supabase.table("evidencias").upsert(seed["evidencias"], on_conflict="id").execute()

    print("Massa demo carregada com sucesso.")
    print(f"Areas: {count_rows(supabase, 'areas')}")
    print(f"Documentos: {count_rows(supabase, 'documentos')}")
    print(f"Riscos: {count_rows(supabase, 'riscos')}")


def main() -> int:
    try:
        load_demo_data()
        return 0
    except Exception as exc:
        secret = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        print(f"Erro ao carregar massa demo: {sanitize_error(str(exc), secret)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
