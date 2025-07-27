import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import './ResetPassword.css';

const ResetPassword = () => {
  const [step, setStep] = useState('request'); // 'request' یا 'reset'
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // مرحله 1: درخواست کد OTP برای ریست رمز
  const requestResetOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    
    try {
      const response = await api.post('/auth/request-reset-password-otp/', { email });
      setMessage(response.data.msg);
      setStep('reset');
    } catch (error) {
      const errorMsg = error.response?.data?.msg || 'خطا در ارسال کد بازیابی';
      setMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // مرحله 2: ریست رمز با کد OTP
  const resetPassword = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setMessage('رمزهای عبور یکسان نیستند');
      return;
    }
    
    setLoading(true);
    setMessage('');
    
    try {
      const response = await api.post('/auth/reset-password-with-otp/', { 
        email, 
        otp, 
        new_password: newPassword 
      });
      setMessage(response.data.msg);
      // بعد از موفقیت، به صفحه ورود برو
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (error) {
      const errorMsg = error.response?.data?.msg || 'خطا در ریست رمز';
      setMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="reset-password-page">
      <div className="reset-password-container">
        {/* بخش ویژگی‌ها */}
        <div className="reset-password-features">
          <h2 className="reset-password-title">بازیابی رمز عبور</h2>
          
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
        <div className="reset-password-form-section">
          <div className="reset-password-form-wrapper">
            <h3 className="form-title">بازیابی رمز عبور</h3>
            
            {message && (
              <div className={`message ${message.includes('خطا') ? 'error' : 'success'}`}>
                {message}
              </div>
            )}
            
            {step === 'request' ? (
              <form onSubmit={requestResetOTP} className="reset-password-form">
                <div className="form-group">
                  <label htmlFor="email">ایمیل:</label>
                  <input
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="ایمیل خود را وارد کنید"
                    required
                    disabled={loading}
                  />
                </div>
                <button 
                  type="submit"
                  disabled={loading}
                  className="reset-password-btn"
                >
                  {loading ? 'در حال ارسال...' : 'ارسال کد بازیابی'}
                </button>
              </form>
            ) : (
              <form onSubmit={resetPassword} className="reset-password-form">
                <div className="form-group">
                  <label htmlFor="otp">کد 6 رقمی:</label>
                  <input
                    type="text"
                    id="otp"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="کد 6 رقمی"
                    maxLength="6"
                    required
                    disabled={loading}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="new-password">رمز عبور جدید:</label>
                  <input
                    type="password"
                    id="new-password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="رمز عبور جدید"
                    required
                    disabled={loading}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="confirm-password">تکرار رمز عبور:</label>
                  <input
                    type="password"
                    id="confirm-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="تکرار رمز عبور"
                    required
                    disabled={loading}
                  />
                </div>
                <button 
                  type="submit"
                  disabled={loading}
                  className="reset-password-btn"
                >
                  {loading ? 'در حال تغییر...' : 'تغییر رمز عبور'}
                </button>
                <button 
                  type="button" 
                  onClick={() => setStep('request')}
                  disabled={loading}
                  className="reset-password-btn"
                  style={{ background: loading ? '#ccc' : '#ff9800' }}
                >
                  ارسال مجدد کد
                </button>
              </form>
            )}
            
            {/* لینک‌های ناوبری */}
            <div className="auth-links">
              <p>
                به حساب کاربری خود رسیدید؟{' '}
                <Link to="/login" className="auth-link">ورود به حساب</Link>
              </p>
              <p>
                حساب کاربری ندارید؟{' '}
                <Link to="/register" className="auth-link">ثبت‌نام کنید</Link>
              </p>
              <p>
                ورود با کد OTP؟{' '}
                <Link to="/login-otp" className="auth-link">ورود با OTP</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;