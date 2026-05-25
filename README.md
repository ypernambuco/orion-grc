# ORION GRC

ORION GRC is a SaaS-style Governance, Risk & Compliance demo for small businesses that need a simple way to centralize documents, monitor risks and understand operational efficiency by area.

Developed by Vaekor Labs.

---

## Live Demo

[https://orion-grc.streamlit.app/](https://orion-grc.streamlit.app/)

---

## Status

Professional MVP demo online and validated in production.

Current scope:

- Public demo without authentication
- No role-based access control yet
- No AI features yet
- Supabase/PostgreSQL persistence
- Demo seed available, but not executed automatically

---

## Product Vision

ORION GRC helps small businesses bring governance into one operational workspace.

The product is designed to help teams:

- Centralize contracts, internal policies, audit files, KPI reports and monitoring evidence
- Track document expiration, pending reviews and missing evidence
- Monitor operational, contractual, internal control and information security risks
- Visualize efficiency by Finance, Legal, HR, IT and Operations
- Support governance routines, audit preparation and executive follow-up

---

## Problem Solved

Small businesses often manage governance through disconnected spreadsheets, folders and informal reminders. This makes it hard to know which documents are expired, which risks need attention and which areas are operating outside the expected control flow.

ORION GRC turns this into a single dashboard with documents, areas, risks and operational KPIs.

---

## Screenshots

### Dashboard

![Dashboard](assets/screenshots/dashboard.png)

### Areas

![Areas](assets/screenshots/areas.png)

### Documentos

![Documentos](assets/screenshots/documentos.png)

### Riscos

![Riscos](assets/screenshots/riscos.png)

---

## Features

- Executive governance dashboard
- General conformity KPI
- Expired and pending document monitoring
- Risk scoring by probability and impact
- Risk classification: Low, Medium, High and Critical
- Area-based tracking
- Document lifecycle management
- Operational efficiency by area
- Plotly analytics dashboards
- Supabase cloud persistence
- Future-ready database structure for profiles, users, evidence and audit history

---

## Modules

### Dashboard

- General conformity
- Expired documents
- Pending documents
- Critical risks
- Risks by area
- Documents by status
- Operational efficiency by area

### Areas

- Area registration
- Area listing
- Foundation for area ownership and future access rules

### Documents

- Document registration
- Category, owner, expiration date and status
- Support for contracts, policies, procedures, reports, flowcharts, KPIs and audit files

### Risks

- Risk registration
- Automatic score calculation
- Impact and probability sliders
- Operational prioritization by classification

---

## Demo Data

Professional demo data is available in:

```text
database/seed_demo.sql
```

The seed includes fictional data for:

- Financeiro
- Juridico
- RH
- TI
- Operacoes

It includes realistic documents such as contracts, internal policies, monitoring reports, flowcharts, KPIs and audit documents. It also includes realistic risks such as document expiration, internal control failure, missing evidence, contractual risk, operational risk and information security risk.

The seed is intentionally manual. It is not executed automatically by the app.

---

## Stack

- Streamlit
- Supabase/PostgreSQL
- Pandas
- Plotly

---

## Setup

1. Create a virtual environment:

```bash
python -m venv .venv
```

2. Activate the environment and install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the environment example:

```bash
cp .env.example .env
```

4. Fill `.env` with the Supabase project URL and anon public key:

```env
SUPABASE_URL=
SUPABASE_KEY=
```

Use the Supabase `anon public` key only.

Do not use `service_role` in the app.

On Streamlit Cloud, configure the same values in `st.secrets`:

```toml
SUPABASE_URL = "your-project-url"
SUPABASE_KEY = "your-anon-public-key"
```

5. Execute the database schema in Supabase SQL Editor:

```text
database/schema.sql
```

6. Optionally execute the manual demo seed:

```text
database/seed_demo.sql
```

7. Run locally:

```bash
streamlit run app.py
```

For Streamlit Community Cloud:

- Repository: `ypernambuco/orion-grc`
- Branch: `main`
- Main file path: `app.py`

Never commit `.env`, credentials or Supabase secrets.

---

## Security Notes

- `.env` must remain ignored by Git
- Supabase credentials must be stored locally or in `st.secrets`
- The app rejects `service_role` keys
- Authentication is intentionally not implemented in this version
- Role-based access control is intentionally not implemented in this version

---

## Future Access Architecture

This version does not implement login, but the database already prepares the foundation for future access control by profile and area.

Planned profiles:

- admin: full access
- governanca: all areas, documents and risks
- juridico: legal documents and legal risks
- gestor_area: own area only
- diretoria: dashboards and general KPIs
- auditoria: documents, evidence and history

The schema includes future-ready tables for:

- perfis
- usuarios
- evidencias
- historico_eventos

The optional `auth_user_id` column in `usuarios` can be connected to `auth.users.id` when authentication is implemented.

---

## Risk Classification

- 1 to 4: Baixo
- 5 to 9: Medio
- 10 to 15: Alto
- 16 to 25: Critico

---

## Roadmap

- [x] Initial project structure
- [x] Supabase integration
- [x] Professional SaaS-style presentation
- [x] Dashboard MVP
- [x] Area management
- [x] Document management
- [x] Risk management
- [x] Manual professional demo seed
- [x] Production demo on Streamlit Cloud
- [ ] Screenshot assets for README
- [ ] Authentication
- [ ] Role-based access control
- [ ] Multi-company workspace
- [ ] Evidence upload
- [ ] Advanced audit trail
- [ ] Automated alerts
- [ ] Advanced executive dashboard
- [ ] Operational AI assistant
- [ ] Operational graph visualization

---

## License

MIT License
