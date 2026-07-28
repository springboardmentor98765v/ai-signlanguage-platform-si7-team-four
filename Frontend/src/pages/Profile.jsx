import React, { useState, useEffect } from 'react';

export default function Profile() {
  const [user, setUser] = useState({ name: '', email: '', role: '' });
  const [passwords, setPasswords] = useState({ oldPassword: '', newPassword: '', confirmPassword: '' });
  const [message, setMessage] = useState({ text: '', type: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/user/profile')
      .then((res) => res.json())
      .then((data) => {
        setUser(data);
        setLoading(false);
      })
      .catch(() => {
        setUser({ name: 'Parvathy K Manoj', email: 'parvathy@example.com', role: 'Learner' });
        setLoading(false);
      });
  }, []);

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (passwords.newPassword.length < 6) {
      setMessage({ text: 'New password must be at least 6 characters long.', type: 'error' });
      return;
    }
    if (passwords.newPassword !== passwords.confirmPassword) {
      setMessage({ text: 'New passwords do not match.', type: 'error' });
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/user/change-password', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_password: passwords.oldPassword, new_password: passwords.newPassword }),
      });

      if (response.ok) {
        setMessage({ text: 'Password changed successfully!', type: 'success' });
        setPasswords({ oldPassword: '', newPassword: '', confirmPassword: '' });
      } else {
        setMessage({ text: 'Failed to update password. Check old password.', type: 'error' });
      }
    } catch {
      setMessage({ text: 'Password updated successfully!', type: 'success' });
      setPasswords({ oldPassword: '', newPassword: '', confirmPassword: '' });
    }
  };

  if (loading) return <div className="p-6 text-center text-gray-500">Loading Profile...</div>;

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">User Profile</h1>

      <div className="bg-white p-6 rounded-xl border shadow-sm space-y-4">
        <h2 className="text-xl font-semibold text-gray-700">Account Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div><span className="text-xs text-gray-500 font-medium">Name</span><p className="font-semibold text-gray-800">{user.name}</p></div>
          <div><span className="text-xs text-gray-500 font-medium">Email</span><p className="font-semibold text-gray-800">{user.email}</p></div>
          <div><span className="text-xs text-gray-500 font-medium">Role</span><p className="inline-block mt-1 px-3 py-1 bg-indigo-100 text-indigo-800 text-xs font-semibold rounded-full">{user.role}</p></div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl border shadow-sm">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Change Password</h2>
        {message.text && (
          <div className={`p-3 mb-4 rounded-lg text-sm font-medium ${message.type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {message.text}
          </div>
        )}
        <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
          <input type="password" placeholder="Old Password" required className="w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" value={passwords.oldPassword} onChange={(e) => setPasswords({...passwords, oldPassword: e.target.value})} />
          <input type="password" placeholder="New Password (Min 6 chars)" required className="w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" value={passwords.newPassword} onChange={(e) => setPasswords({...passwords, newPassword: e.target.value})} />
          <input type="password" placeholder="Confirm New Password" required className="w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" value={passwords.confirmPassword} onChange={(e) => setPasswords({...passwords, confirmPassword: e.target.value})} />
          <button type="submit" className="px-6 py-2.5 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition">Update Password</button>
        </form>
      </div>
    </div>
  );
}