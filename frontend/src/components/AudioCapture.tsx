import { useCallback, useEffect, useRef, useState } from 'react';

type AudioCaptureProps = {
  sessionId?: string;
  questionIndex?: number;
  authToken?: string;
  onTranscript?: (transcript: string) => void;
};

export default function AudioCapture({
  sessionId,
  questionIndex = 0,
  authToken,
  onTranscript,
}: AudioCaptureProps) {
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const finalTranscriptRef = useRef('');
  const [listening, setListening] = useState(false);
  const [supportError, setSupportError] = useState<string | null>(null);

  const stopRecognition = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
  }, []);

  const handleResult = useCallback(
    (event: SpeechRecognitionEvent) => {
      let interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        const text = result[0]?.transcript?.trim();
        if (!text) continue;
        if (result.isFinal) {
          finalTranscriptRef.current = (
            finalTranscriptRef.current
              ? `${finalTranscriptRef.current} ${text}`
              : text
          ).trim();
          if (sessionId && authToken) {
            const base = (process.env.NEXT_PUBLIC_API_BASE ?? '').replace(/\/$/, '');
            const endpoint = `${base || ''}/stt/append`;
            fetch(endpoint, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${authToken}`,
              },
              body: JSON.stringify({
                session_id: sessionId,
                text,
                question_index: questionIndex,
              }),
            }).catch(() => {
              // ignore streaming errors but keep UI responsive
            });
          }
        } else {
          interimTranscript = `${interimTranscript} ${text}`.trim();
        }
      }

      const combined = (
        finalTranscriptRef.current + (interimTranscript ? ` ${interimTranscript}` : '')
      ).trim();
      onTranscript?.(combined);
    },
    [authToken, onTranscript, questionIndex, sessionId]
  );

  const startRecognition = useCallback(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSupportError('Speech recognition is not supported in this browser.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = handleResult;
    recognition.onerror = (event) => {
      if (event.error === 'not-allowed') {
        setSupportError('Microphone permission was denied.');
      } else {
        setSupportError('Speech recognition error occurred.');
      }
      stopRecognition();
    };
    recognition.onend = () => {
      setListening(false);
    };

    finalTranscriptRef.current = '';
    setSupportError(null);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }, [handleResult, stopRecognition]);

  useEffect(() => () => stopRecognition(), [stopRecognition]);
  useEffect(() => {
    finalTranscriptRef.current = '';
  }, [questionIndex, sessionId]);

  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          type="button"
          onClick={listening ? stopRecognition : startRecognition}
        >
          {listening ? 'Stop Recording' : 'Start Recording'}
        </button>
        {sessionId && (
          <span style={{ fontSize: 12, color: '#6b7280', alignSelf: 'center' }}>
            Session: {sessionId.slice(0, 8)}
          </span>
        )}
      </div>
      {supportError && (
        <p style={{ marginTop: 8, color: '#dc2626', fontSize: 12 }}>{supportError}</p>
      )}
    </div>
  );
}
