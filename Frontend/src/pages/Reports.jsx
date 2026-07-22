import React, { useState } from 'react';

export default function Reports() {
  const [downloading, setDownloading] = useState(false);

  const handleDownloadCertificate = async () => {
    setDownloading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/reports/certificate', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Certificate download failed. Check qualification status.');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Sign_Language_Certificate_${localStorage.getItem('username')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert(err.message);
    } finally { setDownloading(false); }
  };

  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
      <h1 style={{ color: '#0f172a' }}>Progress Report & Certificate 🎓</h1>
      <p style={{ color: '#64748b' }}>Review your accomplishments or export your course completion verification certificate.</p>

      <div style={{ background: '#fff', border: '2px dashed #cbd5e1', padding: '40px', borderRadius: '16px', margin: '30px 0' }}>
        <h2 style={{ color: '#2563eb' }}>Official Achievement Certificate</h2>
        <p style={{ fontSize: '18px', margin: '15px 0' }}>Granted to: <strong>{localStorage.getItem('username') || 'Parvathy K Manoj'}</strong></p>
        <p style={{ color: '#64748b' }}>For completing the Alphabets & Gesture Recognition Curriculum with &gt;80% accuracy.</p>
        <button 
          onClick={handleDownloadCertificate} 
          disabled={downloading}
          style={{ background: '#10b981', color: '#fff', border: 'none', padding: '14px 28px', borderRadius: '8px', fontSize: '16px', fontWeight: 'bold', cursor: downloading ? 'not-allowed' : 'pointer', marginTop: '10px' }}
        >
          {downloading ? 'Generating PDF...' : '📄 Download Official Certificate PDF'}
        </button>
      </div>
    </div>
  );
}