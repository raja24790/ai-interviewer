import { useEffect, useMemo, useState } from 'react';
import Avatar from '../components/Avatar';
import AttentionMonitor from '../components/AttentionMonitor';
import AudioCapture from '../components/AudioCapture';
import ScorePanel from '../components/ScorePanel';

const QUESTION_TIME_SECONDS = 120;

type InterviewSession = {
  session_id: string;
  questions: string[];
  token: { access_token: string };
};

type FinalizeResponse = {
  session_id: string;
  pdf_url: string;
  summary: string;
  questions: {
    question: string;
    transcript: string;
    scores: any;
  }[];
};

export default function InterviewPage() {
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [qIndex, setQIndex] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [scores, setScores] = useState<any[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [avatarText, setAvatarText] = useState('Click Start to begin.');
  const [token, setToken] = useState<string | null>(null);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [report, setReport] = useState<FinalizeResponse | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);

  const apiBase = useMemo(
    () => (process.env.NEXT_PUBLIC_API_BASE ?? '').replace(/\/$/, ''),
    []
  );

  const progress = useMemo(() => {
    if (!session || session.questions.length === 0) return 0;
    return ((qIndex + 1) / session.questions.length) * 100;
  }, [qIndex, session]);

  const start = async () => {
    const res = await fetch(`${apiBase}/interview/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: 'general' }),
    });
    if (!res.ok) {
      setAvatarText('Unable to start interview. Please try again.');
      return;
    }
    const data = (await res.json()) as InterviewSession;
    setSession(data);
    setToken(data.token.access_token);
    setAvatarText(data.questions[0]);
    setQIndex(0);
    setTranscript('');
    setScores([]);
    setAnswers(new Array(data.questions.length).fill(''));
    setReport(null);
    setCountdown(QUESTION_TIME_SECONDS);
  };

  useEffect(() => {
    if (!session) return;
    setCountdown(QUESTION_TIME_SECONDS);
  }, [session?.session_id, qIndex]);

  useEffect(() => {
    if (countdown === null) return;
    if (countdown <= 0) return;
    const timer = window.setInterval(() => {
      setCountdown((prev) => {
        if (prev === null) return prev;
        if (prev <= 1) {
          window.clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => window.clearInterval(timer);
  }, [countdown]);

  useEffect(() => {
    if (!session) return;
    setAnswers((prev) => {
      const copy = [...prev];
      copy[qIndex] = transcript;
      return copy;
    });
  }, [transcript, qIndex, session]);

  useEffect(() => {
    if (!transcript) return;
    const words = transcript.split(' ').length;
    const s = {
      clarity: Math.min(5, Math.floor(words / 30) + 2),
      relevance: 3,
      structure: 3,
      conciseness: words < 200 ? 4 : 3,
      confidence: 3,
      commentary: undefined,
      total: 0,
    };
    s.total = s.clarity + s.relevance + s.structure + s.conciseness + s.confidence;
    setScores((prev) => {
      const copy = [...prev];
      copy[qIndex] = s;
      return copy;
    });
  }, [transcript, qIndex]);

  const finalize = async (updatedAnswers: string[]) => {
    if (!session || !token) return;
    setLoadingReport(true);
    setAvatarText('Thank you! Generating report...');
    const payload = {
      session_id: session.session_id,
      transcripts: session.questions.map((question, index) => ({
        question,
        transcript: updatedAnswers[index] ?? '',
      })),
      attention_summary: { focused_ratio: 0.82, distracted_ratio: 0.18 },
    };
    const res = await fetch(`${apiBase}/report/finalize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      setAvatarText('Unable to generate report. Please retry from dashboard.');
      setLoadingReport(false);
      return;
    }
    const data = (await res.json()) as FinalizeResponse;
    setReport(data);
    setScores(data.questions.map((q) => q.scores));
    setAvatarText('Report ready! Review insights on the right.');
    setLoadingReport(false);
  };

  const nextQ = () => {
    if (!session) return;
    const next = qIndex + 1;
    const updatedAnswers = [...answers];
    updatedAnswers[qIndex] = transcript;
    setAnswers(updatedAnswers);
    if (next < session.questions.length) {
      setQIndex(next);
      setAvatarText(session.questions[next]);
      setTranscript('');
    } else {
      finalize(updatedAnswers);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr 320px', gap: 16, padding: 16 }}>
      <div>
        <Avatar text={avatarText} sessionId={session?.session_id} questionIndex={qIndex} />
        {session && <AttentionMonitor sessionId={session.session_id} />}
      </div>
      <div>
        <h2>AI Interview</h2>
        {session && (
          <div style={{ margin: '12px 0', height: 8, background: '#e5e7eb', borderRadius: 999 }}>
            <div
              style={{
                width: `${progress}%`,
                height: '100%',
                borderRadius: 999,
                transition: 'width 0.4s ease',
                background: 'linear-gradient(135deg, #34d399, #059669)',
              }}
            />
          </div>
        )}
        {session && (
          <p style={{ margin: '4px 0', fontSize: 12, color: '#6b7280' }}>
            {session.questions.length > 0
              ? `Question ${qIndex + 1} of ${session.questions.length}`
              : 'Preparing questions...'}
            {countdown !== null && (
              <span style={{ marginLeft: 8 }}>
                ⏱ {countdown}s remaining
              </span>
            )}
          </p>
        )}
        {!session ? (
          <button onClick={start}>Start</button>
        ) : (
          <button onClick={nextQ} disabled={loadingReport}>
            {qIndex + 1 < session.questions.length ? 'Next Question' : 'Finish Interview'}
          </button>
        )}
        <AudioCapture
          sessionId={session?.session_id}
          questionIndex={qIndex}
          authToken={token ?? undefined}
          onTranscript={setTranscript}
        />
        <div style={{ whiteSpace: 'pre-wrap', marginTop: 8 }}>{transcript}</div>
        {report && (
          <div style={{ marginTop: 24, padding: 16, border: '1px solid #e5e7eb', borderRadius: 12 }}>
            <h3 style={{ marginTop: 0 }}>Final Summary</h3>
            <p style={{ fontSize: 14, color: '#374151' }}>{report.summary}</p>
            <a
              href={`${apiBase}${report.pdf_url}`}
              target="_blank"
              rel="noreferrer"
              style={{ color: '#2563eb', fontWeight: 500 }}
            >
              Download PDF Report
            </a>
          </div>
        )}
      </div>
      <div>
        <ScorePanel scores={scores} />
      </div>
    </div>
  );
}
