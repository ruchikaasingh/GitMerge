# PR Conflict Review Workbench

A beginner-friendly research prototype for reviewing Git merge-conflict suggestions. It uses React and JavaScript for the UI, FastAPI for the API/model, and MySQL for saved reviewer decisions.

The current demo analyzes a conflict pasted into the UI. It does **not** connect to GitHub or write commits yet. The GitHub App and PR-branch update flow will be implemented separately after this local workflow is in place.

## Folder layout

```text
.
├── frontend/                   # React + Vite interface
│   ├── src/
│   │   ├── components/         # Conflict editor and review history
│   │   ├── services/           # Calls to the FastAPI endpoints
│   │   ├── App.jsx
│   │   └── styles.css
│   ├── package.json
│   └── package-lock.json
├── backend/                    # SQLAlchemy models and Alembic migration
│   └── alembic/versions/
├── database/setup.sql          # One-time local MySQL database/user setup
├── main.py                     # FastAPI application
├── conflict_resolver.py        # Existing ML prediction and candidate logic
├── train_model.py              # Existing training script
├── training_data.csv           # Training data for the existing model
├── requirements.txt
└── .env.example
```

## Set up the demo on your computer

### 1. Install prerequisites

- Python 3.13
- Node.js 20.19+ (Node 24 LTS is suitable)
- MySQL Server 8.4

### 2. Create the local MySQL database

Open [database/setup.sql](database/setup.sql) in MySQL Workbench while connected as an administrator, then run it. It creates a local development database and app user. The example password is only for a local demo; change it before using this outside your own computer, and update `DATABASE_URL` accordingly.

### 3. Configure the backend

From the repository root in PowerShell:

```powershell
Copy-Item .env.example .env
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python train_model.py
alembic upgrade head
uvicorn main:app --reload
```

The training command creates the local `strategy_model.pkl` from the tracked CSV. The database migration creates the review-history table.

### 4. Start the frontend

Open a second PowerShell window:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. The UI calls FastAPI at <http://localhost:8000> by default. API health is available at <http://localhost:8000/health>, and interactive API documentation is at <http://localhost:8000/docs>.

Paste a conflict block, analyze it, review the candidate, choose a strategy, and save your decision. MySQL stores the strategy and optional repository/PR/file references; it does not store the pasted source code.

Stop each server with `Ctrl+C` when finished. The local MySQL service remains installed and can be stopped using Windows Services or MySQL Workbench.

## Database notes

There was no SQLite database or SQLite integration in the existing project, so there were no records to migrate. MySQL is being added as the first persistent store. Alembic manages its schema. The initial `conflict_reviews` table stores review decisions and references, not GitHub credentials or source code.

The connection pool checks connections before reuse. Review history is indexed by repository, PR number, and creation time. Actual PR locking is not needed yet because GitHub webhooks and concurrent PR jobs are not implemented. Before adding those, we should add a merge-job table with a unique repository/PR/head-SHA key and use a row lock while processing each job.

## API endpoints

- `GET /health` — API and optional database status.
- `POST /analyze` — parse a raw Git conflict block and get the existing model suggestion.
- `POST /predict` — predict from already separated left and right code.
- `GET /api/reviews` — list the latest 50 saved decisions (requires MySQL).
- `POST /api/reviews` — save a reviewer decision (requires MySQL).

## Next implementation stages

1. Add an isolated GitHub integration module for app installation and read-only PR access.
2. Fetch the PR branches in a temporary Git worktree and extract the real conflicting hunks.
3. Show a complete patch preview and apply only reviewer-approved resolutions.
4. Add an explicit, guarded commit to the PR source branch and handle updated heads, permissions, branch protections, and repository checks.
5. Add webhook handling and per-PR database locks when concurrent processing is introduced.
6. Revisit the ML model only after the UI-to-API flow is working and can be evaluated.

## Local-only security note

This demo does not include user authentication. Keep the API and MySQL on your own machine while developing, and do not expose them to a public network.
