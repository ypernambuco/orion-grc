-- ORION GRC demo seed
-- Execute manualmente no SQL Editor do Supabase apenas quando quiser popular a demo.
-- Este arquivo nao cria usuarios autenticados, nao usa service_role e nao altera secrets.

begin;

with seed_areas(nome) as (
    values
        ('Financeiro'),
        ('Juridico'),
        ('RH'),
        ('TI'),
        ('Operacoes')
),
upsert_areas as (
    insert into areas (nome)
    select nome
    from seed_areas
    on conflict (nome) do update set nome = excluded.nome
    returning id, nome
),
area_map as (
    select id, nome
    from upsert_areas
    union
    select id, nome
    from areas
    where nome in (select nome from seed_areas)
),
documentos_demo (
    id,
    nome,
    categoria,
    area_nome,
    responsavel,
    dias_vencimento,
    status,
    escopo_acesso
) as (
    values
        (
            '11111111-1111-4111-8111-111111111001',
            'Contrato de prestacao de servicos contabeis',
            'Contrato',
            'Financeiro',
            'Marina Costa',
            42,
            'Vigente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111002',
            'Politica interna de aprovacao de pagamentos',
            'Politica',
            'Financeiro',
            'Bruno Almeida',
            -12,
            'Vencido',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111003',
            'Relatorio mensal de KPIs financeiros',
            'KPI',
            'Financeiro',
            'Marina Costa',
            7,
            'Pendente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111004',
            'Contrato master de fornecedor logistico',
            'Juridico',
            'Juridico',
            'Renata Soares',
            18,
            'Em revisao',
            'juridico'
        ),
        (
            '11111111-1111-4111-8111-111111111005',
            'Politica de privacidade e retencao documental',
            'Politica',
            'Juridico',
            'Felipe Martins',
            95,
            'Vigente',
            'juridico'
        ),
        (
            '11111111-1111-4111-8111-111111111006',
            'Dossie de auditoria trabalhista',
            'Auditoria',
            'RH',
            'Camila Rocha',
            -25,
            'Vencido',
            'restrito'
        ),
        (
            '11111111-1111-4111-8111-111111111007',
            'Fluxograma de admissao e desligamento',
            'Fluxograma',
            'RH',
            'Livia Nogueira',
            61,
            'Vigente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111008',
            'Relatorio de monitoramento de backups',
            'Relatorio',
            'TI',
            'Rafael Lima',
            3,
            'Pendente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111009',
            'Politica de seguranca da informacao',
            'Politica',
            'TI',
            'Patricia Menezes',
            120,
            'Vigente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111010',
            'Plano de continuidade operacional',
            'Controle',
            'Operacoes',
            'Diego Farias',
            28,
            'Em revisao',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111011',
            'Fluxograma de atendimento a incidentes operacionais',
            'Fluxograma',
            'Operacoes',
            'Aline Barbosa',
            75,
            'Vigente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111012',
            'Relatorio de auditoria de controles internos',
            'Auditoria',
            'Operacoes',
            'Diego Farias',
            -5,
            'Pendente',
            'geral'
        )
)
insert into documentos (
    id,
    nome,
    categoria,
    area_id,
    responsavel,
    vencimento,
    status,
    escopo_acesso
)
select
    documentos_demo.id::uuid,
    documentos_demo.nome,
    documentos_demo.categoria,
    area_map.id,
    documentos_demo.responsavel,
    current_date + documentos_demo.dias_vencimento,
    documentos_demo.status,
    documentos_demo.escopo_acesso
from documentos_demo
join area_map on area_map.nome = documentos_demo.area_nome
on conflict (id) do update set
    nome = excluded.nome,
    categoria = excluded.categoria,
    area_id = excluded.area_id,
    responsavel = excluded.responsavel,
    vencimento = excluded.vencimento,
    status = excluded.status,
    escopo_acesso = excluded.escopo_acesso;

with area_map as (
    select id, nome
    from areas
    where nome in ('Financeiro', 'Juridico', 'RH', 'TI', 'Operacoes')
),
riscos_demo (
    id,
    area_nome,
    descricao,
    probabilidade,
    impacto,
    risco,
    classificacao,
    escopo_acesso
) as (
    values
        (
            '22222222-2222-4222-8222-222222222001',
            'Financeiro',
            'Vencimento documental de politica de pagamentos sem revisao formal.',
            4,
            4,
            16,
            'Critico',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222002',
            'Financeiro',
            'Falha de controle interno na dupla aprovacao de despesas recorrentes.',
            3,
            5,
            15,
            'Alto',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222003',
            'Juridico',
            'Risco contratual por clausula de renovacao automatica sem alerta operacional.',
            4,
            5,
            20,
            'Critico',
            'juridico'
        ),
        (
            '22222222-2222-4222-8222-222222222004',
            'RH',
            'Ausencia de evidencia completa em dossie de auditoria trabalhista.',
            4,
            4,
            16,
            'Critico',
            'restrito'
        ),
        (
            '22222222-2222-4222-8222-222222222005',
            'TI',
            'Risco de seguranca da informacao por monitoramento irregular de backups.',
            3,
            5,
            15,
            'Alto',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222006',
            'TI',
            'Ausencia de evidencia de revisao de acessos privilegiados.',
            3,
            4,
            12,
            'Alto',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222007',
            'Operacoes',
            'Risco operacional por plano de continuidade ainda em revisao.',
            4,
            4,
            16,
            'Critico',
            'geral'
        ),
        (
            '22222222-2222-4222-8222-222222222008',
            'Operacoes',
            'Falha de controle interno na reconciliacao de indicadores de SLA.',
            2,
            4,
            8,
            'Medio',
            'geral'
        )
)
insert into riscos (
    id,
    area_id,
    descricao,
    probabilidade,
    impacto,
    risco,
    classificacao,
    escopo_acesso
)
select
    riscos_demo.id::uuid,
    area_map.id,
    riscos_demo.descricao,
    riscos_demo.probabilidade,
    riscos_demo.impacto,
    riscos_demo.risco,
    riscos_demo.classificacao,
    riscos_demo.escopo_acesso
from riscos_demo
join area_map on area_map.nome = riscos_demo.area_nome
on conflict (id) do update set
    area_id = excluded.area_id,
    descricao = excluded.descricao,
    probabilidade = excluded.probabilidade,
    impacto = excluded.impacto,
    risco = excluded.risco,
    classificacao = excluded.classificacao,
    escopo_acesso = excluded.escopo_acesso;

with evidencias_demo (
    id,
    documento_id,
    risco_id,
    nome,
    descricao,
    url_arquivo
) as (
    values
        (
            '33333333-3333-4333-8333-333333333001',
            '11111111-1111-4111-8111-111111111002',
            '22222222-2222-4222-8222-222222222001',
            'Ata de revisao pendente - pagamentos',
            'Registro de pendencia para revisao da politica interna de aprovacao de pagamentos.',
            null
        ),
        (
            '33333333-3333-4333-8333-333333333002',
            '11111111-1111-4111-8111-111111111004',
            '22222222-2222-4222-8222-222222222003',
            'Checklist juridico de renovacao contratual',
            'Checklist usado para validar clausulas criticas e gatilhos de renovacao.',
            null
        ),
        (
            '33333333-3333-4333-8333-333333333003',
            '11111111-1111-4111-8111-111111111006',
            '22222222-2222-4222-8222-222222222004',
            'Relatorio de auditoria trabalhista',
            'Documento de auditoria com lacunas de evidencia ainda em tratamento.',
            null
        ),
        (
            '33333333-3333-4333-8333-333333333004',
            '11111111-1111-4111-8111-111111111008',
            '22222222-2222-4222-8222-222222222005',
            'Log mensal de monitoramento de backups',
            'Relatorio de monitoramento usado como evidencia de controle de continuidade.',
            null
        ),
        (
            '33333333-3333-4333-8333-333333333005',
            '11111111-1111-4111-8111-111111111010',
            '22222222-2222-4222-8222-222222222007',
            'Plano de resposta a indisponibilidade operacional',
            'Documento de apoio para teste de continuidade e resposta a incidentes.',
            null
        )
)
insert into evidencias (
    id,
    documento_id,
    risco_id,
    nome,
    descricao,
    url_arquivo
)
select
    id::uuid,
    documento_id::uuid,
    risco_id::uuid,
    nome,
    descricao,
    url_arquivo
from evidencias_demo
on conflict (id) do update set
    documento_id = excluded.documento_id,
    risco_id = excluded.risco_id,
    nome = excluded.nome,
    descricao = excluded.descricao,
    url_arquivo = excluded.url_arquivo;

commit;
