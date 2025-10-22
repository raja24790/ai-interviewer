import { CSSProperties, useEffect, useMemo, useState } from 'react';

type AvatarProps = {
  text: string;
  sessionId?: string;
  questionIndex?: number;
};

const containerStyle: CSSProperties = {
  border: '1px solid #ddd',
  borderRadius: 12,
  padding: 16,
  background: '#fff',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: 16,
  textAlign: 'center',
};

const bubbleStyle: CSSProperties = {
  width: 96,
  height: 96,
  borderRadius: '50%',
  background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: '#fff',
  fontSize: 32,
  fontWeight: 600,
  boxShadow: '0 8px 16px rgba(79, 70, 229, 0.25)',
};

export default function Avatar({ text, sessionId, questionIndex }: AvatarProps) {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const baseApi = useMemo(
    () => (process.env.NEXT_PUBLIC_API_BASE ?? '').replace(/\/$/, ''),
    []
  );

  useEffect(() => {
    if (!sessionId || questionIndex === undefined) {
      setVideoUrl(null);
      return;
    }
    const controller = new AbortController();
    const prefix = baseApi || '';
    const url = `${prefix}/avatar/${sessionId}/q${String(questionIndex).padStart(2, '0')}.mp4`;
    fetch(url, { method: 'HEAD', signal: controller.signal })
      .then((res) => {
        if (res.ok) {
          setVideoUrl(url);
        } else {
          setVideoUrl(null);
        }
      })
      .catch(() => setVideoUrl(null));
    return () => controller.abort();
  }, [baseApi, sessionId, questionIndex]);

  return (
    <div style={containerStyle}>
      {videoUrl ? (
        <video
          key={videoUrl}
          src={videoUrl}
          autoPlay
          loop
          muted
          playsInline
          style={{ width: '100%', borderRadius: 12 }}
        />
      ) : (
        <div style={bubbleStyle}>AI</div>
      )}
      <p style={{ margin: 0, color: '#333', fontSize: 14 }}>{text}</p>
    </div>
  );
}
