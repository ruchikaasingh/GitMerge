import { useCallback, useEffect, useMemo, useState } from "react";
import ConflictEditor from "./components/ConflictEditor.jsx";
import ReviewHistory from "./components/ReviewHistory.jsx";
import { api } from "./services/api.js";

const SAMPLE_CONFLICT = `<<<<<<< HEAD
public int available(int sku) {
    return stock.get(sku);
}
=======
public Optional<Integer> available(int sku) {
    return Optional.ofNullable(stock.get(sku));
}
>>>>>>> feature/inventory`;

const STRATEGIES = ["only left", "only right", "accept both sides", "other"];

function makeCandidate(strategy, leftCode, rightCode) {
  if (strategy === "only left") return leftCode;
  if (strategy === "only right") return rightCode;
  if (strategy === "accept both sides") return `${leftCode}\n\n${rightCode}`;
  return "Manual resolution required. The model did not produce a merge candidate for this strategy.";
}

function App() {
  const [conflictText, setConflictText] = useState(SAMPLE_CONFLICT);
  const [repository, setRepository] = useState("");
  const [prNumber, setPrNumber] = useState("");
  const [filePath, setFilePath] = useState("");
  const [result, setResult] = useState(null);
  const [selectedStrategy, setSelectedStrategy] = useState("");
  const [reviews, setReviews] = useState([]);
  const [apiState, setApiState] = useState({ loading: true, connected: false, database: "unknown" });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const databaseAvailable = apiState.database === "connected";
  const candidate = useMemo(() => {
    if (!result || !selectedStrategy) return "";
    return makeCandidate(selectedStrategy, result.left_code, result.right_code);
  }, [result, selectedStrategy]);

  const refreshReviews = useCallback(async () => {
    try {
      setReviews(await api.listReviews());
    } catch {
      setReviews([]);
    }
  }, []);

  useEffect(() => {
    let active = true;
    api.health()
      .then((health) => {
        if (!active) return;
        setApiState({ loading: false, connected: true, database: health.database || "unknown" });
        if (health.database === "connected") refreshReviews();
      })
      .catch(() => {
        if (active) setApiState({ loading: false, connected: false, database: "unknown" });
      });
    return () => { active = false; };
  }, [refreshReviews]);

  async function analyzeConflict(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    setResult(null);
    try {
      const analysis = await api.analyzeConflict(conflictText);
      setResult(analysis);
      setSelectedStrategy(analysis.predicted_strategy || "other");
      setMessage("Suggestion ready. Review both sides before saving a decision.");
    } catch (requestError) {
      setError(requestError.message || "Could not analyze this conflict.");
    } finally {
      setBusy(false);
    }
  }

  async function saveDecision() {
    if (!result || !selectedStrategy) return;
    setBusy(true);
    setError("");
    setMessage("");
    const status = selectedStrategy === "other"
      ? "deferred"
      : selectedStrategy === result.predicted_strategy ? "accepted" : "edited";
    try {
      await api.saveReview({
        repository_full_name: repository.trim() || null,
        pr_number: prNumber ? Number(prNumber) : null,
        file_path: filePath.trim() || null,
        predicted_strategy: result.predicted_strategy || "unknown",
        selected_strategy: selectedStrategy,
        review_status: status,
      });
      setMessage("Decision saved to MySQL. No GitHub branch was changed.");
      await refreshReviews();
    } catch (requestError) {
      setError(requestError.message || "Could not save the decision. Check the MySQL connection.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#workbench" aria-label="Merge Review Workbench home">
          <span className="brand-mark" aria-hidden="true">M</span>
          <span>Merge Review Workbench</span>
        </a>
        <div className="topbar-status" aria-live="polite">
          <span className={`status-dot ${apiState.connected ? "is-online" : "is-offline"}`} />
          {apiState.loading ? "Connecting to API…" : apiState.connected ? "API connected" : "API unavailable"}
          <span className="status-divider">·</span>
          {databaseAvailable ? "MySQL connected" : "MySQL not connected"}
        </div>
      </header>

      <main className="main-content" id="workbench">
        <section className="intro-row">
          <div>
            <p className="eyebrow">Pull request conflict review</p>
            <h1>Review a merge suggestion</h1>
            <p className="intro-copy">Analyze a conflict, compare the proposed strategies, and record your choice.</p>
          </div>
          <span className="phase-badge">Local demo · GitHub write-back not connected</span>
        </section>

        <section className="notice" aria-label="Demo limitation">
          <span className="notice-icon" aria-hidden="true">i</span>
          <p>This demo analyzes pasted conflict blocks. It does not fetch a pull request or write commits to GitHub. Every candidate needs human review.</p>
        </section>

        <div className="workbench-grid">
          <form className="surface input-panel" onSubmit={analyzeConflict}>
            <div className="section-heading">
              <div>
                <p className="eyebrow">Step 1</p>
                <h2>Conflict input</h2>
              </div>
              <button className="button button-quiet" type="button" onClick={() => setConflictText(SAMPLE_CONFLICT)}>
                Load example
              </button>
            </div>

            <div className="field-grid">
              <label className="field">
                <span className="field-label">Repository (optional reference)</span>
                <input value={repository} onChange={(event) => setRepository(event.target.value)} placeholder="owner/repository" />
              </label>
              <label className="field">
                <span className="field-label">PR number</span>
                <input type="number" min="1" value={prNumber} onChange={(event) => setPrNumber(event.target.value)} placeholder="e.g. 42" />
              </label>
            </div>
            <label className="field file-field">
              <span className="field-label">File path (optional)</span>
              <input value={filePath} onChange={(event) => setFilePath(event.target.value)} placeholder="src/InventoryService.java" />
            </label>
            <ConflictEditor value={conflictText} onChange={setConflictText} disabled={busy} />
            <div className="form-footer">
              <span className="field-hint">The model and UI run locally; source code is not saved in MySQL.</span>
              <button className="button button-primary" type="submit" disabled={busy || !apiState.connected}>
                {busy ? "Working…" : "Analyze conflict"}
              </button>
            </div>
          </form>

          <section className="surface result-panel" aria-labelledby="result-title" aria-live="polite">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Step 2</p>
                <h2 id="result-title">Suggestion and review</h2>
              </div>
              {result && <span className="review-badge">Human review required</span>}
            </div>

            {!result ? (
              <div className="result-empty">
                <div className="empty-symbol" aria-hidden="true">⇄</div>
                <strong>Your candidate will appear here</strong>
                <span>Analyze a conflict to compare the two sides and the model’s suggestion.</span>
              </div>
            ) : (
              <>
                <div className="suggestion-summary">
                  <div>
                    <span className="field-hint">Model suggestion</span>
                    <strong>{result.predicted_strategy || "Needs manual review"}</strong>
                  </div>
                  <div className="confidence-box">
                    <span className="field-hint">Model score · uncalibrated</span>
                    <strong>{Math.round((result.confidence || 0) * 100)}%</strong>
                  </div>
                </div>

                <div className="strategy-picker">
                  <span className="field-label">Choose the strategy to preview</span>
                  <div className="strategy-options" role="group" aria-label="Resolution strategy">
                    {STRATEGIES.map((strategy) => (
                      <button
                        className={`strategy-button ${selectedStrategy === strategy ? "is-selected" : ""}`}
                        type="button"
                        key={strategy}
                        aria-pressed={selectedStrategy === strategy}
                        onClick={() => setSelectedStrategy(strategy)}
                      >
                        {strategy === "only left" ? "Keep base" : strategy === "only right" ? "Keep incoming" : strategy === "accept both sides" ? "Combine" : "Manual"}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="diff-grid">
                  <div className="code-pane">
                    <div className="code-pane-title"><span>Base / left</span><span>HEAD</span></div>
                    <pre>{result.left_code || "(empty side)"}</pre>
                  </div>
                  <div className="code-pane">
                    <div className="code-pane-title"><span>Incoming / right</span><span>PR branch</span></div>
                    <pre>{result.right_code || "(empty side)"}</pre>
                  </div>
                </div>

                <div className="candidate-pane">
                  <div className="code-pane-title"><span>Candidate preview</span><span>Not applied</span></div>
                  <pre>{candidate}</pre>
                </div>

                <button className="button button-primary save-button" type="button" onClick={saveDecision} disabled={busy || !databaseAvailable}>
                  {busy ? "Saving…" : "Save review decision"}
                </button>
                {!databaseAvailable && <p className="field-hint save-hint">Start the MySQL service to save decisions. Analysis remains available.</p>}
              </>
            )}
            {message && <p className="feedback success-feedback" role="status">{message}</p>}
            {error && <p className="feedback error-feedback" role="alert">{error}</p>}
          </section>
        </div>

        <ReviewHistory reviews={reviews} databaseAvailable={databaseAvailable} onRefresh={refreshReviews} />
      </main>
      <footer className="footer">Merge Review Workbench <span>·</span> suggestion only, reviewer decides</footer>
    </div>
  );
}

export default App;
