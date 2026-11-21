function shortDate(value) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export default function ReviewHistory({ reviews, databaseAvailable, onRefresh }) {
  return (
    <section className="surface history-section" aria-labelledby="history-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Saved decisions</p>
          <h2 id="history-title">Recent review history</h2>
        </div>
        <button className="button button-quiet" type="button" onClick={onRefresh} disabled={!databaseAvailable}>
          Refresh
        </button>
      </div>
      {!databaseAvailable ? (
        <p className="empty-state">Start MySQL with the demo setup to save and view review history.</p>
      ) : reviews.length === 0 ? (
        <p className="empty-state">No saved decisions yet.</p>
      ) : (
        <div className="history-list">
          {reviews.map((review) => (
            <article className="history-row" key={review.id}>
              <div className="history-main">
                <strong>{review.repository_full_name || "Pasted conflict"}{review.pr_number ? ` · PR #${review.pr_number}` : ""}</strong>
                <span>{review.file_path || "File not specified"}</span>
              </div>
              <div className="history-meta">
                <span>{review.selected_strategy}</span>
                <small>{shortDate(review.created_at)}</small>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
