import { useEffect, useMemo, useState } from 'react';

type AttentionSnapshot = {
  state: 'focused' | 'distracted' | 'unknown';
  score?: number;
  last_event?: string;
};

type AttentionMonitorProps = {
  sessionId: string;
  pollIntervalMs?: number;
};

const STATUS_COLORS: Record<AttentionSnapshot['state'], string> = {
  focused: '#10b981',
  distracted: '#f97316',
  unknown: '#9ca3af',
};

export default function AttentionMonitor({
  sessionId,
  pollIntervalMs = 5000,
}: AttentionMonitorProps) {
  const [snapshot, setSnapshot] = useState<AttentionSnapshot>({
    state: 'unknown',
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (!sessionId) return undefined;

    const fetchSnapshot = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE}/interview/${sessionId}/attention`
        );
        if (!res.ok) {
          throw new Error(`Failed to fetch attention: ${res.status}`);
        }
        const data = (await res.json()) as AttentionSnapshot;
        if (!active) return;
        setSnapshot({
          state: data.state ?? 'unknown',
          score: data.score,
          last_event: data.last_event,
        });
        setError(null);
      } catch (err) {
        if (!active) return;
        setError('Unable to update attention status');
      }
    };

    fetchSnapshot();
    const timer = setInterval(fetchSnapshot, pollIntervalMs);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [sessionId, pollIntervalMs]);

  const statusLabel = useMemo(() => {
    switch (snapshot.state) {
      case 'focused':
        return 'Looks focused';
      case 'distracted':
        return 'Possible distraction detected';
      default:
        return 'Waiting for signal';
    }
  }, [snapshot.state]);

  return (
    <div
      style={{
        marginTop: 16,
        border: '1px solid #e5e7eb',
        borderRadius: 8,
        padding: 16,
        background: '#f9fafb',
      }}
    >
      <h4 style={{ margin: '0 0 8px' }}>Attention Monitor</h4>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span
          style={{
            width: 12,
            height: 12,
            borderRadius: '50%',
            background: STATUS_COLORS[snapshot.state],
            display: 'inline-block',
          }}
        />
        <span style={{ fontSize: 14, color: '#111827' }}>{statusLabel}</span>
      </div>
      {typeof snapshot.score === 'number' && (
        <p style={{ margin: '8px 0 0', fontSize: 12, color: '#4b5563' }}>
          Attention score: {Math.round(snapshot.score * 100)}%
        </p>
      )}
      {snapshot.last_event && (
        <p style={{ margin: '4px 0 0', fontSize: 12, color: '#6b7280' }}>
          Last event: {snapshot.last_event}
        </p>
      )}
      {error && (
        <p style={{ margin: '8px 0 0', fontSize: 12, color: '#ef4444' }}>{error}</p>
      )}
    </div>
  );
}
