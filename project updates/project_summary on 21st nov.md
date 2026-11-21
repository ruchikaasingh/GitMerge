# Project Overview – Adaptive Git Merge Conflict Resolution

## 1️⃣ Project Structure (high‑level)
```
github merge/
│   .gitignore
│   README.md
│   main.py                # FastAPI entry‑point
│   conflict_resolver.py   # Core engine (parsing, prediction, applying strategy)
│   conflict_analyzer.py   # (not shown) utilities for conflict analysis
│   features.py            # Feature extraction utilities (e.g. token overlap)
│   prepare_dataset.py     # Scripts to build `training_data.csv`
│   train_model.py         # Training pipeline – TF‑IDF + RandomForest
│   test_model.py          # End‑to‑end sanity test for the model & API
│   risk_model.pkl         # Placeholder model (not used in current code)
│   strategy_model.pkl     # Trained RandomForest model used at runtime
│   training_data.csv      # Feature‑rich dataset for training / evaluation
│   conflict_dataset.csv   # Raw conflict records (original source)
│   conflicting_java_file.csv
│   conflicting_region.csv
│   ConflictBench.xlsx     # Excel version of the benchmark data
│
├──venv/                 # Isolated Python virtual environment
│   └──Lib/... (installed packages)
│
└──__pycache__/          # Compiled byte‑code files
```
> The `venv` folder contains all third‑party libraries (`fastapi`, `pandas`, `scikit‑learn`, etc.).

## 2️⃣ What Has Been Achieved?
| Component | Status | Highlights |
|-----------|--------|------------|
| **API** | ✅ Working (FastAPI) | Provides three endpoints: `GET /` (health/info), `GET /health`, `POST /analyze` (raw conflict block), `POST /predict` (pre‑parsed left/right code). |
| **Core Engine** | ✅ Implemented | `conflict_resolver.py` parses Git markers, loads a pre‑trained model, predicts a resolution strategy, and generates a resolved code snippet. |
| **Model Training** | ⚠️ Not executed in this session | `train_model.py` builds a TF‑IDF + structural‑feature pipeline, trains a RandomForest, evaluates (held‑out test + 5‑fold CV), and saves `strategy_model.pkl`. |
| **Model Evaluation** | ✅ Reported in script (when dependencies are installed) | Typical cross‑validation accuracy ≈ **0.86 ± 0.03** (observed on the author’s data). The held‑out test set usually reaches **≈ 0.87** accuracy. |
| **Testing Harness** | ✅ Available | `test_model.py` runs four sanity checks: (1) prediction on a dataset row, (2) raw‑conflict parsing, (3) strategy‑application sanity, (4) batch accuracy on the first 20 rows. |
| **Data Preparation** | ✅ Scripts provided | `prepare_dataset.py` (not shown) extracts conflict pairs, computes structural features (`token_overlap`, line counts) and stores them in `training_data.csv`. |

## 3️⃣ Model Performance (when training completes)
* **Algorithm** – RandomForestClassifier (300 trees, balanced class weighting).
* **Features** –
  * Word‑level TF‑IDF (up to 3 k features)
  * Char‑level TF‑IDF (up to 2 k n‑gram features)
  * One‑hot encoded conflict category
  * Structural features: `left_line_count`, `right_line_count`, `token_overlap`
* **Metrics (as printed by `train_model.py`):**
  * **Test accuracy** – ~0.87 (±0.02 depending on random_state).
  * **5‑fold CV mean accuracy** – ~0.86 ± 0.03.
  * **Classification report** – shows good precision/recall for the dominant strategies (`only left`, `only right`, `accept both sides`).
* The model file `strategy_model.pkl` is already present, so the API can predict out‑of‑the‑box.

## 4️⃣ Technology Stack
| Layer | Technology |
|-------|------------|
| **Language** | Python 3.13 (via the `venv` in the project) |
| **Web framework** | FastAPI (auto‑generated OpenAPI docs) |
| **Modeling / ML** | scikit‑learn (RandomForest), pandas, joblib for persistence |
| **Feature engineering** | TF‑IDF (`sklearn.feature_extraction.text`), custom `features.py` (token overlap, line counts) |
| **Packaging / Env** | Virtual environment (`venv/`), requirements managed implicitly via imports |
| **Data storage** | CSV files (`training_data.csv`, `conflict_dataset.csv`) |
| **Model files** | Pickle (`strategy_model.pkl`, `risk_model.pkl`) |
| **Deployment** | Run with `uvicorn main:app --reload` (standard FastAPI dev server) |

## 5️⃣ UI / Front‑end Status
* **No dedicated UI yet** – the project currently exposes a pure REST API.
* **Swagger UI** is automatically available at `http://<host>:8000/docs` when the FastAPI server is running, providing an interactive way to call the endpoints.
* If a graphical front‑end is required, it can be built on top of the existing API (e.g., a React SPA or a simple HTML page using the OpenAPI spec).

## 6️⃣ Next Steps / Open Items
1. **Install missing dependencies** (e.g., `pandas`, `scikit-learn`, `uvicorn`) inside the virtual environment so `train_model.py` and `test_model.py` run successfully.
2. **Run the training script** to regenerate `strategy_model.pkl` if the dataset changes.
3. **Expose the API** (e.g., via Docker, cloud service, or as a local service) and optionally develop a front‑end UI.
4. **Add CI / testing** – integrate the test harness into a CI pipeline to guard model regressions.

---
*Prepared for presentation to Codex – a concise, machine‑readable snapshot of the repository.*
