import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useNavigate } from 'react-router-dom';
import PostEditor from './PostEditor';
import ChannelList from './ChannelList';
import ScheduledPosts from './ScheduledPosts';
import SentPosts from './SentPosts';
import FailedPosts from './FailedPosts';
import PendingPosts from './PendingPosts';
import AIChat from './AIchat';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('editor');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false); // برای منوی موبایل
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await api.get('/auth/me/', {
          withCredentials: true
        });
        
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
        withCredentials: true
      });
    } catch (error) {
      console.error('Logout API error (maybe already logged out):', error);
    } finally {
      navigate('/login');
    }
  };

  // بستن سایدبار و منوی موبایل با زدن روی ESC
  useEffect(() => {
    const handleEsc = (event) => {
      if (event.keyCode === 27) {
        setIsSidebarOpen(false);
        setIsMobileMenuOpen(false);
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => {
      window.removeEventListener('keydown', handleEsc);
    };
  }, []);

  // تب‌های داشبورد
  const tabs = [
    { id: 'editor', label: '📝 ارسال پست جدید' },
    { id: 'pending', label: '⏳ در حال ارسال' },
    { id: 'scheduled', label: '⏰ زمان‌بندی‌شده' },
    { id: 'sent', label: '✅ ارسال‌شده' },
    { id: 'failed', label: '❌ ناموفق' },
    { id: 'ai-chat', label: '🤖 چت با هوش مصنوعی' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'editor': return <PostEditor />;
      case 'pending': return <PendingPosts />;
      case 'scheduled': return <ScheduledPosts />;
      case 'sent': return <SentPosts />;
      case 'failed': return <FailedPosts />;
      case 'ai-chat': return <AIChat />;
      default: return <PostEditor />;
    }
  };

  if (loading) return <div className="loading">در حال بارگذاری...</div>;

  return (
    <div className="dashboard">
      {/* هدر داشبورد */}
      <header className="dashboard-header">
        <div className="header-content">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* دکمه همبرگر برای کانال‌ها */}
            <button 
              onClick={() => setIsSidebarOpen(true)}
              className="hamburger-btn"
            >
              ☰
            </button>
            <h1>داشبورد کاربر</h1>
          </div>
          
          <div className="user-info">
            <span className="welcome-text">
              خوش آمدید، {user?.first_name} {user?.last_name}
            </span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                onClick={() => navigate('/profile')}
                className="profile-btn"
              >
                پروفایل
              </button>
              <button 
                onClick={handleLogout}
                className='logout-btn'
              >
                خروج
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="dashboard-content">
        {/* Overlay برای موبایل - کانال‌ها */}
        <div 
          className={`sidebar-overlay ${isSidebarOpen ? 'active' : ''}`}
          onClick={() => setIsSidebarOpen(false)}
        />

        {/* Overlay برای موبایل - منوی تب‌ها */}
        <div 
          className={`mobile-menu-overlay ${isMobileMenuOpen ? 'active' : ''}`}
          onClick={() => setIsMobileMenuOpen(false)}
        />

        {/* سایدبار - کانال‌ها */}
        <aside className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
          <ChannelList />
        </aside>

        {/* محتوای اصلی */}
        <main className="main-content">
          {/* تب‌های ناوبری - دسکتاپ */}
          <div className="tabs-desktop">
            {tabs.map((tab) => (
              <button 
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* دکمه منوی موبایل */}
          <div className="tabs-mobile">
            <button 
              className="mobile-tab-btn"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {tabs.find(tab => tab.id === activeTab)?.label || 'انتخاب تب'}
              <span className="arrow">▼</span>
            </button>
            
            {/* منوی کشویی موبایل */}
            <div className={`mobile-tabs-menu ${isMobileMenuOpen ? 'open' : ''}`}>
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  className={`mobile-tab-item ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setIsMobileMenuOpen(false);
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* محتوای تب‌ها */}
          <div className="tab-content" role="tabpanel">
            {renderTabContent()}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;