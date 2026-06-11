begin;

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
                    'Não iniciado',
                    'Nao iniciado',
                    'Em andamento',
                    'Concluído',
                    'Concluido',
                    'Atrasado'
                )
            ) not valid;

        alter table public.riscos
            validate constraint riscos_status_plano_check;
    end if;
end $$;

create index if not exists idx_riscos_status_plano
    on public.riscos(status_plano);

commit;
