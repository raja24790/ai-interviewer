export default function ScorePanel({ scores }: { scores: any[] }) {
  return (
    <div style={{ padding: 12, border: '1px solid #eee', borderRadius: 8 }}>
      <h4>Live Scores</h4>
      {scores.map((s, i) => (
        <div key={i} style={{ fontSize: 14, marginBottom: 10 }}>
          <div>
            Q{i + 1}: total {s.total} / 25 — clarity {s.clarity} | relevance {s.relevance} | structure {s.structure} |
            conciseness {s.conciseness} | confidence {s.confidence}
          </div>
          {s.commentary && (
            <div style={{ fontSize: 12, color: '#4b5563', marginTop: 2 }}>{s.commentary}</div>
          )}
        </div>
      ))}
    </div>
  );
}
