import React from 'react';
import { useNavigate } from 'react-router-dom';
import './NotFound.css';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className="not-found">
      <div className="not-found-content">
        <h1 className="not-found-title">404</h1>
        <h2 className="not-found-subtitle">صفحه مورد نظر یافت نشد</h2>
        <p className="not-found-message">
          متأسفانه صفحه‌ای که به دنبال آن بودید یافت نشد.
        </p>
        <div className="not-found-actions">
          <button 
            onClick={() => navigate(-1)} 
            className="not-found-btn secondary"
          >
            بازگشت
          </button>
          <button 
            onClick={() => navigate('/')} 
            className="not-found-btn primary"
          >
            رفتن به صفحه اصلی
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotFound;