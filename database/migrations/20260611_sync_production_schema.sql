begin;

-- Risk Treatment: additive synchronization only.
alter table public.riscos
    add column if not exists plano_acao text;

alter table public.riscos
    add column if not exists responsavel_plano text;

alter table public.riscos
    add column if not exists prazo_plano date;

alter table public.riscos
    add column if not exists status_plano text;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conrelid = 'public.riscos'::regclass
          and contype = 'c'
          and pg_get_constraintdef(oid) like '%status_plano%'
          and pg_get_constraintdef(oid) like '%Nao iniciado%'
          and pg_get_constraintdef(oid) like '%Em andamento%'
          and pg_get_constraintdef(oid) like '%Concluido%'
          and pg_get_constraintdef(oid) like '%Atrasado%'
    ) then
        alter table public.riscos
            add constraint riscos_status_plano_check
            check (
                status_plano is null
                or status_plano in (
                    'Nao iniciado',
                    'Em andamento',
                    'Concluido',
                    'Atrasado'
                )
            ) not valid;

        alter table public.riscos
            validate constraint riscos_status_plano_check;
    end if;
end $$;

-- Recreate versioned indexes only when absent.
create index if not exists idx_documentos_area_id
    on public.documentos(area_id);

create index if not exists idx_documentos_status
    on public.documentos(status);

create index if not exists idx_documentos_vencimento
    on public.documentos(vencimento);

create index if not exists idx_documentos_escopo_acesso
    on public.documentos(escopo_acesso);

create index if not exists idx_riscos_area_id
    on public.riscos(area_id);

create index if not exists idx_riscos_classificacao
    on public.riscos(classificacao);

create index if not exists idx_riscos_escopo_acesso
    on public.riscos(escopo_acesso);

create index if not exists idx_riscos_status_plano
    on public.riscos(status_plano);

-- Evidence structure verification. Fails safely if production is not compatible.
do $$
declare
    required_column text;
begin
    foreach required_column in array array[
        'id',
        'documento_id',
        'risco_id',
        'nome',
        'descricao',
        'url_arquivo',
        'created_by',
        'created_at'
    ]
    loop
        if not exists (
            select 1
            from information_schema.columns
            where table_schema = 'public'
              and table_name = 'evidencias'
              and column_name = required_column
        ) then
            raise exception
                'Estrutura incompatível: coluna public.evidencias.% ausente.',
                required_column;
        end if;
    end loop;
end $$;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conrelid = 'public.evidencias'::regclass
          and contype = 'c'
          and pg_get_constraintdef(oid) like '%num_nonnulls(documento_id, risco_id)%'
    ) then
        alter table public.evidencias
            add constraint evidencias_vinculo_check
            check (num_nonnulls(documento_id, risco_id) >= 1) not valid;

        alter table public.evidencias
            validate constraint evidencias_vinculo_check;
    end if;
end $$;

create index if not exists idx_evidencias_documento_id
    on public.evidencias(documento_id);

create index if not exists idx_evidencias_risco_id
    on public.evidencias(risco_id);

create index if not exists idx_usuarios_perfil_codigo
    on public.usuarios(perfil_codigo);

create index if not exists idx_usuarios_area_id
    on public.usuarios(area_id);

create index if not exists idx_historico_eventos_entidade
    on public.historico_eventos(entidade, entidade_id);

commit;
