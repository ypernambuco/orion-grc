-- ORION GRC corporate demo seed
-- Execute manualmente no SQL Editor do Supabase apenas quando quiser popular a demo.
-- Este arquivo nao cria usuarios autenticados, nao usa service_role e nao altera secrets.

begin;

-- Normaliza nomes curtos da massa anterior quando ainda nao existe a area corporativa completa.
update areas
set nome = 'Recursos Humanos'
where nome = 'RH'
  and not exists (select 1 from areas where nome = 'Recursos Humanos');

update areas
set nome = 'Tecnologia da Informacao'
where nome = 'TI'
  and not exists (select 1 from areas where nome = 'Tecnologia da Informacao');

with seed_areas(nome) as (
    values
        ('Financeiro'),
        ('Juridico'),
        ('Compliance'),
        ('Recursos Humanos'),
        ('Tecnologia da Informacao'),
        ('Operacoes'),
        ('Compras'),
        ('Auditoria Interna')
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
            'Codigo de Conduta Corporativa',
            'Politica',
            'Compliance',
            'Helena Duarte',
            120,
            'Vigente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111002',
            'Politica Anticorrupcao e Relacionamento com Terceiros',
            'Politica',
            'Compliance',
            'Marcos Vieira',
            -18,
            'Vencido',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111003',
            'Relatorio de Conformidade Trimestral',
            'Relatorio',
            'Compliance',
            'Helena Duarte',
            9,
            'Pendente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111004',
            'Politica de Privacidade LGPD',
            'Politica',
            'Juridico',
            'Renata Soares',
            64,
            'Vigente',
            'juridico'
        ),
        (
            '11111111-1111-4111-8111-111111111005',
            'Contrato de Fornecedor Estrategico de Logistica',
            'Contrato',
            'Juridico',
            'Felipe Martins',
            21,
            'Vigente',
            'juridico'
        ),
        (
            '11111111-1111-4111-8111-111111111006',
            'Matriz de Obrigacoes Contratuais Criticas',
            'Evidencia',
            'Juridico',
            'Renata Soares',
            4,
            'Pendente',
            'juridico'
        ),
        (
            '11111111-1111-4111-8111-111111111007',
            'Politica de Seguranca da Informacao',
            'Politica',
            'Tecnologia da Informacao',
            'Patricia Menezes',
            92,
            'Vigente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111008',
            'Procedimento de Gestao de Acessos Privilegiados',
            'Procedimento',
            'Tecnologia da Informacao',
            'Rafael Lima',
            -7,
            'Vencido',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111009',
            'Procedimento de Backup e Recuperacao',
            'Procedimento',
            'Tecnologia da Informacao',
            'Patricia Menezes',
            15,
            'Vigente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111010',
            'Plano de Continuidade de Negocios',
            'Procedimento',
            'Operacoes',
            'Diego Farias',
            28,
            'Vigente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111011',
            'Procedimento de Resposta a Incidentes Operacionais',
            'Procedimento',
            'Operacoes',
            'Aline Barbosa',
            51,
            'Vigente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111012',
            'Relatorio de Indicadores de SLA Operacional',
            'Relatorio',
            'Operacoes',
            'Diego Farias',
            7,
            'Pendente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111013',
            'Politica de Compras Corporativas',
            'Politica',
            'Compras',
            'Carolina Mendes',
            138,
            'Vigente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111014',
            'Procedimento de Homologacao de Fornecedores',
            'Procedimento',
            'Compras',
            'Eduardo Nunes',
            33,
            'Vigente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111015',
            'Evidencia de Due Diligence de Terceiros',
            'Evidencia',
            'Compras',
            'Carolina Mendes',
            11,
            'Pendente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111016',
            'Matriz de Segregacao de Funcoes Financeiras',
            'Evidencia',
            'Financeiro',
            'Bruno Almeida',
            76,
            'Vigente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111017',
            'Politica de Aprovacao de Pagamentos',
            'Politica',
            'Financeiro',
            'Marina Costa',
            -31,
            'Vencido',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111018',
            'Relatorio de Controles Financeiros Mensais',
            'Relatorio',
            'Financeiro',
            'Marina Costa',
            19,
            'Vigente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111019',
            'Procedimento de Fechamento Contabil',
            'Procedimento',
            'Financeiro',
            'Bruno Almeida',
            45,
            'Vigente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111020',
            'Politica de Recrutamento e Desligamento',
            'Politica',
            'Recursos Humanos',
            'Camila Rocha',
            101,
            'Vigente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111021',
            'Dossie de Auditoria Trabalhista',
            'Auditoria',
            'Recursos Humanos',
            'Livia Nogueira',
            13,
            'Pendente',
            'restrito'
        ),
        (
            '11111111-1111-4111-8111-111111111022',
            'Matriz de Treinamentos Obrigatorios',
            'Evidencia',
            'Recursos Humanos',
            'Camila Rocha',
            60,
            'Vigente',
            'area'
        ),
        (
            '11111111-1111-4111-8111-111111111023',
            'Plano Anual de Auditoria Interna',
            'Auditoria',
            'Auditoria Interna',
            'Sofia Andrade',
            88,
            'Vigente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111024',
            'Relatorio de Auditoria Interna de Controles',
            'Auditoria',
            'Auditoria Interna',
            'Gustavo Teixeira',
            36,
            'Vigente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111025',
            'Evidencia de Testes de Controles Chave',
            'Evidencia',
            'Auditoria Interna',
            'Sofia Andrade',
            6,
            'Vigente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111026',
            'Procedimento de Gestao de Crises Corporativas',
            'Procedimento',
            'Operacoes',
            'Aline Barbosa',
            72,
            'Vigente',
            'geral'
        ),
        (
            '11111111-1111-4111-8111-111111111027',
            'Politica de Retencao e Classificacao de Dados',
            'Politica',
            'Tecnologia da Informacao',
            'Rafael Lima',
            114,
            'Vigente',
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
    where nome in (
        'Financeiro',
        'Juridico',
        'Compliance',
        'Recursos Humanos',
        'Tecnologia da Informacao',
        'Operacoes',
        'Compras',
        'Auditoria Interna'
    )
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
            'Tecnologia da Informacao',
            'Vazamento de dados sensiveis por falha de controle de acesso.',
            4,
            5,
            20,
            'Critico',
            'geral'
        ),
        (
            '22222222-2222-4222-8222-222222222002',
            'Tecnologia da Informacao',
            'Falha de backup corporativo em sistemas criticos.',
            3,
            5,
            15,
            'Alto',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222003',
            'Tecnologia da Informacao',
            'Acesso nao autorizado a sistemas criticos por credenciais privilegiadas.',
            4,
            4,
            16,
            'Critico',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222004',
            'Compras',
            'Dependencia de fornecedor estrategico sem plano de contingencia.',
            3,
            4,
            12,
            'Alto',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222005',
            'Compliance',
            'Nao conformidade LGPD por evidencias incompletas de tratamento de dados.',
            3,
            5,
            15,
            'Alto',
            'geral'
        ),
        (
            '22222222-2222-4222-8222-222222222006',
            'Financeiro',
            'Fraude interna por falha de segregacao de funcoes financeiras.',
            4,
            5,
            20,
            'Critico',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222007',
            'Operacoes',
            'Interrupcao de servicos criticos por indisponibilidade operacional.',
            3,
            5,
            15,
            'Alto',
            'geral'
        ),
        (
            '22222222-2222-4222-8222-222222222008',
            'Auditoria Interna',
            'Ausencia de evidencias de auditoria para controles chave.',
            3,
            4,
            12,
            'Alto',
            'geral'
        ),
        (
            '22222222-2222-4222-8222-222222222009',
            'Compras',
            'Falha em processo de compras por homologacao incompleta de terceiros.',
            3,
            3,
            9,
            'Medio',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222010',
            'Financeiro',
            'Exposicao financeira indevida por aprovacao manual fora da politica.',
            3,
            3,
            9,
            'Medio',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222011',
            'Recursos Humanos',
            'Perda de conhecimento organizacional em processos criticos.',
            3,
            3,
            9,
            'Medio',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222012',
            'Compliance',
            'Descumprimento de politica corporativa por baixa adesao a treinamentos.',
            2,
            4,
            8,
            'Medio',
            'geral'
        ),
        (
            '22222222-2222-4222-8222-222222222013',
            'Tecnologia da Informacao',
            'Indisponibilidade de infraestrutura por capacidade insuficiente.',
            3,
            3,
            9,
            'Medio',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222014',
            'Operacoes',
            'Erro humano em processo critico sem dupla verificacao.',
            2,
            4,
            8,
            'Medio',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222015',
            'Juridico',
            'Falha em gestao de terceiros por clausulas contratuais desatualizadas.',
            2,
            4,
            8,
            'Medio',
            'juridico'
        ),
        (
            '22222222-2222-4222-8222-222222222016',
            'Auditoria Interna',
            'Atraso em plano de acao de auditoria interna.',
            2,
            4,
            8,
            'Medio',
            'geral'
        ),
        (
            '22222222-2222-4222-8222-222222222017',
            'Financeiro',
            'Lancamento contabil incorreto identificado apos conciliacao.',
            2,
            2,
            4,
            'Baixo',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222018',
            'Recursos Humanos',
            'Atraso pontual em atualizacao cadastral de colaboradores.',
            2,
            2,
            4,
            'Baixo',
            'area'
        ),
        (
            '22222222-2222-4222-8222-222222222019',
            'Operacoes',
            'Oscilacao em indicador de SLA sem impacto ao cliente final.',
            1,
            3,
            3,
            'Baixo',
            'geral'
        ),
        (
            '22222222-2222-4222-8222-222222222020',
            'Juridico',
            'Renovacao contratual com pendencia documental de baixa materialidade.',
            2,
            2,
            4,
            'Baixo',
            'juridico'
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

with planos_acao_demo (
    risco_id,
    plano_acao,
    responsavel_plano,
    dias_prazo,
    status_plano
) as (
    values
        (
            '22222222-2222-4222-8222-222222222001',
            'Implementar MFA corporativo e revisar controles de acesso.',
            'Equipe de Seguranca',
            30,
            'Em andamento'
        ),
        (
            '22222222-2222-4222-8222-222222222002',
            'Executar testes de restauracao e formalizar evidencias mensais.',
            'Infraestrutura',
            -10,
            'Concluido'
        ),
        (
            '22222222-2222-4222-8222-222222222003',
            'Revisar acessos privilegiados e reduzir credenciais permanentes.',
            'Equipe de Seguranca',
            -5,
            'Atrasado'
        ),
        (
            '22222222-2222-4222-8222-222222222004',
            'Formalizar plano de contingencia para fornecedores estrategicos.',
            null,
            45,
            'Nao iniciado'
        ),
        (
            '22222222-2222-4222-8222-222222222005',
            'Completar evidencias LGPD e revisar bases legais prioritarias.',
            'DPO',
            20,
            'Em andamento'
        ),
        (
            '22222222-2222-4222-8222-222222222007',
            'Atualizar plano de continuidade e executar simulacao operacional.',
            'Operacoes',
            60,
            'Nao iniciado'
        ),
        (
            '22222222-2222-4222-8222-222222222008',
            'Consolidar evidencias dos controles chave de auditoria.',
            'Auditoria Interna',
            -15,
            'Atrasado'
        ),
        (
            '22222222-2222-4222-8222-222222222009',
            'Revisar homologacao e due diligence dos fornecedores ativos.',
            'Compras',
            -5,
            'Concluido'
        ),
        (
            '22222222-2222-4222-8222-222222222010',
            'Automatizar aprovacao financeira e reforcar limites de alcada.',
            'Controladoria',
            25,
            'Em andamento'
        ),
        (
            '22222222-2222-4222-8222-222222222012',
            'Reforcar treinamento e monitorar adesao a politica corporativa.',
            'Compliance',
            10,
            'Em andamento'
        ),
        (
            '22222222-2222-4222-8222-222222222016',
            'Regularizar planos de acao pendentes da auditoria interna.',
            'Auditoria Interna',
            -3,
            'Atrasado'
        ),
        (
            '22222222-2222-4222-8222-222222222017',
            'Corrigir lancamento e reforcar conciliacao automatizada.',
            'Financeiro',
            -20,
            'Concluido'
        )
)
update riscos
set
    plano_acao = planos_acao_demo.plano_acao,
    responsavel_plano = planos_acao_demo.responsavel_plano,
    prazo_plano = current_date + planos_acao_demo.dias_prazo,
    status_plano = planos_acao_demo.status_plano
from planos_acao_demo
where riscos.id = planos_acao_demo.risco_id::uuid;

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
            '22222222-2222-4222-8222-222222222012',
            'Plano de acao - politica anticorrupcao',
            'Evidencia de revisao pendente da politica anticorrupcao e reforco de treinamento corporativo.',
            null
        ),
        (
            '33333333-3333-4333-8333-333333333002',
            '11111111-1111-4111-8111-111111111006',
            '22222222-2222-4222-8222-222222222015',
            'Checklist juridico de obrigacoes contratuais',
            'Checklist usado para validar clausulas criticas e gatilhos de renovacao.',
            null
        ),
        (
            '33333333-3333-4333-8333-333333333003',
            '11111111-1111-4111-8111-111111111008',
            '22222222-2222-4222-8222-222222222003',
            'Registro de revisao de acessos privilegiados',
            'Documento de controle com lacunas de revisao e evidencias pendentes.',
            null
        ),
        (
            '33333333-3333-4333-8333-333333333004',
            '11111111-1111-4111-8111-111111111009',
            '22222222-2222-4222-8222-222222222002',
            'Log mensal de testes de backup',
            'Evidencia de execucao de rotinas de backup e recuperacao corporativa.',
            null
        ),
        (
            '33333333-3333-4333-8333-333333333005',
            '11111111-1111-4111-8111-111111111010',
            '22222222-2222-4222-8222-222222222007',
            'Teste de continuidade operacional',
            'Documento de apoio para teste de continuidade e resposta a incidentes.',
            null
        ),
        (
            '33333333-3333-4333-8333-333333333006',
            '11111111-1111-4111-8111-111111111015',
            '22222222-2222-4222-8222-222222222009',
            'Evidencia de homologacao de fornecedores',
            'Registro de due diligence e validacao de terceiros estrategicos.',
            null
        ),
        (
            '33333333-3333-4333-8333-333333333007',
            '11111111-1111-4111-8111-111111111017',
            '22222222-2222-4222-8222-222222222006',
            'Ata de revisao de aprovacao de pagamentos',
            'Registro de pendencia relacionada a segregacao de funcoes e aprovacao financeira.',
            null
        ),
        (
            '33333333-3333-4333-8333-333333333008',
            '11111111-1111-4111-8111-111111111025',
            '22222222-2222-4222-8222-222222222008',
            'Evidencia de testes de controles chave',
            'Conjunto de evidencias usado pela auditoria interna para validar controles criticos.',
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
