create extension if not exists "pgcrypto";

create table if not exists areas (
    id uuid primary key default gen_random_uuid(),
    nome text not null unique,
    created_at timestamptz not null default now()
);

create table if not exists perfis (
    codigo text primary key,
    nome text not null,
    descricao text,
    created_at timestamptz not null default now()
);

insert into perfis (codigo, nome, descricao)
values
    ('admin', 'Admin', 'Acesso total ao sistema.'),
    ('governanca', 'Governanca', 'Acesso a todas as areas, documentos e riscos.'),
    ('juridico', 'Juridico', 'Acesso futuro a documentos e riscos juridicos.'),
    ('gestor_area', 'Gestor de area', 'Acesso futuro restrito a propria area.'),
    ('diretoria', 'Diretoria', 'Acesso futuro a dashboards e KPIs gerais.'),
    ('auditoria', 'Auditoria', 'Acesso futuro a documentos, evidencias e historico.')
on conflict (codigo) do update set
    nome = excluded.nome,
    descricao = excluded.descricao;

create table if not exists usuarios (
    id uuid primary key default gen_random_uuid(),
    auth_user_id uuid unique,
    nome text not null,
    email text unique,
    perfil_codigo text not null references perfis(codigo) on update cascade,
    area_id uuid references areas(id) on delete set null,
    ativo boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists documentos (
    id uuid primary key default gen_random_uuid(),
    nome text not null,
    categoria text not null,
    area_id uuid not null references areas(id) on delete restrict,
    responsavel text not null,
    vencimento date not null,
    status text not null,
    escopo_acesso text not null default 'geral'
        check (escopo_acesso in ('geral', 'area', 'juridico', 'restrito')),
    created_by uuid references usuarios(id) on delete set null,
    created_at timestamptz not null default now()
);

create table if not exists riscos (
    id uuid primary key default gen_random_uuid(),
    area_id uuid not null references areas(id) on delete restrict,
    descricao text not null,
    probabilidade integer not null check (probabilidade between 1 and 5),
    impacto integer not null check (impacto between 1 and 5),
    risco integer not null check (risco between 1 and 25),
    classificacao text not null check (classificacao in ('Baixo', 'Medio', 'Alto', 'Critico')),
    plano_acao text,
    responsavel_plano text,
    prazo_plano date,
    status_plano text check (
        status_plano in (
            'Não iniciado',
            'Nao iniciado',
            'Em andamento',
            'Concluído',
            'Concluido',
            'Atrasado'
        )
    ),
    escopo_acesso text not null default 'geral'
        check (escopo_acesso in ('geral', 'area', 'juridico', 'restrito')),
    created_by uuid references usuarios(id) on delete set null,
    created_at timestamptz not null default now()
);

create table if not exists evidencias (
    id uuid primary key default gen_random_uuid(),
    documento_id uuid references documentos(id) on delete cascade,
    risco_id uuid references riscos(id) on delete cascade,
    nome text not null,
    descricao text,
    url_arquivo text,
    created_by uuid references usuarios(id) on delete set null,
    created_at timestamptz not null default now(),
    check (num_nonnulls(documento_id, risco_id) >= 1)
);

create table if not exists historico_eventos (
    id uuid primary key default gen_random_uuid(),
    entidade text not null check (entidade in ('area', 'documento', 'risco', 'evidencia', 'usuario')),
    entidade_id uuid not null,
    acao text not null,
    detalhes jsonb not null default '{}'::jsonb,
    usuario_id uuid references usuarios(id) on delete set null,
    created_at timestamptz not null default now()
);

alter table documentos
    add column if not exists escopo_acesso text not null default 'geral'
        check (escopo_acesso in ('geral', 'area', 'juridico', 'restrito'));

alter table documentos
    add column if not exists created_by uuid references usuarios(id) on delete set null;

alter table riscos
    add column if not exists escopo_acesso text not null default 'geral'
        check (escopo_acesso in ('geral', 'area', 'juridico', 'restrito'));

alter table riscos
    add column if not exists created_by uuid references usuarios(id) on delete set null;

alter table riscos
    add column if not exists plano_acao text;

alter table riscos
    add column if not exists responsavel_plano text;

alter table riscos
    add column if not exists prazo_plano date;

alter table riscos
    add column if not exists status_plano text
        check (
            status_plano in (
                'Não iniciado',
                'Nao iniciado',
                'Em andamento',
                'Concluído',
                'Concluido',
                'Atrasado'
            )
        );

create index if not exists idx_documentos_area_id on documentos(area_id);
create index if not exists idx_documentos_status on documentos(status);
create index if not exists idx_documentos_vencimento on documentos(vencimento);
create index if not exists idx_documentos_escopo_acesso on documentos(escopo_acesso);
create index if not exists idx_riscos_area_id on riscos(area_id);
create index if not exists idx_riscos_classificacao on riscos(classificacao);
create index if not exists idx_riscos_escopo_acesso on riscos(escopo_acesso);
create index if not exists idx_riscos_status_plano on riscos(status_plano);
create index if not exists idx_usuarios_perfil_codigo on usuarios(perfil_codigo);
create index if not exists idx_usuarios_area_id on usuarios(area_id);
create index if not exists idx_evidencias_documento_id on evidencias(documento_id);
create index if not exists idx_evidencias_risco_id on evidencias(risco_id);
create index if not exists idx_historico_eventos_entidade on historico_eventos(entidade, entidade_id);

grant usage on schema public to anon;

grant select on
    public.areas,
    public.documentos,
    public.riscos,
    public.perfis,
    public.usuarios,
    public.evidencias,
    public.historico_eventos
to anon;

grant insert on
    public.areas,
    public.documentos,
    public.riscos,
    public.evidencias
to anon;

do $$
declare
    target_table text;
    policy_name text;
begin
    foreach target_table in array array[
        'areas',
        'documentos',
        'riscos',
        'perfis',
        'usuarios',
        'evidencias',
        'historico_eventos'
    ]
    loop
        policy_name := 'anon_select_' || target_table;

        if not exists (
            select 1
            from pg_policies
            where schemaname = 'public'
              and tablename = target_table
              and policyname = policy_name
        ) then
            execute format(
                'create policy %I on public.%I for select to anon using (true)',
                policy_name,
                target_table
            );
        end if;
    end loop;
end $$;

do $$
declare
    target_table text;
    policy_name text;
begin
    foreach target_table in array array['areas', 'documentos', 'riscos', 'evidencias']
    loop
        policy_name := 'anon_insert_' || target_table;

        if not exists (
            select 1
            from pg_policies
            where schemaname = 'public'
              and tablename = target_table
              and policyname = policy_name
        ) then
            execute format(
                'create policy %I on public.%I for insert to anon with check (true)',
                policy_name,
                target_table
            );
        end if;
    end loop;
end $$;

comment on table perfis is
    'Perfis preparados para controle de acesso futuro: admin, governanca, juridico, gestor_area, diretoria e auditoria.';
comment on table usuarios is
    'Tabela preparada para autenticacao futura. auth_user_id pode apontar para auth.users.id quando o login for implementado.';
comment on column usuarios.area_id is
    'Usado no futuro para restringir gestor_area a propria area.';
comment on column documentos.escopo_acesso is
    'Campo preparado para futuras politicas de acesso por perfil e area. Use juridico para itens juridicos.';
comment on column riscos.escopo_acesso is
    'Campo preparado para futuras politicas de acesso por perfil e area. Use juridico para riscos juridicos.';
comment on table evidencias is
    'Tabela futura para evidencias vinculadas a documentos ou riscos, especialmente para auditoria.';
comment on table historico_eventos is
    'Tabela futura para trilha de auditoria sem exigir login na V1.';
