# Production Schema Synchronization Report

Audit date: 2026-06-11

## Scope

Comparison between `database/schema.sql` and the Supabase project currently
configured by `SUPABASE_URL` / `SUPABASE_KEY`.

No product feature, UX, Dashboard, operational module, Auth or RLS change is
part of this synchronization.

## Confirmed Differences

All expected public tables are present:

- `areas`
- `perfis`
- `usuarios`
- `documentos`
- `riscos`
- `evidencias`
- `historico_eventos`

Missing columns confirmed in `public.riscos`:

- `plano_acao`
- `responsavel_plano`
- `prazo_plano`
- `status_plano`

Because `status_plano` is absent, its check constraint and supporting index are
also confirmed absent.

The current `public.evidencias` table contains all columns expected by the
versioned schema:

- `id`
- `documento_id`
- `risco_id`
- `nome`
- `descricao`
- `url_arquivo`
- `created_by`
- `created_at`

No Supabase Storage bucket named `evidencias` is visible in the current
environment. The evidence table remains compatible with file references through
`url_arquivo`, but permanent upload remains unavailable until Storage and its
security policies are provisioned separately.

## Constraints And Indexes

The public PostgREST API does not expose `pg_constraint`, `pg_indexes` or
`information_schema.columns`. Their remote presence cannot be proven using the
available anon key.

The generated migration handles this safely by:

- adding only missing Risk Treatment columns;
- adding the `riscos_status_plano_check` constraint only when absent;
- validating the constraint before commit;
- creating expected Risk Treatment and Evidence indexes only when absent;
- recreating every versioned operational index only when absent;
- adding the Evidence relationship check only when no equivalent check exists;
- verifying the Evidence column contract before commit.

## Migration

Run in Supabase SQL Editor:

```text
database/migrations/20260611_sync_production_schema.sql
```

The migration is additive and transactional. It does not use `DROP TABLE`,
remove existing columns or delete data.

Application status: **not applied from this workstation**. The configured
environment provides only the public anon key; no PostgreSQL administrative
connection or Supabase service role is available for DDL execution. Production
remains intentionally unchanged until an administrator runs the migration in
Supabase SQL Editor.

## Expected Impact

- Existing risks remain unchanged because all new columns are nullable.
- Risk Treatment persistence becomes available after migration.
- Existing documents, evidence records and relationships remain unchanged.
- Evidence uploads remain in session fallback mode until a Storage bucket and
  appropriate Storage policies are deliberately provisioned.

## Operational Risks

- Risk Treatment remains read-compatible but cannot persist plans before the
  migration is applied.
- Applying the migration during heavy writes can briefly lock `public.riscos`
  while columns and the constraint are added.
- Existing non-null `status_plano` values outside the allowed set would cause
  constraint validation to fail and roll back the transaction.
- Storage must not be opened to anonymous uploads without an explicit security
  review.
