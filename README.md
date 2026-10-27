# YA DOK

AI-powered clinical simulation platform for medical students.
Educational use only - it never diagnoses real patients.

## Project layout

| Folder         | What it is                              | Tech             | Deployed to |
|----------------|-----------------------------------------|------------------|-------------|
| `backend/`     | API + business logic + AI layer         | Python / FastAPI | Railway     |
| `frontend/`    | Web app (UI)                            | Next.js / TS     | Vercel      |
| `avatar-unity/`| Virtual patient avatar (optional, last) | Unity / C#       | WebGL build inside `frontend/public/avatar/` |
| `data/`        | Case preparation (before DB ingestion)  | Python scripts   | -           |
| `docs/`        | Documentation                           | Markdown         | -           |

Database, auth and file storage live on **Supabase** (not in this repo).

## Quick start

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate     Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env             # then fill in the values
uvicorn app.main:app --reload
```
Open http://localhost:8000/docs and http://localhost:8000/api/health

### Frontend
```bash
cd frontend
npx create-next-app@latest . --typescript   # first time only
npm run dev
```

## Git workflow
- `main`    : stable, protected (PR + 1 review required)
- `develop` : integration branch
- `feature/<name>` : one branch per feature, open a PR into `develop`
