import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import Spinner from '../Common/Spinner'; // import کردن اسپینر
import './VerifyEmail.css';

const VerifyEmail = () => {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('request'); // 'request' یا 'verify'
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSpinner, setShowSpinner] = useState(false); // state برای نمایش اسپینر
  const navigate = useNavigate();

  // درخواست کد OTP برای وریفای ایمیل
  const requestOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await api.post('/auth/request-otp/', {
        email,
        purpose: 'verify',
      });

      // پیام موفقیت سرور را نمایش بده
      setMessage(response.data.msg);

      // اگر پیام شامل "ارسال شد" بود، به مرحله بعد برو
      if (response.data.msg.includes('ارسال')) {
        setStep('verify');
      }
    } catch (error) {
      const errorMsg =
        error.response?.data?.msg ||
        error.message ||
        'خطا در ارسال کد وریفای';
      setMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // وریفای کد OTP
  const verifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    if (!/^\d{6}$/.test(otp)) {
      setMessage('کد باید ۶ رقم عددی باشد');
      setLoading(false);
      return;
    }

    try {
      const response = await api.post(
        '/auth/verify-otp/',
        { email, otp, purpose: 'verify' },
        { withCredentials: true }
      );

      setMessage(response.data.msg);

      // نمایش اسپینر و رفتن به داشبورد
      setShowSpinner(true);
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
    } catch (error) {
      const errorMsg =
        error.response?.data?.msg || error.message || 'خطا در وریفای کد';
      setMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="verify-email-page">
      {/* نمایش اسپینر */}
      {showSpinner && <Spinner message="در حال انتقال به داشبورد..." />}
      
      <div className="verify-email-container">
        {/* بخش ویژگی‌ها */}
        <div className="verify-email-features">
          <h2 className="verify-email-title">وریفای ایمیل</h2>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">📧</div>
              <h3>وریفای ایمیل</h3>
              <p>برای استفاده از خدمات، ابتدا باید ایمیل خود را وریفای کنید</p>
            </div>

          </div>
        </div>

        {/* بخش فرم */}
        <div className="verify-email-form-section">
          <div className="verify-email-form-wrapper">
            <h3 className="form-title">وریفای ایمیل</h3>

            {message && (
              <div className={`message ${message.includes('خطا') ? 'error' : 'success'}`}>
                {message}
              </div>
            )}

            {step === 'request' ? (
              <form onSubmit={requestOTP} className="verify-email-form">
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
                <button type="submit" disabled={loading} className="verify-email-btn">
                  {loading ? 'در حال ارسال...' : 'ارسال کد وریفای'}
                </button>
              </form>
            ) : (
              <form onSubmit={verifyOTP} className="verify-email-form">
                <div className="form-group">
                  <label htmlFor="otp">کد ۶ رقمی:</label>
                  <input
                    type="text"
                    id="otp"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="کد ۶ رقمی"
                    maxLength="6"
                    required
                    disabled={loading}
                  />
                </div>
                <button type="submit" disabled={loading} className="verify-email-btn">
                  {loading ? 'در حال وریفای...' : 'وریفای ایمیل'}
                </button>
                <button
                  type="button"
                  onClick={() => setStep('request')}
                  disabled={loading}
                  className="verify-email-btn"
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
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;