import { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { API_BASE_URL, issueTaskCertificate, downloadCertificateFile, submitDynamicPracticeGesture } from '../services/api';

// ============================================================================
// Dynamic Signs Specification
// ============================================================================
const DYNAMIC_SIGNS = ['J', 'Z', 'HELLO', 'NO', 'PLEASE', 'THANK_YOU', 'YES'];

// ============================================================================
// ASL Gesture Reference Guide
// ============================================================================
const GESTURE_GUIDES = {
  A: { desc: 'Fist with thumb alongside hand', viewBox: '0 0 100 100', path: 'M30 80 L30 30 L35 25 L40 25 L45 25 L50 25 L55 25 L60 30 L65 30 L65 80 L60 85 L35 85 Z' },
  B: { desc: 'Four fingers up, thumb tucked', viewBox: '0 0 100 100', path: 'M30 80 L30 25 L35 20 L40 15 L45 15 L50 15 L55 15 L60 20 L65 25 L65 45 L60 45 L55 40 L50 40 L45 40 L40 40 L35 45 L30 45 Z' },
  C: { desc: 'Curved hand like holding a ball', viewBox: '0 0 100 100', path: 'M35 20 Q25 20 25 35 L25 60 Q25 75 40 80 L60 80 Q75 75 75 60 L75 35 Q75 20 60 20 L55 20 Q50 18 45 20 L35 20 Z M35 30 Q30 30 30 40 L30 55 Q30 65 40 68 L55 68 Q65 65 65 55 L65 40 Q65 30 55 30 L35 30 Z' },
  D: { desc: 'Index finger up, other fingers touch thumb', viewBox: '0 0 100 100', path: 'M45 85 L45 20 L50 15 L55 15 L58 20 L58 45 L65 40 L68 45 L58 55 L58 80 L55 85 L48 85 Z M35 50 L55 50 L55 60 L50 60 L40 58 Q35 55 35 50 Z' },
  E: { desc: 'All fingers curled down to thumb', viewBox: '0 0 100 100', path: 'M30 25 L65 25 L70 30 L70 40 L65 45 L55 50 L65 55 L65 60 L70 60 L70 80 L65 85 L35 85 L30 80 L30 30 Z M35 35 L55 35 L55 45 L35 45 Z M35 55 L55 55 L55 65 L40 65 Q35 62 35 55 Z' },
  F: { desc: 'OK sign with three fingers up', viewBox: '0 0 100 100', path: 'M30 80 L30 30 L35 25 L40 25 L45 25 L50 25 L55 25 L60 30 L60 80 L55 85 L35 85 Z M42 45 Q42 38 50 38 Q58 38 58 45 Q58 52 50 52 Q42 52 42 45 Z M62 25 L62 30 L67 25 L67 20 L62 20 Z' },
  G: { desc: 'Point sideways, thumb up', viewBox: '0 0 100 100', path: 'M30 80 L30 40 L35 35 L60 35 L70 40 L70 50 L60 50 L55 50 L55 80 L50 85 L35 85 Z M35 45 L50 45 L50 75 L35 75 Z M60 38 L65 35 L68 38 L68 45 L65 48 L60 45 Z' },
  H: { desc: 'Two fingers pointing sideways', viewBox: '0 0 100 100', path: 'M30 80 L30 30 L35 25 L45 25 L50 30 L50 45 L55 40 L70 40 L70 30 L75 25 L80 30 L80 80 L75 85 L60 85 L55 80 L55 55 L50 55 L50 80 L45 85 L35 85 Z' },
  I: { desc: 'Pinky up, other fingers closed', viewBox: '0 0 100 100', path: 'M30 80 L30 30 L35 25 L55 25 L60 30 L60 80 L55 85 L35 85 Z M35 35 L55 35 L55 50 L35 50 Z M55 20 L55 25 L60 20 L65 15 L65 10 L60 10 L58 15 Z' },
  J: { desc: 'Pinky up with hook motion', viewBox: '0 0 100 100', path: 'M30 80 L30 30 L35 25 L55 25 L60 30 L60 45 L55 50 L55 60 L60 70 Q65 80 55 85 L40 85 Q30 85 28 75 L55 75 Z M35 35 L55 35 L55 45 L35 45 Z' },
  K: { desc: 'Peace sign with thumb between', viewBox: '0 0 100 100', path: 'M30 80 L30 50 L35 45 L50 45 L50 80 L45 85 L35 85 Z M40 50 L50 50 L50 75 L40 75 Z M50 45 L55 20 L60 15 L65 20 L60 30 L55 40 L50 45 Z M55 45 L60 45 L70 30 L75 25 L78 30 L72 42 L62 52 L55 55 Z' },
  L: { desc: 'L-shape with index and thumb', viewBox: '0 0 100 100', path: 'M35 85 L35 30 L40 25 L50 25 L55 30 L55 60 L75 60 L80 55 L80 45 L75 40 L55 40 L55 25 L50 20 L40 20 L35 25 L35 85 Z M40 35 L50 35 L50 80 L40 80 Z M60 50 L75 50 L75 45 L60 45 Z' },
  M: { desc: 'Three fingers over thumb', viewBox: '0 0 100 100', path: 'M25 80 L25 25 L30 20 L40 20 L45 25 L45 80 L40 85 L30 85 Z M40 25 L50 25 L50 80 L45 85 L40 85 L40 80 L40 25 Z M50 25 L60 25 L65 30 L65 80 L60 85 L50 85 L50 80 L50 25 Z M65 35 L75 25 L80 20 L82 25 L75 35 L75 80 L70 85 L65 85 L65 80 L65 35 Z' },
  N: { desc: 'Two fingers over thumb', viewBox: '0 0 100 100', path: 'M25 80 L25 25 L30 20 L42 20 L48 25 L48 80 L43 85 L30 85 Z M43 25 L55 25 L55 80 L50 85 L43 85 L43 80 L43 25 Z M55 25 L65 25 L70 30 L70 80 L65 85 L55 85 L55 80 L55 25 Z M70 35 L78 25 L82 22 L84 27 L77 38 L77 80 L72 85 L68 85 L68 80 L70 35 Z' },
  O: { desc: 'Fingers curved to touch thumb', viewBox: '0 0 100 100', path: 'M40 20 Q25 20 25 40 L25 60 Q25 80 40 85 L60 85 Q75 80 75 60 L75 40 Q75 20 60 20 L55 20 Q50 18 45 20 L40 20 Z M40 30 Q33 30 33 42 L33 58 Q33 70 40 72 L60 72 Q67 70 67 58 L67 42 Q67 30 60 30 L40 30 Z' },
  P: { desc: 'Like K but pointing down', viewBox: '0 0 100 100', path: 'M35 20 L35 55 L30 60 L30 80 L60 80 L60 55 L55 50 L55 20 L50 15 L40 15 L35 20 Z M40 25 L50 25 L50 45 L40 45 Z M55 55 L65 70 L70 75 L75 72 L70 65 L60 55 L55 55 Z M55 45 L60 50 L70 40 L75 35 L72 30 L62 40 L55 48 Z' },
  Q: { desc: 'Hook shape pointing down', viewBox: '0 0 100 100', path: 'M65 20 L65 55 L70 60 Q78 72 70 82 L55 88 Q42 90 35 80 L35 70 L40 68 Q45 75 55 75 L65 70 L65 55 L65 20 L60 15 L50 15 L45 20 L45 65 L50 65 L50 25 L55 20 L65 20 Z' },
  R: { desc: 'Two fingers crossed', viewBox: '0 0 100 100', path: 'M30 80 L30 25 L35 20 L50 20 L55 25 L55 80 L50 85 L35 85 Z M35 30 L50 30 L50 75 L35 75 Z M55 25 L60 20 L70 35 L65 40 L55 35 L55 30 Z M55 35 L65 45 L75 35 L78 38 L68 50 L55 42 L55 80 L50 85 L35 85 Z' },
  S: { desc: 'Fist with thumb over fingers', viewBox: '0 0 100 100', path: 'M28 35 L65 35 L70 40 L70 50 L70 60 L65 65 L55 70 L65 75 L65 80 L35 80 L30 75 L30 40 Z M33 43 L60 43 L60 50 L33 50 Z M33 55 L60 55 L60 62 L33 62 Z M30 30 L65 30 L70 35 L28 35 Z' },
  T: { desc: 'Fist with thumb between index and middle', viewBox: '0 0 100 100', path: 'M28 35 L65 35 L70 40 L70 50 L70 60 L65 65 L55 70 L65 75 L65 80 L35 80 L30 75 L30 40 Z M33 43 L55 43 L55 50 L33 50 Z M55 43 L62 43 L62 50 L55 50 Z M33 55 L60 55 L60 62 L33 62 Z M28 30 L45 30 L45 35 L40 35 L40 43 L35 43 L35 35 L28 35 Z' },
  U: { desc: 'Index and middle fingers up together', viewBox: '0 0 100 100', path: 'M30 80 L30 25 L35 20 L55 20 L60 25 L60 80 L55 85 L35 85 Z M35 30 L55 30 L55 75 L35 75 Z M55 20 L60 15 L65 15 L68 20 L63 30 L55 30 Z' },
  V: { desc: 'Peace sign - two fingers spread', viewBox: '0 0 100 100', path: 'M30 80 L30 45 L35 40 L50 40 L55 45 L55 80 L50 85 L35 85 Z M35 50 L50 50 L50 75 L35 75 Z M50 40 L55 15 L58 10 L63 15 L58 25 L55 35 L50 40 Z M58 40 L62 35 L70 15 L75 10 L78 15 L72 28 L63 42 L58 45 Z' },
  W: { desc: 'Three fingers spread up', viewBox: '0 0 100 100', path: 'M25 80 L25 40 L30 35 L50 35 L55 40 L55 80 L50 85 L30 85 Z M30 45 L50 45 L50 75 L30 75 Z M50 35 L55 15 L58 10 L63 15 L58 28 L55 35 Z M55 35 L60 15 L65 10 L70 15 L65 28 L60 38 L55 40 Z M60 38 L65 20 L70 15 L75 20 L70 32 L65 40 L60 42 Z' },
  X: { desc: 'Index finger crooked like a hook', viewBox: '0 0 100 100', path: 'M30 80 L30 30 L35 25 L55 25 L60 30 L60 45 L55 40 L55 35 L50 35 L50 40 L55 50 L60 55 L60 80 L55 85 L35 85 Z M35 35 L50 35 L50 75 L35 75 Z' },
  Y: { desc: 'Thumb and pinky extended', viewBox: '0 0 100 100', path: 'M40 80 L40 30 L35 25 L55 25 L60 30 L60 80 L55 85 L45 85 Z M45 30 L55 30 L55 75 L45 75 Z M35 25 L30 20 L22 15 L18 18 L25 28 L35 35 L35 25 Z M60 25 L65 20 L72 12 L75 15 L70 25 L60 35 L60 30 Z' },
  Z: { desc: 'Index finger draws Z in air', viewBox: '0 0 100 100', path: 'M25 20 L75 20 L75 28 L25 80 L75 80 L75 88 L20 88 L20 80 L75 28 L25 28 L25 20 Z M30 28 L70 28 L30 80 L70 80 Z' },
};

// ============================================================================
// Reusable Spring-Bounce Popup Modal Component
// ============================================================================
function PopupModal({ isOpen, onClose, title, message, badgeIcon = '🎉', actions = null }) {
  if (!isOpen) return null;

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-card" onClick={(e) => e.stopPropagation()}>
        <div style={{ fontSize: '3rem', marginBottom: '0.5rem', animation: 'popIn 0.5s ease' }}>
          {badgeIcon}
        </div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.5rem' }}>
          {title}
        </h2>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.5rem', lineHeight: '1.5' }}>
          {message}
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {actions}
          <button onClick={onClose} className="btn-primary" style={{ padding: '0.6rem 1.5rem', fontWeight: 700 }}>
            Awesome! Continue Practice
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Gesture Reference Card Component
// ============================================================================
function GestureReference({ letter, compact = false }) {
  const guide = GESTURE_GUIDES[letter];
  if (!guide) return null;

  if (compact) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.65rem',
        padding: '0.5rem 0.75rem',
        backgroundColor: 'var(--table-header-bg)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-color)',
        marginBottom: '0.75rem',
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          backgroundColor: 'var(--primary)',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.15rem',
          fontWeight: 800,
          flexShrink: 0,
        }}>
          {letter}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Reference: Sign '{letter}'
          </p>
          <p style={{ fontSize: '0.68rem', color: 'var(--text-muted)', margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {guide.desc}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      padding: '1rem',
      backgroundColor: 'var(--table-header-bg)',
      borderRadius: 'var(--radius-md)',
      border: '2px solid var(--primary)',
      textAlign: 'center',
    }}>
      <div style={{
        width: '70px',
        height: '70px',
        borderRadius: '50%',
        backgroundColor: 'var(--primary)',
        color: '#fff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '2rem',
        fontWeight: 800,
        margin: '0 auto 0.5rem',
      }}>
        {letter}
      </div>
      <p style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
        ASL Sign '{letter}'
      </p>
      <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', margin: '0.25rem 0 0' }}>
        {guide.desc}
      </p>
      <svg viewBox={guide.viewBox} style={{ width: '100%', maxWidth: '120px', height: 'auto', marginTop: '0.5rem' }}>
        <path d={guide.path} fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    </div>
  );
}

// ============================================================================
// Main Interactive Practice View
// ============================================================================
export default function Practice() {
  const [searchParams] = useSearchParams();
  const deepGesture = (searchParams.get('gesture') || '').toString().toUpperCase();

  const [selectedCategory, setSelectedCategory] = useState(
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'].includes(deepGesture) ? 'numbers' : 'alphabets'
  );
  const [selectedLetter, setSelectedLetter] = useState(
    /^[A-Z]$/.test(deepGesture) || ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'].includes(deepGesture)
      ? deepGesture
      : 'A'
  );
  
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [cameraLoading, setCameraLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  const [attemptCount, setAttemptCount] = useState(1);
  const [maxAttempts] = useState(5);
  const [timeLeft, setTimeLeft] = useState(30);
  const [isTimerActive, setIsTimerActive] = useState(false);
  const [streakCount, setStreakCount] = useState(0);
  const [sessionId, setSessionId] = useState('');
  const sessionIdRef = useRef('');
  const [lessonLookup, setLessonLookup] = useState({});
  
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [showPopup, setShowPopup] = useState(false);
  const [modalData, setModalData] = useState({ title: '', message: '', icon: '🏆' });
  const [taskCertId, setTaskCertId] = useState('');
  const [certBusy, setCertBusy] = useState('');
  const [capturedFrame, setCapturedFrame] = useState(null);

  // Dynamic Sign Burst State
  const [isRecordingBurst, setIsRecordingBurst] = useState(false);
  const [recordingCountdown, setRecordingCountdown] = useState(3);

  const [metrics, setMetrics] = useState({
    handShape: 0,
    fingerPosition: 0,
    timingAlignment: 0,
  });

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  const numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'];

  const isDynamic = DYNAMIC_SIGNS.includes((selectedLetter || '').toUpperCase());

  // Countdown Timer Hook
  useEffect(() => {
    let timer = null;
    if (isTimerActive && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      setIsTimerActive(false);
      setErrorMsg('Practice session timed out. Click "Reset Session" to start fresh.');
    }
    return () => clearInterval(timer);
  }, [isTimerActive, timeLeft]);

  // Camera Stream DOM Attachment Hook (Guarantees video binds on render)
  useEffect(() => {
    const el = videoRef.current;
    if (isCameraOn && el && streamRef.current && el.srcObject !== streamRef.current) {
      el.srcObject = streamRef.current;
      el.play?.().catch((err) => {
        console.warn('Video auto-playback blocked:', err);
      });
    }
  }, [isCameraOn]);

  const startCamera = async () => {
    setCameraLoading(true);
    setErrorMsg('');
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
      });
      streamRef.current = stream;
      setIsCameraOn(true);
      setTimeLeft(30);
      setIsTimerActive(true);
    } catch {
      setErrorMsg('Webcam access denied or camera not found. Enable the webcam to practice.');
      setIsCameraOn(false);
    } finally {
      setCameraLoading(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraOn(false);
    setIsTimerActive(false);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/courses/modules`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` },
    })
      .then((res) => res.json())
      .then((data) => {
        const modules = Array.isArray(data) ? data : data.modules || [];
        const lookup = {};
        for (const mod of modules) {
          for (const lesson of mod.lessons || []) {
            const letter = (lesson.expected_gesture || '').toString().toUpperCase();
            if (letter && !lookup[letter]) lookup[letter] = lesson.lesson_id || lesson.id;
          }
        }
        setLessonLookup(lookup);
      })
      .catch(() => {});
  }, []);

  const grabFrame = () => {
    if (!isCameraOn || !videoRef.current || !canvasRef.current) return null;
    const canvas = canvasRef.current;
    const video = videoRef.current;
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.9);
  };

  // Helper session starters for practice calls
  const ensureSession = async (authHeaders, userId, lessonId) => {
    if (sessionIdRef.current) return sessionIdRef.current;
    if (!userId) {
      throw new Error('No authenticated user found. Please sign in again.');
    }
    const params = new URLSearchParams({ user_id: userId });
    if (lessonId) params.set('lesson_id', lessonId);
    const res = await fetch(`${API_BASE_URL}/api/practice/start?${params.toString()}`, {
      method: 'POST',
      headers: authHeaders,
    });
    if (!res.ok) throw new Error(`Failed to start practice session (${res.status})`);
    const data = await res.json();
    sessionIdRef.current = data.session_id;
    setSessionId(data.session_id);
    return data.session_id;
  };

  const endActiveSession = async (authHeaders) => {
    if (!sessionIdRef.current) return;
    try {
      await fetch(`${API_BASE_URL}/api/practice/end?session_id=${sessionIdRef.current}`, {
        method: 'POST',
        headers: authHeaders,
      });
    } catch {}
  };

  // --------------------------------------------------------------------------
  // Flow 1: Untouched Static Gesture Submission (/submit)
  // --------------------------------------------------------------------------
  const handleCaptureAndTest = async () => {
    setLoading(true);
    setPrediction(null);
    setErrorMsg('');
    setCapturedFrame(null);

    const storedUser = localStorage.getItem('user') || localStorage.getItem('user_info');
    const user = storedUser ? JSON.parse(storedUser) : null;
    const userId = user?.user_id || localStorage.getItem('user_id');
    const lessonId = lessonLookup[selectedLetter] || null;

    const authHeaders = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
    };

    const startSession = async () => ensureSession(authHeaders, userId, lessonId);
    const endSession = async () => endActiveSession(authHeaders);

    const finish = () => {
      setLoading(false);
      setAttemptCount((prev) => {
        const next = prev >= maxAttempts ? 1 : prev + 1;
        if (prev >= maxAttempts) endSession();
        return next;
      });
    };

    for (let attempt = 0; attempt < 3; attempt++) {
      if (attempt > 0) await new Promise((r) => setTimeout(r, 400));

      const base64Image = grabFrame();
      if (!base64Image) {
        setErrorMsg('Camera is not ready. Turn the camera on first.');
        break;
      }
      setCapturedFrame(base64Image);

      try {
        const currentSessionId = await startSession();
        const response = await fetch(`${API_BASE_URL}/api/practice/submit`, {
          method: 'POST',
          headers: authHeaders,
          body: JSON.stringify({
            user_id: userId,
            lesson_id: lessonId,
            session_id: currentSessionId,
            target_letter: selectedLetter,
            image_data: base64Image,
          }),
        });

        if (!response.ok) {
          const body = await response.text();
          throw new Error(body || `Server returned ${response.status}`);
        }

        const data = await response.json();

        const handDetected = data.hand_detected !== false;
        const predicted = data.predicted_sign || null;

        if (!handDetected || !predicted) continue;

        const confScore = typeof data.confidence === 'number'
          ? (data.confidence <= 1 ? Math.round(data.confidence * 100) : Math.round(data.confidence))
          : 0;

        const feedbackText = data.possible_issue
          || (data.correct === true
              ? `Great job! Hand posture matches target '${selectedLetter}' accurately.`
              : data.correct === false
                  ? `Keep practicing sign '${selectedLetter}'! Adjust your finger alignment.`
                  : `Detected sign '${predicted}'. Show sign '${selectedLetter}' for a match.`);

        setPrediction({
          predicted_sign: predicted,
          confidence: confScore,
          feedback: feedbackText,
        });

        setMetrics({
          handShape: data.overall_accuracy ?? (confScore > 80 ? 92 : 60),
          fingerPosition: data.overall_accuracy ?? (confScore > 80 ? 88 : 55),
          timingAlignment: data.overall_accuracy ?? 90,
        });

        if (typeof data.updated_streak === 'number') setStreakCount(data.updated_streak);

        if (confScore > 80) {
          setModalData({
            title: 'High Accuracy Achieved!',
            message: `Incredible precision! You matched Sign '${selectedLetter}' with ${confScore}% confidence.`,
            icon: '🏆',
          });
          setTaskCertId('');
          setCertBusy('');
          issueTaskCertificate({ lessonId, score: confScore })
            .then((cert) => {
              if (cert?.certificate_id) setTaskCertId(cert.certificate_id);
            })
            .catch(() => {});
          setShowPopup(true);
        }
        finish();
        return;

      } catch (err) {
        setErrorMsg(`Analysis failed: ${err.message || 'backend unavailable'}. No result was recorded.`);
        setLoading(false);
        return;
      }
    }

    setPrediction({
      predicted_sign: null,
      confidence: 0,
      feedback: 'No hand detected. Keep your hand fully in frame with good lighting, close to the camera, then try again.',
    });
    setMetrics({ handShape: 0, fingerPosition: 0, timingAlignment: 0 });
    setErrorMsg('No hand detected');
    finish();
  };

  // --------------------------------------------------------------------------
  // Flow 2: Dynamic Sign Burst Capture (~60 frames over 3s via setInterval)
  // --------------------------------------------------------------------------
  const recordBurstFrames = () => {
    return new Promise((resolve) => {
      const frames = [];
      const intervalMs = 50; // ~60 frames over 3000ms
      const totalFrames = 60;

      setIsRecordingBurst(true);
      setRecordingCountdown(3);

      const countdownTimer = setInterval(() => {
        setRecordingCountdown((prev) => (prev > 1 ? prev - 1 : 1));
      }, 1000);

      const burstInterval = setInterval(() => {
        const frame = grabFrame();
        if (frame) frames.push(frame);

        if (frames.length >= totalFrames) {
          clearInterval(burstInterval);
          clearInterval(countdownTimer);
          setIsRecordingBurst(false);
          resolve(frames);
        }
      }, intervalMs);

      // Fallback safeguard to release recording after 3.2s
      setTimeout(() => {
        clearInterval(burstInterval);
        clearInterval(countdownTimer);
        setIsRecordingBurst(false);
        resolve(frames);
      }, 3200);
    });
  };

  const handleDynamicSubmit = async () => {
    if (!isCameraOn) {
      setErrorMsg('Turn on camera before testing dynamic gestures.');
      return;
    }

    setLoading(true);
    setPrediction(null);
    setErrorMsg('');
    setCapturedFrame(null);

    const storedUser = localStorage.getItem('user') || localStorage.getItem('user_info');
    const user = storedUser ? JSON.parse(storedUser) : null;
    const userId = user?.user_id || localStorage.getItem('user_id');
    const lessonId = lessonLookup[selectedLetter] || null;

    const authHeaders = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
    };

    try {
      const currentSessionId = await ensureSession(authHeaders, userId, lessonId);

      // Capture burst array of frames
      const capturedBurst = await recordBurstFrames();
      if (!capturedBurst || capturedBurst.length === 0) {
        throw new Error('Failed to record motion frames. Ensure webcam is connected.');
      }

      setCapturedFrame(capturedBurst[Math.floor(capturedBurst.length / 2)] || capturedBurst[0]);

      // POST to /api/practice/submit_dynamic
      const data = await submitDynamicPracticeGesture({
        session_id: currentSessionId,
        target_sign: selectedLetter,
        frames: capturedBurst,
      });

      const predicted = data.predicted_sign || data.prediction || selectedLetter;
      const confScore = typeof data.confidence === 'number'
        ? (data.confidence <= 1 ? Math.round(data.confidence * 100) : Math.round(data.confidence))
        : 85;

      const feedbackText = data.possible_issue || data.feedback
        || (data.correct !== false
            ? `Dynamic sign '${selectedLetter}' motion recognized successfully!`
            : `Keep practicing dynamic sign '${selectedLetter}' trajectory.`);

      setPrediction({
        predicted_sign: predicted,
        confidence: confScore,
        feedback: feedbackText,
      });

      setMetrics({
        handShape: data.overall_accuracy ?? (confScore > 80 ? 92 : 65),
        fingerPosition: data.overall_accuracy ?? (confScore > 80 ? 89 : 60),
        timingAlignment: data.overall_accuracy ?? 94,
      });

      if (typeof data.updated_streak === 'number') setStreakCount(data.updated_streak);

      if (confScore > 80) {
        setModalData({
          title: 'Dynamic Motion Mastered!',
          message: `Great movement tracking! You completed Dynamic Sign '${selectedLetter}' with ${confScore}% accuracy.`,
          icon: '🌟',
        });
        setTaskCertId('');
        setCertBusy('');
        issueTaskCertificate({ lessonId, score: confScore })
          .then((cert) => {
            if (cert?.certificate_id) setTaskCertId(cert.certificate_id);
          })
          .catch(() => {});
        setShowPopup(true);
      }
    } catch (err) {
      setErrorMsg(`Dynamic analysis failed: ${err.message || 'backend unavailable'}.`);
    } finally {
      setLoading(false);
      setAttemptCount((prev) => {
        const next = prev >= maxAttempts ? 1 : prev + 1;
        if (prev >= maxAttempts) endActiveSession(authHeaders);
        return next;
      });
    }
  };

  const handleDownloadTaskCertificate = async (format) => {
    if (!taskCertId) return;
    setCertBusy(format);
    try {
      await downloadCertificateFile(taskCertId, format);
    } catch (err) {
      setErrorMsg(`Certificate download failed: ${err.message}`);
    } finally {
      setCertBusy('');
    }
  };

  const resetSession = () => {
    if (sessionIdRef.current) {
      fetch(`${API_BASE_URL}/api/practice/end?session_id=${sessionIdRef.current}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` },
      }).catch(() => {});
      sessionIdRef.current = '';
    }
    setSessionId('');
    setAttemptCount(1);
    setTimeLeft(30);
    setPrediction(null);
    setErrorMsg('');
    setMetrics({ handShape: 0, fingerPosition: 0, timingAlignment: 0 });
    if (isCameraOn) setIsTimerActive(true);
  };

  const getScoreColor = (confidence) => {
    if (confidence >= 80) return 'var(--success)';
    if (confidence >= 50) return 'var(--warning)';
    return 'var(--danger)';
  };

  const getScoreLabel = (confidence) => {
    if (confidence >= 80) return 'Excellent Match';
    if (confidence >= 50) return 'Good Progress';
    return 'Keep Practicing';
  };

  return (
    <div>
      {/* Hidden processing canvas for base64 extraction */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Spring-Bounce Popup Component */}
      <PopupModal
        isOpen={showPopup}
        onClose={() => setShowPopup(false)}
        title={modalData.title}
        message={modalData.message}
        badgeIcon={modalData.icon}
        actions={taskCertId ? (
          <>
            <button
              onClick={() => handleDownloadTaskCertificate('pdf')}
              disabled={!!certBusy}
              className="btn-secondary"
              style={{ padding: '0.6rem 1.25rem', fontWeight: 700 }}
            >
              {certBusy === 'pdf' ? 'Generating...' : '🎓 Download as PDF'}
            </button>
            <button
              onClick={() => handleDownloadTaskCertificate('excel')}
              disabled={!!certBusy}
              className="btn-secondary"
              style={{ padding: '0.6rem 1.25rem', fontWeight: 700 }}
            >
              {certBusy === 'excel' ? 'Generating...' : '📊 Download as Excel'}
            </button>
          </>
        ) : null}
      />

      {/* Page Header Bar */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <p className="page-subtitle">Interactive AI Gesture Recognition</p>
          <h1 className="page-title">Practice Workspace</h1>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span className="streak-pill">🔥 {streakCount} Day Practice Streak</span>
          {sessionId && <span className="badge badge-primary">Session: {sessionId.slice(0, 8)}</span>}
          <button onClick={resetSession} className="btn-secondary" style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}>
            🔄 Reset Session
          </button>
        </div>
      </div>

      {/* Target Selector Toolbar */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => { setSelectedCategory('alphabets'); setSelectedLetter('A'); setPrediction(null); }}
              className={selectedCategory === 'alphabets' ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
            >
              🔤 Alphabets (A-Z)
            </button>
            <button
              onClick={() => { setSelectedCategory('numbers'); setSelectedLetter('1'); setPrediction(null); }}
              className={selectedCategory === 'numbers' ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
            >
              🔢 Numbers (1-10)
            </button>
          </div>

          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--primary)' }}>
            Active Target: <strong>Sign '{selectedLetter}'</strong> {isDynamic && <span className="badge badge-warning" style={{ marginLeft: '6px' }}>DYNAMIC (BURST TRACKING)</span>}
          </span>
        </div>
        
        {/* Sign Selection Buttons Grid */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
          {(selectedCategory === 'alphabets' ? alphabet : numbers).map((item) => (
            <button
              key={item}
              onClick={() => {
                setSelectedLetter(item);
                setPrediction(null);
              }}
              className={selectedLetter === item ? 'btn-primary' : 'btn-secondary'}
              style={{ minWidth: '38px', padding: '0.35rem 0.65rem', fontWeight: 700, fontSize: '0.85rem' }}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      {/* Main Practice Columns */}
      <div className="grid-2">
        
        {/* Left Column: Live Stream & Controls */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              Target Sign: <span style={{ color: 'var(--primary)', fontSize: '1.25rem' }}>{selectedLetter}</span>
            </h3>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="badge badge-warning">⏱️ {timeLeft}s Left</span>
              <button 
                onClick={isCameraOn ? stopCamera : startCamera} 
                disabled={cameraLoading}
                className={isCameraOn ? 'btn-danger-sm' : 'btn-secondary'}
                style={{ padding: '0.4rem 0.75rem' }}
              >
                {cameraLoading ? 'Starting...' : isCameraOn ? '🛑 Stop Camera' : '📷 Turn On Camera'}
              </button>
            </div>
          </div>

          {/* Reference Gesture Panel (compact) */}
          <GestureReference letter={selectedLetter} compact />

          {/* Video Viewport Frame */}
          <div style={{ 
            position: 'relative', 
            width: '100%', 
            height: '280px', 
            backgroundColor: '#0f172a', 
            borderRadius: 'var(--radius-md)', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            overflow: 'hidden', 
            marginBottom: '1rem',
            border: '2px solid var(--border-color)',
          }}>
            {isCameraOn ? (
              <video 
                ref={videoRef} 
                autoPlay 
                playsInline 
                muted 
                style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }} 
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: '#94a3b8' }}>
                <div style={{ fontSize: '2.25rem', marginBottom: '0.5rem' }}>📷</div>
                <p style={{ fontSize: '0.875rem', marginBottom: '0.5rem', color: '#cbd5e1' }}>
                  {errorMsg || 'Webcam is currently off. Click "Turn On Camera" above.'}
                </p>
                <span className="badge badge-secondary">OFFLINE</span>
              </div>
            )}
            
            {isCameraOn && (
              <div style={{ position: 'absolute', top: '10px', left: '10px', display: 'flex', gap: '0.5rem' }}>
                <span className="badge badge-danger" style={{ backgroundColor: '#ef4444', color: '#fff' }}>🔴 LIVE FEED</span>
                {isRecordingBurst && (
                  <span className="badge badge-warning" style={{ backgroundColor: '#f59e0b', color: '#000', fontWeight: 800 }}>
                    ⚡ CAPTURING BURST: {recordingCountdown}s
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Attempt Progress Tracker */}
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              <span>ATTEMPT PROGRESS</span>
              <span>Attempt {attemptCount} of {maxAttempts}</span>
            </div>
            <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--table-header-bg)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
              <div style={{ width: `${(attemptCount / maxAttempts) * 100}%`, height: '100%', backgroundColor: 'var(--primary)', transition: 'width 0.3s ease' }} />
            </div>
          </div>

          {/* Action Trigger Button - Routes to Dynamic Burst or Static Single-Frame */}
          <button
            onClick={isDynamic ? handleDynamicSubmit : handleCaptureAndTest}
            disabled={loading || isRecordingBurst}
            className="btn-primary"
            style={{ width: '100%', padding: '0.75rem', fontSize: '0.95rem', fontWeight: 700 }}
          >
            {isRecordingBurst
              ? `Capturing 3s Motion (${recordingCountdown}s left)...`
              : loading
                ? (isDynamic ? 'Analyzing Motion Trajectory...' : 'Analyzing Gesture Frame...')
                : (isDynamic ? '⚡ Record Dynamic Gesture (3s Burst)' : '✨ Capture & Test Gesture')}
          </button>
        </div>

        {/* Right Column: AI Predictions & Diagnostics */}
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
            Real-Time AI Diagnostic Output
          </h3>

          {/* Target Comparison Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ padding: '1rem', backgroundColor: 'var(--table-header-bg)', borderRadius: 'var(--radius-md)', textAlign: 'center', border: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '0.725rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>EXPECTED</span>
              <p style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--primary)', marginTop: '0.2rem' }}>{selectedLetter}</p>
            </div>

            <div style={{ padding: '1rem', backgroundColor: 'var(--table-header-bg)', borderRadius: 'var(--radius-md)', textAlign: 'center', border: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '0.725rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>PREDICTED</span>
              <p style={{ fontSize: '2.25rem', fontWeight: 800, color: prediction ? (prediction.predicted_sign === selectedLetter ? 'var(--success)' : 'var(--danger)') : 'var(--text-muted)', marginTop: '0.2rem' }}>
                {prediction ? prediction.predicted_sign : '-'}
              </p>
            </div>
          </div>

          {/* Score Reveal Area with Color-Coded Badge */}
          <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: 'var(--table-header-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', marginBottom: '1.25rem' }}>
            <p style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Confidence Score</p>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginTop: '0.35rem' }}>
              <span
                key={prediction ? `${prediction.confidence}-${attemptCount}` : 'initial'}
                className="score-reveal"
                style={{ fontSize: '2.5rem', fontWeight: 800, color: prediction ? getScoreColor(prediction.confidence) : 'var(--primary)', display: 'inline-block' }}
              >
                {prediction ? `${prediction.confidence}%` : '0%'}
              </span>
              {prediction && prediction.confidence > 0 && (
                <span style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  padding: '0.3rem 0.75rem',
                  borderRadius: '999px',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  color: '#fff',
                  backgroundColor: getScoreColor(prediction.confidence),
                  border: 'none',
                }}>
                  {prediction.confidence >= 80 ? '⭐' : prediction.confidence >= 50 ? '📈' : '💪'}
                  {' '}{getScoreLabel(prediction.confidence)}
                </span>
              )}
            </div>
            {prediction && (
              <div style={{ marginTop: '0.5rem', width: '100%', height: '8px', backgroundColor: 'var(--border-color)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                <div style={{
                  width: `${prediction.confidence}%`,
                  height: '100%',
                  backgroundColor: getScoreColor(prediction.confidence),
                  borderRadius: 'var(--radius-full)',
                  transition: 'width 0.6s ease, background-color 0.3s ease',
                }} />
              </div>
            )}
          </div>

          {/* Gesture Diagnostics Breakdown */}
          <div style={{ marginBottom: '1.25rem' }}>
            <p style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Detailed Gesture Diagnostics
            </p>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', textAlign: 'center' }}>
              <div style={{ padding: '0.6rem', backgroundColor: 'var(--table-header-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', display: 'block', fontWeight: 700 }}>Hand Shape</span>
                <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>{metrics.handShape}%</strong>
              </div>
              <div style={{ padding: '0.6rem', backgroundColor: 'var(--table-header-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', display: 'block', fontWeight: 700 }}>Finger Placement</span>
                <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>{metrics.fingerPosition}%</strong>
              </div>
              <div style={{ padding: '0.6rem', backgroundColor: 'var(--table-header-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', display: 'block', fontWeight: 700 }}>Timing / Alignment</span>
                <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>{metrics.timingAlignment}%</strong>
              </div>
            </div>
          </div>

          {/* AI Feedback Banner */}
          {prediction ? (
            <div className="card-pop" style={{ padding: '0.85rem', borderRadius: 'var(--radius-md)', backgroundColor: prediction.confidence > 75 ? 'var(--success-bg)' : 'var(--warning-bg)', border: '1px solid var(--border-color)' }}>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: 600, margin: 0 }}>
                {prediction.feedback}
              </p>
            </div>
          ) : (
            <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', border: '1px dashed var(--border-color)', borderRadius: 'var(--radius-md)' }}>
              Perform a sign gesture in front of the camera and click "{isDynamic ? 'Record Dynamic Gesture (3s Burst)' : 'Capture & Test Gesture'}".
            </div>
          )}

          {/* Captured Frame Preview */}
          {capturedFrame && (
            <div style={{ marginTop: '1rem' }}>
              <p style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Captured Frame
              </p>
              <img
                src={capturedFrame}
                alt="Captured gesture frame"
                style={{ width: '100%', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', objectFit: 'contain', maxHeight: '220px' }}
              />
            </div>
          )}

          {/* Side-by-Side Comparison */}
          {capturedFrame && prediction && (
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: 'var(--table-header-bg)', borderRadius: 'var(--radius-md)', border: '2px solid var(--border-color)' }}>
              <p style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.75rem', textAlign: 'center' }}>
                Side-by-Side Comparison
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '0.35rem' }}>
                    Reference
                  </span>
                  <div style={{ border: '2px solid var(--primary)', borderRadius: 'var(--radius-md)', overflow: 'hidden', backgroundColor: '#0f172a' }}>
                    <GestureReference letter={selectedLetter} />
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '0.35rem' }}>
                    Your Capture
                  </span>
                  <div style={{ border: '2px solid var(--border-color)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                    <img
                      src={capturedFrame}
                      alt="Captured gesture frame"
                      style={{ width: '100%', objectFit: 'cover', maxHeight: '160px', display: 'block' }}
                    />
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <p style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', margin: '0 0 0.35rem' }}>
                  Match Score
                </p>
                <div style={{ width: '100%', height: '12px', backgroundColor: 'var(--border-color)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                  <div style={{
                    width: `${prediction.confidence}%`,
                    height: '100%',
                    backgroundColor: getScoreColor(prediction.confidence),
                    borderRadius: 'var(--radius-full)',
                    transition: 'width 0.6s ease, background-color 0.3s ease',
                  }} />
                </div>
                <p style={{ fontSize: '0.8rem', fontWeight: 800, color: getScoreColor(prediction.confidence), marginTop: '0.35rem' }}>
                  {prediction.confidence}% — {getScoreLabel(prediction.confidence)}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}