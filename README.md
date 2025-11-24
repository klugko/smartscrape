# SmartScrape

SmartScrape est un backend de **prospection B2B** qui :

- Crawle des sites web à partir d’URLs.
- Identifie les entreprises pertinentes pour du **dev / data / IA**.
- Extrait des **contacts** (emails, téléphones, LinkedIn).
- Utilise un **LLM (OpenAI)** pour enrichir le profil et scorer les prospects.
- Expose une API pour rechercher, filtrer et paginer les résultats.

---

## Stack technique

- Python 3.11+
- FastAPI
- PostgreSQL (SQLAlchemy 2)
- Redis + RQ (workers de scraping)
- httpx + BeautifulSoup + lxml
- OpenAI (chat completions, JSON mode)

---


## Prérequis

* Python 3.11
* PostgreSQL (local)
* Redis (local)
* Une clé API OpenAI valide (`OPENAI_API_KEY`).

---

## Configuration

Créer un fichier `backend/.env` :

```env
# Backend
APP_ENV=dev
APP_PORT=8000

# Postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=smartscrape_v2
POSTGRES_USER=postgres
POSTGRES_PASSWORD=abcd

# Redis
REDIS_URL=redis://localhost:6379/0

# Scraping
SCRAPER_USER_AGENT=SmartScrapeBot/0.1
SCRAPER_MAX_DEPTH=2
SCRAPER_REQUEST_DELAY_SECONDS=1.0
SCRAPER_REQUEST_TIMEOUT_SECONDS=15.0
SCRAPER_MAX_PAGES_PER_DOMAIN=60

# OpenAI / LLM
OPENAI_API_KEY=sk-xxxx                      
OPENAI_MODEL=gpt-4.1-mini
OPENAI_ENABLE=1
OPENAI_MAX_TOKENS=2000
LLM_MAX_CHARS=20000
```

Créer la base de données PostgreSQL correspondante :

```sql
CREATE DATABASE smartscrape_v2;
CREATE USER postgres WITH PASSWORD 'mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE smartscrape_v2 TO postgres;
```

(Adapte `POSTGRES_USER` / `POSTGRES_PASSWORD` à ta conf locale.)

---

## Installation & lancement (local, sans Docker)

Depuis la racine du repo :

```bash
cd backend

# 1. Créer et activer un venv
python -m venv venv
source venv/bin/activate

# 2. Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# 3. (Optionnel) Forcer la création des tables
python -c "from app.db.session import engine; from app.db.base import Base; Base.metadata.create_all(bind=engine)"
```

### Lancer l’API FastAPI

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* Swagger UI : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* OpenAPI JSON : [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

### Lancer le worker RQ

Dans un **autre terminal** :

```bash
cd backend
source venv/bin/activate
python -m app.workers.worker
```

Le worker consomme la queue `url_scan` et exécute les jobs de crawling + enrichissement IA.

---

## Principaux endpoints

### 1. Lancer un scan d’URLs

**POST** `/api/jobs/scan-urls`

Payload :

```json
{
  "urls": [
    "https://www.example.com",
    "https://www.octo.com"
  ]
}
```

Réponse : liste de jobs créés (id, status, timestamps…).

### 2. Suivre un job

**GET** `/api/jobs/{job_id}`

Exemple :

```bash
curl "http://127.0.0.1:8000/api/jobs/1"
```

Status possibles : `pending`, `running`, `done`, `error`.

---

### 3. Recherche entreprise + contacts + leads (endpoint principal)

**GET** `/api/company-contacts/search`

Query params :

* `q` : recherche texte (nom, description, tags, site, contacts…)
* `country`, `city`, `industry`
* `prospect_type` : `project|staffing|both|unknown`
* `min_score` : score minimum (0–100, calculé par le LLM ou l’heuristique)
* `status` : statut de prospection (`to_contact`, `in_progress`, `won`, `lost`, etc.)
* `page` (1-based), `page_size` (<= 200)

Exemple :

```bash
curl "http://127.0.0.1:8000/api/company-contacts/search?q=octo&min_score=30&page=1&page_size=20"
```

Réponse :

```json
{
  "total": 3,
  "items": [
    {
      "company": { ... },
      "contacts": [ ... ],
      "leads": [ ... ]
    }
  ]
}
```

---

### 4. Endpoints de base

* **GET** `/api/companies`
  Filtre simple sur `country`, `prospect_type`, `min_score`, `status`, `limit`, `offset`.

* **GET** `/api/contacts`
  Filtre sur `company_id`, `email_contains`, `limit`, `offset`.

* **GET** `/api/leads`
  Liste les entrées de prospection (`ProspectionMeta`).

* **PATCH** `/api/leads/{lead_id}`
  Mise à jour du statut de prospection.

Exemple :

```bash
curl -X PATCH "http://127.0.0.1:8000/api/leads/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "owner": "jean.aime",
    "notes": "Premier email envoyé"
  }'
```

---

## Notes

* Le crawler respecte **robots.txt** autant que possible et limite la profondeur / le nombre de pages par domaine.
* L’enrichissement IA (score, type de prospect, tags, localisation…) dépend de la qualité du contenu public du site.
* L’API ne fait **pas** d’envoi d’emails : elle s’intègre avec tes outils de séquences/CRM pour la partie outreach.

