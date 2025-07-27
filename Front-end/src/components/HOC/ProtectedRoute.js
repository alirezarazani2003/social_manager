import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // فقط یه درخواست ساده به /auth/me/ بزن
        // اگه کوکی‌ها درست باشن، احراز هویت می‌شه
        await api.get('/auth/me/', {
          withCredentials: true
        });
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Auth check failed:', error);
        // اگر احراز هویت ناموفق بود، به صفحه لاگین برو
        if (error.response?.status === 401) {
          navigate('/login');
        }
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [navigate]);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#f5f5f5'
      }}>
        <div style={{
          padding: '20px',
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          در حال بررسی احراز هویت...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // چون navigate انجام شده
  }

  return children;
};

export default ProtectedRoute;