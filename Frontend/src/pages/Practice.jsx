import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

export default function Practice() {
  const location = useLocation();
  const { lessonId, title, expected } = location.state || { lessonId: 'les_letter_a', title: "The Alphabet Letter 'A'", expected: 'A' };
  
  const [sessionId, setSessionId] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [isPracticing, setIsPracticing] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(document.createElement('canvas'));

  useEffect(() => {
    if (isPracticing) {
      const initSession = async () => {
        try {
          const token = localStorage.getItem('access_token');
          const res = await fetch('http://localhost:8000/api/practice/start', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ lesson_id: lessonId })
          });
          const data = await res.json();
          setSessionId(data.session_id);

          const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
          if (videoRef.current) videoRef.current.srcObject = stream;
          streamRef.current = stream;
        } catch (err) {
          console.error(err);
          alert('Could not start webcam practice tracking session logs.');
          setIsPracticing(false);
        }
      };
      initSession();
    } else {
      stopWebcam();
    }
    return () => stopWebcam();
  }, [isPracticing, lessonId]);

  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  const handleEvaluateSession = async () => {
    if (!videoRef.current || !sessionId) return;
    setEvaluating(true);

    try {
      const token = localStorage.getItem('access_token');
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const base64Image = canvas.toDataURL('image/jpeg').split(',')[1];

      const frameRes = await fetch('http://localhost:8000/api/practice/process-frame', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, frame_data: base64Image })
      });
      const frameData = await frameRes.json();

      const evalRes = await fetch('http://localhost:8000/api/assessment/evaluate', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          expected_gesture: expected,
          predicted_gesture: frameData.predicted_sign,
          confidence: frameData.confidence
        })
      });

      const evalData = await evalRes.json();
      setFeedback(evalData);
    } catch (err) {
      console.error(err);
      alert('Error connecting to assessment engine algorithms.');
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div style={{ padding: '40px', maxWidth: '1100px', margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px' }}>
      <div style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.03)' }}>
        <h2>Active Session: {title}</h2>
        <p style={{ margin: '10px 0 20px 0' }}>Target Sign Objective: <strong style={{ color: '#2563eb' }}>{expected}</strong></p>
        
        <div style={{ width: '100%', height: '340px', background: '#1e293b', borderRadius: '8px', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#cbd5e1' }}>
          {isPracticing ? (
            <video ref={videoRef} autoPlay playsInline style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <div style={{ textAlign: 'center' }}><span style={{ fontSize: '40px' }}>📷</span><p>Webcam turned off.</p></div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '15px', marginTop: '20px' }}>
          <button onClick={() => setIsPracticing(!isPracticing)} style={{ flex: 1, background: isPracticing ? '#ef4444' : '#10b981', color: '#fff', border: 'none', padding: '12px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
            {isPracticing ? "🛑 Stop Practice" : "▶️ Start Practice"}
          </button>
          <button onClick={handleEvaluateSession} disabled={!isPracticing || evaluating} style={{ flex: 1, background: isPracticing && !evaluating ? '#2563eb' : '#94a3b8', color: '#fff', border: 'none', padding: '12px', borderRadius: '6px', cursor: isPracticing ? 'pointer' : 'not-allowed', fontWeight: 'bold' }}>
            {evaluating ? 'Analyzing...' : '🎯 Trigger Live Assessment'}
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ background: '#fff', padding: '20px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.03)', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ width: '60px', height: '60px', background: '#cbd5e1', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', fontWeight: 'bold', color: '#0f172a' }}>{expected}</div>
          <div><h4 style={{ margin: '0 0 4px 0', color: '#0f172a' }}>Reference Visual Guide</h4><p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Imitate this gesture alignment shape.</p></div>
        </div>

        <div style={{ background: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.03)', flex: 1 }}>
          <h3 style={{ color: '#0f172a', margin: '0 0 15px 0' }}>AI Live Metric Evaluations</h3>
          {feedback ? (
            <div style={{ background: feedback.feedback?.is_correct ? '#ecfdf5' : '#fff5f5', padding: '15px', borderRadius: '8px', borderLeft: `5px solid ${feedback.feedback?.is_correct ? '#10b981' : '#ef4444'}` }}>
              <h4 style={{ color: '#0f172a', margin: '0 0 8px 0' }}>Calculated Accuracy Score: {feedback.overall_accuracy}%</h4>
              <div style={{ fontSize: '13px', color: '#475569', margin: '10px 0' }}>
                <div>• Hand Shape Metric: {feedback.metrics?.hand_shape_score}%</div>
                <div>• Finger Position Metric: {feedback.metrics?.finger_position_score}%</div>
              </div>
              <p style={{ color: '#0f172a', fontSize: '14px', margin: '5px 0 0 0' }}><strong>AI Suggestions:</strong> {feedback.feedback?.suggestions?.[0]}</p>
            </div>
          ) : (
            <p style={{ color: '#64748b', marginTop: '15px' }}>Start your camera capture stream and submit to process image arrays live.</p>
          )}
        </div>
      </div>
    </div>
  );
}