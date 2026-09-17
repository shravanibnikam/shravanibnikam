<!-- Profile README — renders at https://github.com/shravanibnikam -->

<div align="center">

<img alt="" src="https://readme-typing-svg.demolab.com?font=Press+Start+2P&size=11&duration=99999&pause=99999&color=b04c7b&center=true&vCenter=true&width=800&height=16&lines=%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93" />

<img alt="New challenger approaching" src="https://readme-typing-svg.demolab.com?font=Press+Start+2P&size=11&duration=99999&pause=99999&color=e63d6a&center=true&vCenter=true&width=800&height=20&lines=NEW+CHALLENGER+APPROACHING..." />

<img alt="Shravani" src="https://readme-typing-svg.demolab.com?font=Press+Start+2P&size=40&duration=1800&pause=99999&color=b04c7b&center=true&vCenter=true&width=800&height=90&lines=SHRAVANI" />

<img alt="Backend, Python, PostgreSQL, Docker, ML/AI" src="https://readme-typing-svg.demolab.com?font=Press+Start+2P&size=9&duration=1400&pause=99999&color=b04c7b&center=true&vCenter=true&width=800&height=26&lines=BACKEND%20%E2%97%86%20PYTHON%20%E2%97%86%20POSTGRESQL%20%E2%97%86%20DOCKER%20%E2%97%86%20ML%2FAI&delay=2000" />

<img alt="Open to work: co-op 2027, full-time January 2028" src="https://readme-typing-svg.demolab.com?font=Press+Start+2P&size=8&duration=600&pause=500&color=e63d6a&center=true&vCenter=true&width=800&height=20&lines=%3E_%20OPEN%20TO%20WORK%20%E2%80%94%20CO-OP%202027%20%2F%20FULL-TIME%20JAN%202028&delay=3600" />

<img alt="" src="https://readme-typing-svg.demolab.com?font=Press+Start+2P&size=11&duration=99999&pause=99999&color=b04c7b&center=true&vCenter=true&width=800&height=16&lines=%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93%E2%96%93" />

**[Projects](#-projects) · [Skills](#-skill-tree) · [Experience](#-experience) · [Education](#-education) · [Contact](#-contact)**

</div>

---

## ▸ CHARACTER SHEET

```
┌────────────────────────────────────────────────────────────────┐
│  CLASS  ▸  Backend Engineer · ML/AI · Data Engineering         │
│  GUILD  ▸  Northeastern University · MS Computer Science       │
│  LEVEL  ▸  Graduate Student · expected December 2027           │
│  ZONE   ▸  Seattle, WA · open to relocation                    │
│  STACK  ▸  Python · PostgreSQL · Docker · Distributed Systems  │
│  QUEST  ▸  Co-op Spring/Summer 2027 · full-time from Jan 2028  │
│  STATUS ▸  ▶ OPEN TO WORK                                      │
└────────────────────────────────────────────────────────────────┘
```

---

## ▸ PROJECTS

### ◆ [Query Plan Lab](https://github.com/shravanibnikam/query-plan-lab) — what indexes actually cost

![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL_16-4f5560?style=flat-square&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-4f5560?style=flat-square&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-4f5560?style=flat-square&logo=docker&logoColor=white)
[![Tests](https://github.com/shravanibnikam/query-plan-lab/actions/workflows/tests.yml/badge.svg)](https://github.com/shravanibnikam/query-plan-lab/actions/workflows/tests.yml)

A reproducible benchmark of **eight index strategies against four query archetypes on a 10M-row table**, parsing `EXPLAIN (ANALYZE, BUFFERS)` into **160 timed measurements** with per-index build time and disk cost.

- **539 ms → 72 ms** on a filtered range query using a 10 MB partial index — **28% faster than a 404 MB covering index at 1/39th the storage.** Bigger index, slower query.
- **Adding GIN made its own target query 22% slower.** Reported deliberately, because a benchmark that only publishes its wins isn't a benchmark.
- **Reproduced a stale-statistics regression:** the planner estimated 1 row against 399,882 actual and picked a nested loop. `ANALYZE` restored the hash join and halved execution time.

### ◆ [Rhea](https://github.com/shravanibnikam/rhea-period-tracker) — local-first cycle tracker

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-b04c7b?style=flat-square&logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-b04c7b?style=flat-square&logo=supabase&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-b04c7b?style=flat-square&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-b04c7b?style=flat-square&logo=react&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-b04c7b?style=flat-square&logo=githubactions&logoColor=white)

**[▶ Live app](https://shravanibnikam.github.io/rhea-period-tracker/)** · A cycle tracker where the interesting problem is correctness across devices, not the UI.

- **PostgreSQL schema on Supabase across five row-level-security-scoped tables**, with four versioned migrations shipped to production.
- **Hybrid logical clock columns and a last-write-wins trigger** reconcile concurrent edits made on different devices.
- Cycle length, phase, and prediction windows are **computed entirely on-device** from one structured record per logged day; trends surface through Recharts.
- **260+ unit and integration tests**, with GitHub Actions running type checking, linting, tests, and builds on every push.

### ◆ [MergeLag](https://github.com/shravanibnikam/mergelag) — how long will this PR sit?

![Python](https://img.shields.io/badge/Python-e63d6a?style=flat-square&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-e63d6a?style=flat-square&logo=postgresql&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-e63d6a?style=flat-square&logo=githubactions&logoColor=white)
[![CI](https://github.com/shravanibnikam/mergelag/actions/workflows/ci.yml/badge.svg)](https://github.com/shravanibnikam/mergelag/actions/workflows/ci.yml)

`in progress` · A GitHub App that predicts how long open pull requests take to merge, flags the ones likely to stall, and posts a weekly digest of what is actually slowing the review queue down.

- Scope is the **full ML lifecycle**, not just a model: point-in-time feature pipeline, leakage tests, model registry, serving API, drift monitoring, and auto-retrain.
- Built around **machinery that stops it lying about its own accuracy** — every invariant guard ships with a permanent negative control proving it still catches a known-bad input.

### ◆ [Third Place Finder](https://github.com/shravanibnikam/Third-Place-Finder-Web) — cafés, libraries, coworking

![MySQL](https://img.shields.io/badge/MySQL-3c3c4f?style=flat-square&logo=mysql&logoColor=white)
![Node.js](https://img.shields.io/badge/Node%2FExpress-3c3c4f?style=flat-square&logo=nodedotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3c3c4f?style=flat-square&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-3c3c4f?style=flat-square&logo=react&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet-3c3c4f?style=flat-square&logo=leaflet&logoColor=white)

`being rebuilt` · A Seattle study-spot finder. v1 shipped and is now being rebuilt from scratch — new UI, new backend, new design.

- **MySQL schema** modelling users, venue attributes, and saved preferences.
- **Guest and authenticated sessions routed through a single write path**, so anonymous activity survived sign-up instead of being thrown away.
- Node/Express REST API and a React/TypeScript client rendering filtered venue results on a Leaflet map.

---

## ▸ SKILL TREE

<div align="center">

`⌨️ Languages` &nbsp; ![Python](https://img.shields.io/badge/Python-b04c7b?style=flat-square&logo=python&logoColor=white) ![SQL](https://img.shields.io/badge/SQL-b04c7b?style=flat-square&logo=postgresql&logoColor=white) ![TypeScript](https://img.shields.io/badge/TypeScript-b04c7b?style=flat-square&logo=typescript&logoColor=white) ![Java](https://img.shields.io/badge/Java-b04c7b?style=flat-square&logo=openjdk&logoColor=white) ![C/C++](https://img.shields.io/badge/C%2FC%2B%2B-b04c7b?style=flat-square&logo=cplusplus&logoColor=white) ![Node/Express](https://img.shields.io/badge/Node%2FExpress-b04c7b?style=flat-square&logo=nodedotjs&logoColor=white) ![React](https://img.shields.io/badge/React-b04c7b?style=flat-square&logo=react&logoColor=white)

`🗄️ Backend & DB` &nbsp; ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-e63d6a?style=flat-square&logo=postgresql&logoColor=white) ![MySQL](https://img.shields.io/badge/MySQL-e63d6a?style=flat-square&logo=mysql&logoColor=white) ![Schema Design](https://img.shields.io/badge/Schema_Design-e63d6a?style=flat-square&logoColor=white) ![Migrations](https://img.shields.io/badge/Versioned_Migrations-e63d6a?style=flat-square&logoColor=white) ![Query Opt.](https://img.shields.io/badge/Query_Optimization-e63d6a?style=flat-square&logoColor=white) ![EXPLAIN](https://img.shields.io/badge/EXPLAIN_Analysis-e63d6a?style=flat-square&logoColor=white) ![Indexing](https://img.shields.io/badge/Indexing_Strategy-e63d6a?style=flat-square&logoColor=white) ![REST](https://img.shields.io/badge/REST_API_Design-e63d6a?style=flat-square&logoColor=white) ![Concurrency](https://img.shields.io/badge/Concurrency_%26_Conflict_Resolution-e63d6a?style=flat-square&logoColor=white)

`☁️ Cloud & Infra` &nbsp; ![AWS](https://img.shields.io/badge/AWS-4f5560?style=flat-square&logoColor=white) ![GCP](https://img.shields.io/badge/Google_Cloud-4f5560?style=flat-square&logo=googlecloud&logoColor=white) ![Docker](https://img.shields.io/badge/Docker_%26_Compose-4f5560?style=flat-square&logo=docker&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-4f5560?style=flat-square&logo=githubactions&logoColor=white) ![Git](https://img.shields.io/badge/Git-4f5560?style=flat-square&logo=git&logoColor=white) ![Linux](https://img.shields.io/badge/Linux_%2F_CLI-4f5560?style=flat-square&logo=linux&logoColor=white) ![Supabase](https://img.shields.io/badge/Supabase-4f5560?style=flat-square&logo=supabase&logoColor=white)

`🧪 Testing & Data` &nbsp; ![Testing](https://img.shields.io/badge/Unit_%26_Integration_Tests-3c3c4f?style=flat-square&logoColor=white) ![Type Checking](https://img.shields.io/badge/Type_Checking-3c3c4f?style=flat-square&logoColor=white) ![Linting](https://img.shields.io/badge/Linting-3c3c4f?style=flat-square&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-3c3c4f?style=flat-square&logo=pandas&logoColor=white) ![NumPy](https://img.shields.io/badge/NumPy-3c3c4f?style=flat-square&logo=numpy&logoColor=white) ![spaCy](https://img.shields.io/badge/spaCy-3c3c4f?style=flat-square&logo=spacy&logoColor=white) ![TensorFlow](https://img.shields.io/badge/TensorFlow-3c3c4f?style=flat-square&logo=tensorflow&logoColor=white) ![Hugging Face](https://img.shields.io/badge/Hugging_Face-3c3c4f?style=flat-square&logo=huggingface&logoColor=white) ![Tableau](https://img.shields.io/badge/Tableau-3c3c4f?style=flat-square&logoColor=white) ![Power BI](https://img.shields.io/badge/Power_BI-3c3c4f?style=flat-square&logoColor=white)

</div>

---

## ▸ EXPERIENCE

### AI/ML Intern · CSRBOX with IBM SkillsBuild
`2024` · `remote`

- Built a **Python ingestion pipeline** to clean and restructure raw customer interaction records, resolving inconsistent and missing fields.
- Rebuilt classification and dialogue flows around **the intents that actually dominated traffic**, cutting average response time **30%**.
- Built **Power BI dashboards** surfacing interaction patterns and common failure points, and presented the findings to a non-technical team.

---

## ▸ RESEARCH

**Unified Sentiment Analysis of Customer Reviews** — published, *IRJMETS* Vol. 07, Issue 05

- Aspect-level sentiment pipeline over **7k+ customer reviews** in Python (Pandas, spaCy).
- Scored sentiment **per product attribute rather than per review**, using BERT-based classification.

---

## ▸ LEADERSHIP

**Google Developer Groups on Campus** — Cloud Computing Co-Lead · UI/UX & Marketing Lead
`Sep 2022 – Jun 2025` · `Pune, India`

- Designed and delivered hands-on **GCP workshops** (Compute Engine, Cloud Run, Cloud Storage, BigQuery, Firebase) to **200+ students across three years**, debugging live deployments mid-session.
- Split curriculum ownership with a fellow lead and coordinated a **12-person organizing team** across speakers, scheduling, materials, and day-of logistics for **7 events a year**.
- Onboarded and mentored **15 junior members** into session leads.

---

## ▸ EDUCATION

```
┌──────────────────────────────────────────────────────────────────┐
│  MS Computer Science · Northeastern University, Seattle          │
│  expected December 2027                                          │
│  ▸ Scalable Distributed Systems · DBMS · Algorithms              │
│  ▸ Cloud Computing · Programming Design Paradigms                │
├──────────────────────────────────────────────────────────────────┤
│  BS Artificial Intelligence & Data Science                       │
│  Savitribai Phule Pune University, Maharashtra, India            │
│  June 2025                                                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## ▸ STATS

<div align="center">

<img alt="Shravani's GitHub contribution graph" src="https://ghchart.rshah.org/b04c7b/shravanibnikam" width="96%" />
</div>

---

## ▸ CONTACT

<div align="center">

[![LinkedIn](https://img.shields.io/badge/LinkedIn-b04c7b?style=for-the-badge&logoColor=white)](https://www.linkedin.com/in/shravaninikam/)
[![Email](https://img.shields.io/badge/Email-e63d6a?style=for-the-badge&logo=gmail&logoColor=white)](mailto:shravanibnikam@gmail.com)

<img alt="Seattle, WA · backend · databases · ml · open to work" src="https://readme-typing-svg.demolab.com?font=Press+Start+2P&size=8&duration=99999&pause=99999&color=e63d6a&center=true&vCenter=true&width=800&height=18&lines=seattle%2C%20wa%20%C2%B7%20backend%20%C2%B7%20databases%20%C2%B7%20ml%20%C2%B7%20open%20to%20work" />

</div>
