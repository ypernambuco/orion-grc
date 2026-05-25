# ORION GRC

Sistema web simples para gestao de governanca, riscos, documentos e eficiencia operacional.

## Stack

- Streamlit
- Supabase/PostgreSQL
- Pandas
- Plotly

## Configuracao

1. Crie um ambiente virtual:

```bash
python -m venv .venv
```

2. Ative o ambiente virtual e instale as dependencias:

```bash
pip install -r requirements.txt
```

3. Copie o arquivo de exemplo de ambiente:

```bash
cp .env.example .env
```

4. Preencha as variaveis no arquivo `.env`:

```env
SUPABASE_URL=https://cqsodsfdswdwzagfzvue.supabase.co
SUPABASE_KEY=
```

Use a chave `anon public` do Supabase em `SUPABASE_KEY`. Nao use `service_role` no app.

No Streamlit Cloud, configure as mesmas variaveis em `st.secrets`:

```toml
SUPABASE_URL = "https://cqsodsfdswdwzagfzvue.supabase.co"
SUPABASE_KEY = "sua-chave-anon-public"
```

5. Execute o SQL em `database/schema.sql` no SQL Editor do Supabase.

6. Rode o projeto:

```bash
streamlit run app.py
```

## Modulos

- Dashboard com indicadores e graficos.
- Areas com cadastro e listagem.
- Documentos com cadastro por area, responsavel, vencimento e status.
- Riscos com calculo automatico de pontuacao e classificacao.

## Arquitetura futura de acesso

Esta V1 nao implementa login, mas o banco ja deixa preparada a base para controle por perfil e area.

Perfis planejados:

- admin: acesso total.
- governanca: todas as areas, documentos e riscos.
- juridico: documentos e riscos juridicos.
- gestor_area: apenas a propria area.
- diretoria: dashboards e KPIs gerais.
- auditoria: documentos, evidencias e historico.

O schema inclui tabelas futuras para `perfis`, `usuarios`, `evidencias` e `historico_eventos`. A coluna `auth_user_id` em `usuarios` fica opcional nesta V1 e podera ser conectada ao `auth.users.id` do Supabase quando a autenticacao for implementada.

## Classificacao de riscos

- 1 a 4: Baixo
- 5 a 9: Medio
- 10 a 15: Alto
- 16 a 25: Critico
