import { useCallback, useEffect, useRef, useState } from 'react';
import * as blazeface from '@tensorflow-models/blazeface';
import * as cocoSsd from '@tensorflow-models/coco-ssd';
import '@tensorflow/tfjs';

type AttentionDetectorProps = {
  sessionId: string;
  authToken: string;
  onAttentionChange?: (state: 'focused' | 'distracted' | 'unknown') => void;
};

type AttentionEvent = {
  state: 'focused' | 'distracted' | 'unknown';
  event: string;
  confidence: number;
  timestamp: string;
};

export default function AttentionDetector({
  sessionId,
  authToken,
  onAttentionChange,
}: AttentionDetectorProps) {
  const [isActive, setIsActive] = useState(false);
  const [currentState, setCurrentState] = useState<'focused' | 'distracted' | 'unknown'>('unknown');
  const [error, setError] = useState<string | null>(null);
  const [modelLoading, setModelLoading] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const faceModelRef = useRef<blazeface.BlazeFaceModel | null>(null);
  const objectModelRef = useRef<cocoSsd.ObjectDetection | null>(null);
  const intervalIdRef = useRef<NodeJS.Timeout | null>(null);

  // Load ML models
  const loadModels = useCallback(async () => {
    if (faceModelRef.current && objectModelRef.current) return;

    setModelLoading(true);
    setError(null);

    try {
      const [faceModel, objectModel] = await Promise.all([
        blazeface.load(),
        cocoSsd.load(),
      ]);

      faceModelRef.current = faceModel;
      objectModelRef.current = objectModel;
      setModelLoading(false);
    } catch (err) {
      setError('Failed to load AI models. Please refresh the page.');
      setModelLoading(false);
      console.error('Model loading error:', err);
    }
  }, []);

  // Send attention event to backend
  const sendAttentionEvent = useCallback(
    async (event: AttentionEvent) => {
      if (!sessionId || !authToken) return;

      const base = (process.env.NEXT_PUBLIC_API_BASE ?? '').replace(/\/$/, '');
      const endpoint = `${base}/interview/${sessionId}/attention`;

      try {
        await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify(event),
        });
      } catch (err) {
        console.error('Failed to send attention event:', err);
      }
    },
    [sessionId, authToken]
  );

  // Analyze frame for attention signals
  const analyzeFrame = useCallback(async () => {
    if (
      !videoRef.current ||
      !canvasRef.current ||
      !faceModelRef.current ||
      !objectModelRef.current
    ) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx || video.readyState !== 4) return;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current frame
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    try {
      // Detect faces
      const faces = await faceModelRef.current.estimateFaces(canvas, false);

      // Detect objects (looking for phones, books, etc.)
      const predictions = await objectModelRef.current.detect(canvas);

      // Analyze attention state
      let newState: 'focused' | 'distracted' | 'unknown' = 'unknown';
      let eventDescription = '';
      let confidence = 0;

      if (faces.length === 0) {
        newState = 'distracted';
        eventDescription = 'no_face_detected';
        confidence = 0.9;
      } else if (faces.length > 1) {
        newState = 'distracted';
        eventDescription = 'multiple_faces_detected';
        confidence = 0.8;
      } else {
        // Check for distracting objects
        const distractingObjects = predictions.filter(
          (pred) =>
            pred.class === 'cell phone' ||
            pred.class === 'book' ||
            pred.class === 'laptop' ||
            pred.class === 'tv'
        );

        if (distractingObjects.length > 0) {
          newState = 'distracted';
          eventDescription = `${distractingObjects[0].class}_detected`;
          confidence = distractingObjects[0].score;
        } else {
          // Face is present and no distractions
          const face = faces[0];
          const topLeft = face.topLeft as [number, number];
          const bottomRight = face.bottomRight as [number, number];
          const centerX = (topLeft[0] + bottomRight[0]) / 2;
          const centerY = (topLeft[1] + bottomRight[1]) / 2;

          // Check if face is roughly centered (person looking at camera)
          const isCentered =
            centerX > canvas.width * 0.3 &&
            centerX < canvas.width * 0.7 &&
            centerY > canvas.height * 0.2 &&
            centerY < canvas.height * 0.8;

          if (isCentered) {
            newState = 'focused';
            eventDescription = 'looking_forward';
            const prob = face.probability as number[] | undefined;
            confidence = prob?.[0] ?? 0.85;
          } else {
            newState = 'distracted';
            eventDescription = 'looking_away';
            confidence = 0.7;
          }
        }
      }

      // Update state and send event if changed
      if (newState !== currentState) {
        setCurrentState(newState);
        onAttentionChange?.(newState);

        const event: AttentionEvent = {
          state: newState,
          event: eventDescription,
          confidence,
          timestamp: new Date().toISOString(),
        };

        await sendAttentionEvent(event);
      }
    } catch (err) {
      console.error('Frame analysis error:', err);
    }
  }, [currentState, onAttentionChange, sendAttentionEvent]);

  // Start camera and detection
  const startDetection = useCallback(async () => {
    if (isActive) return;

    setError(null);

    try {
      // Load models if not already loaded
      await loadModels();

      // Request camera access
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user',
        },
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        await videoRef.current.play();
      }

      // Start periodic analysis (every 2 seconds)
      const intervalId = setInterval(analyzeFrame, 2000);
      intervalIdRef.current = intervalId;

      setIsActive(true);
    } catch (err) {
      if (err instanceof Error) {
        if (err.name === 'NotAllowedError') {
          setError('Camera permission denied. Please allow camera access.');
        } else if (err.name === 'NotFoundError') {
          setError('No camera found on this device.');
        } else {
          setError('Failed to start camera. Please try again.');
        }
      }
      console.error('Camera access error:', err);
    }
  }, [isActive, loadModels, analyzeFrame]);

  // Stop camera and detection
  const stopDetection = useCallback(() => {
    if (intervalIdRef.current) {
      clearInterval(intervalIdRef.current);
      intervalIdRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsActive(false);
    setCurrentState('unknown');
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopDetection();
    };
  }, [stopDetection]);

  return (
    <div style={{ marginTop: 16, padding: 16, border: '1px solid #e5e7eb', borderRadius: 8 }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: 16, fontWeight: 600 }}>
        Attention Monitoring
      </h3>

      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <button
            type="button"
            onClick={isActive ? stopDetection : startDetection}
            disabled={modelLoading}
            style={{
              padding: '8px 16px',
              backgroundColor: isActive ? '#dc2626' : '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: 6,
              cursor: modelLoading ? 'not-allowed' : 'pointer',
              opacity: modelLoading ? 0.6 : 1,
            }}
          >
            {modelLoading
              ? 'Loading AI Models...'
              : isActive
              ? 'Stop Monitoring'
              : 'Start Monitoring'}
          </button>

          {isActive && (
            <div style={{ marginTop: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor:
                      currentState === 'focused'
                        ? '#10b981'
                        : currentState === 'distracted'
                        ? '#f59e0b'
                        : '#6b7280',
                  }}
                />
                <span style={{ fontSize: 14, fontWeight: 500 }}>
                  Status: {currentState === 'focused' ? 'Focused ✓' :
                           currentState === 'distracted' ? 'Distracted' :
                           'Analyzing...'}
                </span>
              </div>
              <p style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
                AI is monitoring your attention using your camera
              </p>
            </div>
          )}

          {error && (
            <p style={{ marginTop: 8, color: '#dc2626', fontSize: 12 }}>{error}</p>
          )}
        </div>

        {/* Hidden video and canvas for processing */}
        <div style={{ display: 'none' }}>
          <video ref={videoRef} playsInline muted />
          <canvas ref={canvasRef} />
        </div>

        {/* Optional: Show video preview */}
        {isActive && (
          <div style={{ width: 160, height: 120, position: 'relative' }}>
            <video
              ref={videoRef}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                borderRadius: 8,
                border: '2px solid #e5e7eb',
              }}
              playsInline
              muted
            />
            <div
              style={{
                position: 'absolute',
                top: 4,
                right: 4,
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: '#dc2626',
                animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
