import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useNavigate } from 'react-router-dom';
import PostEditor from './PostEditor';
import ChannelList from './ChannelList';
import ScheduledPosts from './ScheduledPosts';
import SentPosts from './SentPosts';
import FailedPosts from './FailedPosts';
import PendingPosts from './PendingPosts';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('editor'); // 'editor', 'scheduled', 'sent', 'failed', 'pending'
  const navigate = useNavigate();

useEffect(() => {
  const fetchUserData = async () => {
    try {
      const response = await api.get('/auth/me/', {
        withCredentials: true
      });
      
      // اگر ایمیل وریفای نشده باشه، به صفحه وریفای برو
      if (!response.data.is_verified) {
        navigate('/verify-email');
        return;
      }
      
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user ', error);
      if (error.response?.status === 401) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  fetchUserData();
}, [navigate]);

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout/', {}, {
        withCredentials: true // مهم: این خط کوکی‌ها رو پاک می‌کنه
      });
    } catch (error) {
      console.error('Logout API error (maybe already logged out):', error);
    } finally {
      // در هر صورت، به صفحه لاگین برو
      navigate('/login');
    }
  };

  if (loading) return <div className="loading">در حال بارگذاری...</div>;

  return (
    <div className="dashboard">
    {/* هدر داشبورد */}
    <header className="dashboard-header" style={{
      background: 'rgba(255, 255, 255, 0.1)',
      backdropFilter: 'blur(10px)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
      padding: '1rem 2rem',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',

    }}>
      <div className="header-content" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        <h1 style={{
          color: 'white',
          margin: 0,
          fontSize: '2rem',
          textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)'
        }}>
          داشبورد کاربر
        </h1>
        <div className="user-info" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <span className="welcome-text" style={{
            color: 'white',
            fontSize: '1.1rem'
          }}>
            خوش آمدید، {user?.first_name} {user?.last_name}
          </span>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button 
              onClick={() => navigate('/profile')}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '25px',
                cursor: 'pointer',
                fontSize: '1rem',
                transition: 'all 0.3s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.3)';
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = 'none';
              }}
            >
              پروفایل
            </button>
            <button 
              onClick={handleLogout}
              className='logout-btn'
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = 'rgba(244, 67, 54, 1)';
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 4px 15px rgba(244, 67, 54, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = 'rgba(244, 67, 54, 0.2)';
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = 'none';
              }}
            >
              خروج
            </button>
          </div>
        </div>
      </div>
    </header>

      <div className="dashboard-content">
        {/* سایدبار با لیست کانال‌ها */}
        <aside className="sidebar">
          <ChannelList />
        </aside>

        {/* محتوای اصلی */}
        <main className="main-content">
          {/* تب‌های ناوبری */}
          <div className="tabs" role="tablist">
            <button 
              role="tab"
              aria-selected={activeTab === 'editor'}
              className={`tab-btn ${activeTab === 'editor' ? 'active' : ''}`}
              onClick={() => setActiveTab('editor')}
            >
              📝 ارسال پست جدید
            </button>
            <button 
              role="tab"
              aria-selected={activeTab === 'pending'}
              className={`tab-btn ${activeTab === 'pending' ? 'active' : ''}`}
              onClick={() => setActiveTab('pending')}
            >
              ⏳ در حال ارسال
            </button>
            <button 
              role="tab"
              aria-selected={activeTab === 'scheduled'}
              className={`tab-btn ${activeTab === 'scheduled' ? 'active' : ''}`}
              onClick={() => setActiveTab('scheduled')}
            >
              ⏰ زمان‌بندی‌شده
            </button>
            <button 
              role="tab"
              aria-selected={activeTab === 'sent'}
              className={`tab-btn ${activeTab === 'sent' ? 'active' : ''}`}
              onClick={() => setActiveTab('sent')}
            >
              ✅ ارسال‌شده
            </button>
            <button 
              role="tab"
              aria-selected={activeTab === 'failed'}
              className={`tab-btn ${activeTab === 'failed' ? 'active' : ''}`}
              onClick={() => setActiveTab('failed')}
            >
              ❌ ناموفق
            </button>
          </div>

          {/* محتوای تب‌ها */}
          <div className="tab-content" role="tabpanel">
            {activeTab === 'editor' && (
              <div className="editor-tab">
                <PostEditor />
              </div>
            )}
            {activeTab === 'pending' && (
              <div className="pending-tab">
                <PendingPosts />
              </div>
            )}
            {activeTab === 'scheduled' && (
              <div className="scheduled-tab">
                <ScheduledPosts />
              </div>
            )}
            {activeTab === 'sent' && (
              <div className="sent-tab">
                <SentPosts />
              </div>
            )}
            {activeTab === 'failed' && (
              <div className="failed-tab">
                <FailedPosts />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;