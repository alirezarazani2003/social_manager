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
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const navigate = useNavigate();

  // تشخیص کاراکتر فارسی/عربی
  const isPersianChar = (char) => {
    const code = char.charCodeAt(0);
    return (code >= 1570 && code <= 1740) || code === 8204 || code === 8205;
  };

  // ولیدیشن ایمیل برای جلوگیری از ورود فارسی
  const handleEmailKeyDown = (e) => {
    if (isPersianChar(e.key)) {
      e.preventDefault();
      setMessage('لطفاً کیبورد خود را به حالت انگلیسی تغییر دهید');
    } else if (message.includes('کیبورد')) {
      setMessage('');
    }
  };

  // ولیدیشن رمز عبور برای جلوگیری از فارسی
  const handlePasswordKeyDown = (e) => {
    if (isPersianChar(e.key)) {
      e.preventDefault();
      setMessage('لطفاً کیبورد خود را به حالت انگلیسی تغییر دهید');
    } else if (message.includes('کیبورد')) {
      setMessage('');
    }
  };

  const handleConfirmPasswordKeyDown = (e) => {
    if (isPersianChar(e.key)) {
      e.preventDefault();
      setMessage('لطفاً کیبورد خود را به حالت انگلیسی تغییر دهید');
    } else if (message.includes('کیبورد')) {
      setMessage('');
    }
  };

  // تابع ارزیابی قدرت رمز عبور
  const getPasswordStrength = (password) => {
    if (password === '') return { label: '', width: 0, color: '' };

    const checks = {
      length: password.length >= 8,
      lower: /[a-z]/.test(password),
      upper: /[A-Z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    };

    const passedChecks = Object.values(checks).filter(Boolean).length;

    let strength = 0;
    let label = '';
    let color = '';

    if (passedChecks === 5 && password.length >= 8) {
      strength = 100;
      label = 'بسیار قوی';
      color = '#28a745'; // سبز
    } else if (passedChecks >= 3) {
      strength = 50;
      label = 'متوسط';
      color = '#ffc107'; // زرد
    } else {
      strength = 20;
      label = 'ضعیف';
      color = '#dc3545'; // قرمز
    }

    return { label, width: strength, color };
  };

  const strength = getPasswordStrength(newPassword);

  // فقط اگر رمز "بسیار قوی" باشد، فرم قابل ارسال است
  const isPasswordValid = () => {
    return (
      newPassword.length >= 8 &&
      confirmPassword === newPassword &&
      strength.label === 'بسیار قوی'
    );
  };

  // مرحله 1: درخواست کد OTP
  const requestResetOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    if (!email) {
      setMessage('لطفاً ایمیل خود را وارد کنید');
      setLoading(false);
      return;
    }

    const emailRegex = /\S+@\S+\.\S+/;
    if (!emailRegex.test(email)) {
      setMessage('آدرس ایمیل نامعتبر است');
      setLoading(false);
      return;
    }

    // جلوگیری از ورود فارسی در ایمیل
    if (/[آ-ی]/.test(email)) {
      setMessage('ایمیل نباید شامل کاراکتر فارسی باشد');
      setLoading(false);
      return;
    }

    try {
      const response = await api.post('/auth/request-reset-otp/', { email });
      setMessage(response.data.msg || 'کد بازیابی به ایمیل شما ارسال شد');
      setStep('reset');
    } catch (error) {
      const errorMsg = error.response?.data?.msg || 'خطا در ارسال کد بازیابی. لطفاً دوباره تلاش کنید.';
      setMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // مرحله 2: تغییر رمز عبور
  const resetPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    if (strength.label !== 'بسیار قوی') {
      setMessage('رمز عبور باید بسیار قوی باشد');
      setLoading(false);
      return;
    }

    if (newPassword !== confirmPassword) {
      setMessage('رمزهای عبور با هم مطابقت ندارند');
      setLoading(false);
      return;
    }

    // جلوگیری از ورود فارسی در رمز عبور
    if (/[آ-ی]/.test(newPassword)) {
      setMessage('رمز عبور نباید شامل کاراکتر فارسی باشد');
      setLoading(false);
      return;
    }

    try {
      const response = await api.post('/auth/reset-password/', {
        email,
        otp,
        new_password: newPassword,
      });
      setMessage(response.data.msg || 'رمز عبور با موفقیت تغییر کرد');

      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (error) {
      const errorMsg = error.response?.data?.msg || 'خطا در تغییر رمز عبور. لطفاً دوباره تلاش کنید.';
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

        {/* فرم */}
        <div className="reset-password-form-section">
          <div className="reset-password-form-wrapper">
            <h3 className="form-title">بازیابی رمز عبور</h3>

            {message && (
              <div className={`message ${message.includes('خطا') || message.includes('مشکل') || message.includes('کیبورد') ? 'error' : 'success'}`}>
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
                    onKeyDown={handleEmailKeyDown}
                    placeholder="example@email.com"
                    required
                    disabled={loading}
                    dir="ltr"
                    inputMode="text"
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
                    placeholder="123456"
                    maxLength="6"
                    required
                    disabled={loading}
                    dir="ltr"
                  />
                </div>

                {/* فیلد رمز عبور جدید با دکمه چشم */}
                <div className="form-group password-group">
                  <label htmlFor="new-password">رمز عبور جدید:</label>
                  <div className="password-input-container">
                    <input
                      type={showNewPassword ? 'text' : 'password'}
                      id="new-password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      onKeyDown={handlePasswordKeyDown}
                      placeholder="رمز عبور بسیار قوی وارد کنید"
                      required
                      disabled={loading}
                      dir="ltr"
                      inputMode="text"
                    />
                    <button
                      type="button"
                      className="password-toggle-btn"
                      onClick={() => setShowNewPassword(prev => !prev)}
                      aria-label={showNewPassword ? 'مخفی کردن رمز عبور' : 'نمایش رمز عبور'}
                    >
                      {showNewPassword ? '👁️‍🗨️' : '🙈'}
                    </button>
                  </div>

                  {/* نوار قدرت رمز عبور */}
                  {newPassword && (
                    <div className="password-strength-container">
                      <div
                        className="password-strength-bar"
                        style={{
                          width: `${strength.width}%`,
                          backgroundColor: strength.color,
                        }}
                      ></div>
                      <div className="password-strength-label" style={{ color: strength.color }}>
                        {strength.label}
                      </div>
                    </div>
                  )}

                  {/* پیام راهنما */}
                  {newPassword && strength.label === 'ضعیف' && (
                    <div className="password-hint error">
                      رمز عبور خیلی ضعیف است. از ترکیب حروف بزرگ، کوچک، عدد و کاراکتر خاص استفاده کنید.
                    </div>
                  )}
                  {newPassword && strength.label === 'متوسط' && (
                    <div className="password-hint">
                      رمز عبور متوسط است. رمز باید حاوی کاراکتر های بزرگ و کوچک، اعداد و کاراکتر های خاص مانند @$% باشد.
                    </div>
                  )}
                </div>

                {/* فیلد تکرار رمز عبور با دکمه چشم */}
                <div className="form-group password-group">
                  <label htmlFor="confirm-password">تکرار رمز عبور:</label>
                  <div className="password-input-container">
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      id="confirm-password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      onKeyDown={handleConfirmPasswordKeyDown}
                      placeholder="تکرار رمز عبور"
                      required
                      disabled={loading}
                      dir="ltr"
                      inputMode="text"
                    />
                    <button
                      type="button"
                      className="password-toggle-btn"
                      onClick={() => setShowConfirmPassword(prev => !prev)}
                      aria-label={showConfirmPassword ? 'مخفی کردن رمز عبور' : 'نمایش رمز عبور'}
                    >
                      {showConfirmPassword ? '👁️‍🗨️' : '🙈'}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading || !isPasswordValid()}
                  className="reset-password-btn"
                >
                  {loading ? 'در حال تغییر...' : 'تغییر رمز عبور'}
                </button>

                <button
                  type="button"
                  onClick={requestResetOTP}
                  disabled={loading}
                  className="reset-password-btn resend-btn"
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