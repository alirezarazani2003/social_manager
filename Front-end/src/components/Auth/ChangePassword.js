import React, { useState } from 'react';
import api from '../../services/api';
import { useNavigate } from 'react-router-dom';

const ChangePassword = () => {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleChangePassword = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/auth/change-password/', {
        old_password: oldPassword,
        new_password: newPassword
      });
      setMessage(response.data.msg);
      // پاک کردن فرم
      setOldPassword('');
      setNewPassword('');
      // بعد از موفقیت، به داشبورد برو
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (error) {
      setMessage(error.response?.data?.msg || 'خطا در تغییر رمز');
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '400px', margin: '50px auto' }}>
      <h2>تغییر رمز عبور</h2>
      
      {message && (
        <div style={{ 
          padding: '10px', 
          margin: '10px 0',
          backgroundColor: message.includes('خطا') ? '#ffebee' : '#e8f5e8',
          border: `1px solid ${message.includes('خطا') ? '#f44336' : '#4caf50'}`,
          borderRadius: '4px'
        }}>
          {message}
        </div>
      )}
      
      <form onSubmit={handleChangePassword}>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="password"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            placeholder="رمز عبور فعلی"
            required
            style={{ width: '100%', padding: '10px', boxSizing: 'border-box', marginBottom: '10px' }}
          />
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="رمز عبور جدید"
            required
            style={{ width: '100%', padding: '10px', boxSizing: 'border-box' }}
          />
        </div>
        <button 
          type="submit"
          style={{ padding: '10px 20px', backgroundColor: '#4caf50', color: 'white', border: 'none', borderRadius: '4px', marginRight: '10px' }}
        >
          تغییر رمز
        </button>
        <button 
          type="button" 
          onClick={() => navigate('/dashboard')}
          style={{ padding: '10px 20px', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px' }}
        >
          انصراف
        </button>
      </form>
    </div>
  );
};

export default ChangePassword;