const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof body.detail === "string" ? body.detail : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return body;
}

export const api = {
  health: () => request("/health"),
  analyzeConflict: (conflictText) => request("/analyze", {
    method: "POST",
    body: JSON.stringify({ conflict_text: conflictText, conflict_category: "unknown" }),
  }),
  listReviews: () => request("/api/reviews"),
  saveReview: (review) => request("/api/reviews", {
    method: "POST",
    body: JSON.stringify(review),
  }),
};
