export default function ConflictEditor({ value, onChange, disabled }) {
  return (
    <label className="field conflict-editor">
      <span className="field-label">Conflict block</span>
      <span className="field-hint">Paste the Git conflict markers and both code versions.</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={13}
        spellCheck="false"
        disabled={disabled}
        aria-label="Git conflict block"
      />
    </label>
  );
}
