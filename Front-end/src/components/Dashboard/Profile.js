import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import './Profile.css';

const Profile = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    email: ''
  });
  const navigate = useNavigate();

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await api.get('/auth/me/', {
        withCredentials: true
      });
      setUser(response.data);
      setFormData({
        first_name: response.data.first_name,
        last_name: response.data.last_name,
        phone: response.data.phone,
        email: response.data.email
      });
    } catch (error) {
      console.error('Error fetching user profile:', error);
      setMessage('خطا در دریافت اطلاعات کاربری');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setEditing(true);
  };

  const handleCancelEdit = () => {
    setEditing(false);
    // بازگشت به مقادیر اصلی
    if (user) {
      setFormData({
        first_name: user.first_name,
        last_name: user.last_name,
        phone: user.phone,
        email: user.email
      });
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await api.put('/auth/update-profile/', 
        formData,
        { withCredentials: true }
      );
      
      setUser(response.data);
      setEditing(false);
      setMessage('اطلاعات کاربری با موفقیت به‌روز شد');
      
    } catch (error) {
      const errorMsg = error.response?.data?.msg || 
                      error.response?.data?.detail || 
                      'خطا در به‌روزرسانی اطلاعات کاربری';
      setMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout/', {}, {
        withCredentials: true
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      navigate('/login');
    }
  };

  if (loading && !user) {
    return (
      <div className="profile-page">
        <div className="loading">در حال بارگذاری...</div>
      </div>
    );
  }

  return (
    <div className="profile-page">        
        {/* بخش فرم پروفایل */}
        <div className="profile-form-section">
          {/* هدر پروفایل با دکمه‌های برگشت و خروج */}
          <header className="profile-header">
            <div className="header-content">
              <div className="user-info">
                <span className="welcome-text">
                  خوش آمدید، {user?.first_name} {user?.last_name}
                </span>
                <div className="user-actions">
                  <button 
                    onClick={() => navigate('/dashboard')}
                    className="dashboard-btn"
                  >
                    داشبورد
                  </button>
                  <button 
                    onClick={handleLogout}
                    className="logout-btn"
                  >
                    خروج
                  </button>
                </div>
              </div>
            </div>
          </header>
          
          <div className="profile-form-wrapper">
            <h3 className="form-title">اطلاعات کاربری</h3>
            
            {message && (
              <div className={`message ${message.includes('خطا') ? 'error' : 'success'}`}>
                {message}
              </div>
            )}
            
            {editing ? (
              <form onSubmit={handleSave} className="profile-form">
                <div className="form-group">
                  <label htmlFor="first_name">نام:</label>
                  <input
                    type="text"
                    id="first_name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    required
                    disabled={loading}
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="last_name">نام خانوادگی:</label>
                  <input
                    type="text"
                    id="last_name"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleChange}
                    required
                    disabled={loading}
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="phone">شماره تلفن:</label>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    required
                    disabled={loading}
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="email">ایمیل:</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    disabled={loading}
                  />
                </div>
                
                <div className="form-actions">
                  <button 
                    type="button" 
                    onClick={handleCancelEdit}
                    className="btn btn-secondary"
                    disabled={loading}
                  >
                    انصراف
                  </button>
                  <button 
                    type="submit" 
                    className="btn btn-success"
                    disabled={loading}
                  >
                    {loading ? 'در حال ذخیره...' : 'ذخیره تغییرات'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="profile-info">
                <div>
                  <strong>نام:</strong>
                  <span>{user?.first_name}</span>
                </div>
                
                <div>
                  <strong>نام خانوادگی:</strong>
                  <span>{user?.last_name}</span>
                </div>
                
                <div>
                  <strong>شماره تلفن:</strong>
                  <span>{user?.phone}</span>
                </div>
                
                <div>
                  <strong>ایمیل:</strong>
                  <span>{user?.email}</span>
                </div>
                
                <div>
                  <strong>وضعیت وریفای ایمیل:</strong>
                  <span className={`status-badge ${user?.is_verified ? 'verified' : 'not-verified'}`}>
                    {user?.is_verified ? 'وریفای شده' : 'وریفای نشده'}
                  </span>
                </div>
                
                <div className="form-actions">
                  <button 
                    onClick={() => navigate('/change-password')}
                    className="btn btn-warning"
                  >
                    تغییر رمز عبور
                  </button>
                  <button 
                    onClick={handleEdit}
                    className="btn btn-primary"
                  >
                    ویرایش پروفایل
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>


  );
};

export default Profile;