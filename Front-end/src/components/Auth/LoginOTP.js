import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import './LoginOTP.css';
import '../Common/Spinner.css'; // مسیر رو بر اساس ساختار پروژه‌تون تنظیم کنید

// کامپوننت اسپینر
const Spinner = ({ message = 'در حال انتقال...' }) => {
  return (
    <div className="spinner-overlay">
      <div className="spinner-container">
        <div className="spinner"></div>
        <div className="spinner-text">{message}</div>
      </div>
    </div>
  );
};

const LoginOTP = () => {
  const [step, setStep] = useState('request'); // 'request' یا 'verify'
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSpinner, setShowSpinner] = useState(false); // state برای نمایش اسپینر
  const navigate = useNavigate();

  // مرحله 1: درخواست کد OTP
  const requestOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    
    try {
      const response = await api.post('/auth/request-login-otp/', { 
        email,
        purpose: 'login'
      });
      setMessage(response.data.msg);
      setStep('verify');
    } catch (error) {
      const errorMsg = error.response?.data?.msg || 'خطا در ارسال کد ورود';
      setMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // مرحله 2: ورود با کد OTP
  const loginWithOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    
    try {
      const response = await api.post('/auth/login-with-otp/', 
        { email, otp },
        { withCredentials: true }
      );
      
      setMessage(response.data.msg);
      
      // نمایش اسپینر و رفتن به داشبورد
      setShowSpinner(true);
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
      
    } catch (error) {
      const errorMsg = error.response?.data?.msg || 'خطا در ورود';
      setMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-otp-page">
      {/* نمایش اسپینر */}
      {showSpinner && <Spinner message="در حال انتقال به داشبورد..." />}
      
      <div className="login-otp-container">
        {/* بخش ویژگی‌ها */}
        <div className="login-otp-features">
          <h2 className="login-otp-title">به سرویس مدیریت شبکه های اجتماعی خوش آمدید!</h2>
          
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">📱</div>
              <h3>مدیریت چند پلتفرم</h3>
              <p>ارسال همزمان پست به کانال‌های تلگرام و بله</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">⏱️</div>
              <h3>زمان‌بندی پست‌ها</h3>
              <p>زمان‌بندی ارسال پست‌ها در آینده</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>گزارش‌گیری</h3>
              <p>مشاهده وضعیت ارسال پست‌ها و آمار عملکرد</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>امنیت بالا</h3>
              <p>حفاظت از اطلاعات شما با روش‌های امنیتی پیشرفته</p>
            </div>
          </div>
          
        </div>
        
        {/* بخش فرم */}
        <div className="login-otp-form-section">
          <div className="login-otp-form-wrapper">
            <h3 className="form-title">ورود با کد OTP</h3>
            
            {message && (
              <div className={`message ${message.includes('خطا') ? 'error' : 'success'}`}>
                {message}
              </div>
            )}
            
            {step === 'request' ? (
              <form onSubmit={requestOTP} className="login-otp-form">
                <div className="form-group">
                  <label htmlFor="email">ایمیل:</label>
                  <input
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="ایمیل خود را وارد کنید"
                    dir="ltr"
                    required
                    disabled={loading}
                  />
                </div>
                <button 
                  type="submit"
                  disabled={loading}
                  className="login-otp-btn"
                >
                  {loading ? 'در حال ارسال...' : 'ارسال کد ورود'}
                </button>
              </form>
            ) : (
              <form onSubmit={loginWithOTP} className="login-otp-form">
                <div className="form-group">
                  <label htmlFor="otp">کد 6 رقمی:</label>
                  <input
                    type="text"
                    dir="ltr"
                    id="otp"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="کد 6 رقمی"
                    maxLength="6"
                    required
                    disabled={loading}
                  />
                </div>
                <button 
                  type="submit"
                  disabled={loading}
                  className="login-otp-btn"
                >
                  {loading ? 'در حال ورود...' : 'ورود'}
                </button>
                <button 
                  type="button" 
                  onClick={() => setStep('request')}
                  disabled={loading}
                  className="login-otp-btn"
                  style={{ background: loading ? '#ccc' : '#ff9800' }}
                >
                  ارسال مجدد کد
                </button>
              </form>
            )}
            
            {/* لینک‌های ناوبری */}
            <div className="auth-links">
              <p>
                رمز عبور خود را فراموش کرده‌اید؟{' '}
                <Link to="/reset-password" className="auth-link">بازیابی رمز عبور</Link>
              </p>
              <p>
                حساب کاربری ندارید؟{' '}
                <Link to="/register" className="auth-link">ثبت‌نام کنید</Link>
              </p>
              <p>
                ورود عادی؟{' '}
                <Link to="/login" className="auth-link">ورود با رمز عبور</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginOTP;