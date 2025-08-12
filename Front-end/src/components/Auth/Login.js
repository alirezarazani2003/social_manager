import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import './Login.css';
import '../Common/Spinner';

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

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSpinner, setShowSpinner] = useState(false);
  const [showPassword, setShowPassword] = useState(false); // برای دکمه چشم
  const navigate = useNavigate();

  // تشخیص کاراکتر فارسی
  const isPersianChar = (char) => {
    const code = char.charCodeAt(0);
    return (code >= 1570 && code <= 1740) || code === 8204 || code === 8205;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // پاک کردن خطای فیلد وقتی کاربر تایپ می‌کنه
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handlePasswordKeyDown = (e) => {
    if (isPersianChar(e.key)) {
      e.preventDefault();
      setMessage('لطفاً کیبورد خود را به حالت انگلیسی تغییر دهید');
    } else if (message.includes('کیبورد')) {
      setMessage('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setErrors({});

    // ولیدیشن فرانت‌اند
    let formErrors = {};

    if (!formData.email) {
      formErrors.email = 'ایمیل الزامی است';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      formErrors.email = 'ایمیل نامعتبر است';
    }

    if (!formData.password) {
      formErrors.password = 'رمز عبور الزامی است';
    } else if (formData.password.length < 8) {
      formErrors.password = 'رمز عبور باید حداقل ۸ کاراکتر باشد';
    } else if (/[آ-ی]/.test(formData.password)) {
      formErrors.password = 'رمز عبور نباید شامل کاراکتر فارسی باشد';
    }

    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post(
        process.env.REACT_APP_LOGIN_URL,
        formData,
        { withCredentials: true }
      );

      if (response.status === 200) {
        setMessage(response.data.message || 'ورود موفق');
        setShowSpinner(true);
        setTimeout(() => {
          navigate('/dashboard');
        }, 1500);
      }
    } catch (error) {
      setLoading(false);
      const status = error.response?.status;
      if (status === 429) {
      setMessage('تعداد درخواست‌ها بیش از حد مجاز است. لطفاً کمی صبر کنید.');
      navigate('/warning', {
        state: {
          message: 'تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً صبر کنید.',
          email: formData.email
        }
      });
      return;
    }
      if (status === 401) {
        const errorMsg = error.response?.data?.message || 'ورود ناموفق بود.';
        if (errorMsg.includes('وریفای') || errorMsg.includes('verify')) {
          setMessage(errorMsg || 'لطفاً ایمیل خود را وریفای کنید');
          setShowSpinner(true);
          setTimeout(() => {
            navigate('/verify-email', {
              state: {
                email: formData.email,
                message: errorMsg || 'لطفاً ایمیل خود را وریفای کنید'
              }
            });
          }, 2000);
          return;
        } else {
          setErrors({ general: errorMsg });
        }
      } else if (status === 400) {
        setErrors({ general: 'ایمیل یا رمز عبور اشتباه است.' });
      } else {
        setErrors({ general: 'خطایی رخ داده است. لطفاً دوباره تلاش کنید.' });
      }
    }
  };

  return (
    <div className="login-page">
      {showSpinner && <Spinner message="در حال انتقال به صفحه بعد..." />}

      <div className="login-container">
        <div className="login-features">
          <h2 className="login-title">به سرویس مدیریت شبکه های اجتماعی خوش آمدید!</h2>
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

        <div className="login-form-section">
          <div className="login-form-wrapper">
            <h3 className="form-title">ورود به حساب کاربری</h3>

            {message && (
              <div className={`message ${message.includes('خطا') || message.includes('وریفای') ? 'error' : 'success'}`}>
                {message}
              </div>
            )}

            {errors.general && (
              <div className="message error">{errors.general}</div>
            )}

            <form onSubmit={handleSubmit} className="login-form">
              <div className="form-group">
                <label htmlFor="email">ایمیل:</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="ایمیل خود را وارد کنید"
                  required
                  disabled={loading}
                  dir="ltr"
                  className={errors.email ? 'error-input' : ''}
                />
                {errors.email && (
                  <div className="field-error">{errors.email}</div>
                )}
              </div>

              <div className="form-group password-group">
                <label htmlFor="password">رمز عبور:</label>
                <div className="password-input-container">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    onKeyDown={handlePasswordKeyDown}
                    placeholder="رمز عبور خود را وارد کنید"
                    required
                    disabled={loading}
                    dir="ltr"
                    inputMode="text"
                    className={errors.password ? 'error-input' : ''}
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword(prev => !prev)}
                    aria-label={showPassword ? 'مخفی کردن رمز عبور' : 'نمایش رمز عبور'}
                  >
                    {showPassword ? '👁️‍🗨️' : '🙈'}
                  </button>
                </div>
                {errors.password && (
                  <div className="field-error">{errors.password}</div>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="login-btn"
              >
                {loading ? 'در حال ورود...' : 'ورود'}
              </button>
            </form>

            <div className="auth-links">
              <p>
                حساب کاربری ندارید؟{' '}
                <Link to="/register" className="auth-link">ثبت‌نام کنید</Link>
              </p>
              <p>
                رمز عبور خود را فراموش کرده‌اید؟{' '}
                <Link to="/reset-password" className="auth-link">بازیابی رمز عبور</Link>
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

export default Login;