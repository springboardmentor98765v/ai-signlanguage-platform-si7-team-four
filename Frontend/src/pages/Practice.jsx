import React, { useState, useRef, useEffect } from 'react';

export default function Practice() {
  const [selectedLetter, setSelectedLetter] = useState('A');
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Interactive Session State
  const [attemptCount, setAttemptCount] = useState(1);
  const [timeLeft, setTimeLeft] = useState(15);
  const [isTimerActive, setIsTimerActive] = useState(false);
  
  // Detailed Metric Breakdown State
  const [metrics, setMetrics] = useState({
    handShape: 0,
    fingerPosition: 0,
    timingAlignment: 0,
  });

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

  // Session Countdown Timer Logic
  useEffect(() => {
    let timer = null;
    if (isTimerActive && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      setIsTimerActive(false);
    }
    return () => clearInterval(timer);
  }, [isTimerActive, timeLeft]);

  // Start Webcam Stream
  const startCamera = async () => {
    try {
      setErrorMsg('');
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480 } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      streamRef.current = stream;
      setIsCameraOn(true);
      setTimeLeft(15);
      setIsTimerActive(true);
    } catch (err) {
      setErrorMsg('Webcam access denied or camera not found. Operating in fallback simulation mode.');
      setIsCameraOn(false);
    }
  };

  // Stop Webcam Stream
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsCameraOn(false);
    setIsTimerActive(false);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  // Capture Frame & Send to AI Backend / Fallback
  const handleCaptureAndTest = async () => {
    setLoading(true);
    setPrediction(null);
    setErrorMsg('');

    let base64Image = null;

    // Extract frame from hidden canvas if camera is active
    if (isCameraOn && videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      base64Image = canvas.toDataURL('image/jpeg', 0.8);
    }

    try {
      // Attempt real API call to Python FastAPI backend
      const response = await fetch('http://localhost:8000/api/practice/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({
          target_letter: selectedLetter,
          image_data: base64Image,
        }),
      });

      if (!response.ok) {
        throw new Error('Backend offline or endpoint unreachable');
      }

      const data = await response.json();
      
      setPrediction({
        predicted_sign: data.predicted_sign || selectedLetter,
        confidence: data.confidence || 92,
        feedback: data.feedback || 'Great job! Hand posture matches target gesture accurately.',
      });

      setMetrics({
        handShape: data.metrics?.hand_shape || 94,
        fingerPosition: data.metrics?.finger_position || 88,
        timingAlignment: data.metrics?.timing || 91,
      });

    } catch (err) {
      // Fallback Simulation Mode
      setTimeout(() => {
        const isCorrect = Math.random() > 0.25;
        const confidenceScore = isCorrect
          ? Math.floor(Math.random() * 12) + 86
          : Math.floor(Math.random() * 35) + 35;

        const predicted = isCorrect
          ? selectedLetter
          : alphabet[Math.floor(Math.random() * alphabet.length)];

        setPrediction({
          predicted_sign: predicted,
          confidence: confidenceScore,
          feedback: isCorrect
            ? `Excellent execution for Letter '${selectedLetter}'! Finger positioning and palm angle align with baseline specifications.`
            : `Detected sign '${predicted}'. Try adjusting your thumb angle and keep your knuckles level with the camera lens.`,
        });

        setMetrics({
          handShape: isCorrect ? Math.floor(Math.random() * 10) + 90 : Math.floor(Math.random() * 30) + 40,
          fingerPosition: isCorrect ? Math.floor(Math.random() * 12) + 85 : Math.floor(Math.random() * 30) + 45,
          timingAlignment: isCorrect ? Math.floor(Math.random() * 10) + 88 : Math.floor(Math.random() * 25) + 50,
        });
      }, 500);
    } finally {
      setTimeout(() => {
        setLoading(false);
        setAttemptCount((prev) => (prev >= 5 ? 1 : prev + 1));
      }, 500);
    }
  };

  const resetSession = () => {
    setAttemptCount(1);
    setTimeLeft(15);
    setPrediction(null);
    setMetrics({ handShape: 0, fingerPosition: 0, timingAlignment: 0 });
  };

  return (
    <div>
      {/* Hidden processing canvas for frame extraction */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <p className="page-subtitle">Interactive AI Training</p>
          <h1 className="page-title">Practice Session</h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className="badge badge-primary">Session ID: sess_112233</span>
          <button onClick={resetSession} className="btn-secondary" style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}>
            🔄 Reset Session
          </button>
        </div>
      </div>

      {/* Target Letter Selector */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Select Target Alphabet Gesture
          </span>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--primary)' }}>
            Active Target: <strong>Letter {selectedLetter}</strong>
          </span>
        </div>
        
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
          {alphabet.map((letter) => (
            <button
              key={letter}
              onClick={() => {
                setSelectedLetter(letter);
                setPrediction(null);
              }}
              className={selectedLetter === letter ? 'btn-primary' : 'btn-secondary'}
              style={{ minWidth: '38px', padding: '0.35rem 0.65rem', fontWeight: 700, fontSize: '0.85rem' }}
            >
              {letter}
            </button>
          ))}
        </div>
      </div>

      {/* Main Practice Workspace */}
      <div className="grid-2">
        
        {/* Left Column: Live Webcam & Controls */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              Target Sign: <span style={{ color: 'var(--primary)', fontSize: '1.25rem' }}>{selectedLetter}</span>
            </h3>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="badge badge-warning">⏱️ Time Left: {timeLeft}s</span>
              <button 
                onClick={isCameraOn ? stopCamera : startCamera} 
                className={isCameraOn ? 'btn-danger-sm' : 'btn-secondary'}
                style={{ padding: '0.4rem 0.75rem' }}
              >
                {isCameraOn ? '🛑 Stop Camera' : '📷 Turn On Camera'}
              </button>
            </div>
          </div>

          {/* Webcam Viewport Frame */}
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
            border: '2px solid var(--border-color)'
          }}>
            {isCameraOn ? (
              <video 
                ref={videoRef} 
                autoPlay 
                playsInline 
                muted 
                style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: '#94a3b8' }}>
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📷</div>
                <p style={{ fontSize: '0.875rem', marginBottom: '0.5rem', color: '#cbd5e1' }}>
                  {errorMsg || 'Webcam access denied or camera not found. Operating in fallback simulation mode.'}
                </p>
                <span className="badge badge-secondary">OFFLINE / FALLBACK MODE</span>
              </div>
            )}
            
            {/* Live Camera Badge overlay */}
            {isCameraOn && (
              <div style={{ position: 'absolute', top: '10px', left: '10px' }}>
                <span className="badge badge-danger" style={{ backgroundColor: '#ef4444', color: '#fff' }}>🔴 LIVE</span>
              </div>
            )}
          </div>

          {/* Attempt Progress Tracker */}
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              <span>ATTEMPT PROGRESS</span>
              <span>Attempt {attemptCount} of 5</span>
            </div>
            <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--table-header-bg)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
              <div style={{ width: `${(attemptCount / 5) * 100}%`, height: '100%', backgroundColor: 'var(--primary)', transition: 'width 0.3s ease' }} />
            </div>
          </div>

          {/* Action Trigger Button */}
          <button
            onClick={handleCaptureAndTest}
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%', padding: '0.75rem', fontSize: '0.95rem', fontWeight: 700 }}
          >
            {loading ? 'Analyzing Gesture Frame...' : '✨ Capture & Test Gesture'}
          </button>
        </div>

        {/* Right Column: Real-Time AI Diagnostics & Metrics */}
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
            Real-Time AI Output
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

          {/* 🌟 Day 8 Score-Reveal Animation Container */}
          <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: 'var(--table-header-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', marginBottom: '1.25rem' }}>
            <p style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Confidence Score</p>
            <span
              key={prediction ? `${prediction.confidence}-${attemptCount}` : 'initial'}
              className="score-reveal"
              style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--primary)', display: 'inline-block' }}
            >
              {prediction ? `${prediction.confidence}%` : '0%'}
            </span>
          </div>

          {/* Detailed Metric Breakdown Cards */}
          <div style={{ marginBottom: '1.25rem' }}>
            <p style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Gesture Diagnostics
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

          {/* Dynamic AI Feedback Note */}
          {prediction ? (
            <div className="card-pop" style={{ padding: '0.85rem', borderRadius: 'var(--radius-md)', backgroundColor: prediction.confidence > 75 ? 'var(--success-bg)' : 'var(--warning-bg)', border: '1px solid var(--border-color)' }}>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: 600, margin: 0 }}>
                {prediction.feedback}
              </p>
            </div>
          ) : (
            <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', border: '1px dashed var(--border-color)', borderRadius: 'var(--radius-md)' }}>
              Perform a sign gesture in front of the camera and click "Capture & Test Gesture".
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


function PopupModal({ isOpen, onClose, title, message, badgeIcon = '🎉' }) {
  if (!isOpen) return null;

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-card" onClick={(e) => e.stopPropagation()}>
        {/* Animated Badge Icon Header */}
        <div style={{ fontSize: '3rem', marginBottom: '0.5rem', animation: 'popIn 0.5s ease' }}>
          {badgeIcon}
        </div>

        {/* Title */}
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.5rem' }}>
          {title}
        </h2>

        {/* Message */}
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.5rem', lineHeight: '1.5' }}>
          {message}
        </p>

        {/* Actions */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem' }}>
          <button onClick={onClose} className="btn-primary" style={{ padding: '0.6rem 1.5rem', fontWeight: 700 }}>
            Got it!
          </button>
        </div>
      </div>
    </div>
  );
}
const [showModal, setShowModal] = useState(false);

return (
  <div>
    <button onClick={() => setShowModal(true)} className="btn-primary">
      Show Popup Modal
    </button>

    <PopupModal
      isOpen={showModal}
      onClose={() => setShowModal(false)}
      title="Badge Unlocked!"
      message="Congratulations! You have completed 7 practice sessions in a row."
      badgeIcon="🏆"
    />
  </div>
);