import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import Spinner from '../Common/Spinner';
import './Register.css';

const Register = () => {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    email: '',
    password: '',
    password2: ''
  });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSpinner, setShowSpinner] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showPassword2, setShowPassword2] = useState(false);
  const navigate = useNavigate();

  // تشخیص کاراکتر فارسی/عربی
  const isPersianChar = (char) => {
    const code = char.charCodeAt(0);
    return (code >= 1570 && code <= 1740) || code === 8204 || code === 8205;
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
      strength = 60;
      label = 'متوسط';
      color = '#ffc107'; // زرد
    } else {
      strength = 20;
      label = 'ضعیف';
      color = '#dc3545'; // قرمز
    }

    return { label, width: strength, color };
  };

  const strength = getPasswordStrength(formData.password);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // پاک کردن خطا وقتی کاربر تایپ می‌کنه
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
      setErrors(prev => ({
        ...prev,
        password: 'لطفاً کیبورد خود را به حالت انگلیسی تغییر دهید'
      }));
    } else if (errors.password) {
      setErrors(prev => ({
        ...prev,
        password: ''
      }));
    }
  };

  const handlePassword2KeyDown = (e) => {
    if (isPersianChar(e.key)) {
      e.preventDefault();
      setErrors(prev => ({
        ...prev,
        password2: 'لطفاً کیبورد خود را به حالت انگلیسی تغییر دهید'
      }));
    } else if (errors.password2) {
      setErrors(prev => ({
        ...prev,
        password2: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setErrors({});

    // ولیدیشن فرانت‌اند
    let formErrors = {};

    if (!formData.first_name) {
      formErrors.first_name = 'نام الزامی است';
    }
    if (!formData.last_name) {
      formErrors.last_name = 'نام خانوادگی الزامی است';
    }
    if (!formData.phone) {
      formErrors.phone = 'شماره تلفن الزامی است';
    } else if (!/^09\d{9}$/.test(formData.phone)) {
      formErrors.phone = 'شماره تلفن نامعتبر است. لطفاً یک شماره معتبر وارد کنید (مثلاً: 09123456789)';
    }
    if (!formData.email) {
      formErrors.email = 'ایمیل الزامی است';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      formErrors.email = 'ایمیل نامعتبر است';
    }
    if (!formData.password) {
      formErrors.password = 'رمز عبور الزامی است';
    } else if (formData.password.length < 8) {
      formErrors.password = 'رمز عبور باید حداقل 8 کاراکتر باشد';
    } else if (/[آ-ی]/.test(formData.password)) {
      formErrors.password = 'رمز عبور نباید شامل کاراکتر فارسی باشد';
    }
    if (formData.password !== formData.password2) {
      formErrors.password2 = 'رمزهای عبور یکسان نیستند';
    } else if (/[آ-ی]/.test(formData.password2)) {
      formErrors.password2 = 'رمز عبور نباید شامل کاراکتر فارسی باشد';
    }

    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      setLoading(false);
      return;
    }

    try {
      const response = await api.post('/users/register/', formData, {
        withCredentials: true
      });
      setMessage(response.data.msg || 'ثبت‌نام موفق');
      setShowSpinner(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Register error:', error);
      }
      if (error.response?.data) {
        const serverErrors = error.response.data;
        if (serverErrors.first_name || serverErrors.last_name || 
            serverErrors.phone || serverErrors.email || 
            serverErrors.password || serverErrors.password2) {
          setErrors({
            first_name: serverErrors.first_name || '',
            last_name: serverErrors.last_name || '',
            phone: serverErrors.phone || '',
            email: serverErrors.email || '',
            password: serverErrors.password || '',
            password2: serverErrors.password2 || ''
          });
        } else {
          const errorMsg = serverErrors.msg || 
                          serverErrors.detail || 
                          serverErrors.reason ||
                          'خطا در ثبت‌نام';
          setMessage(Array.isArray(errorMsg) ? errorMsg[0] : 
                    typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : 
                      errorMsg || 'خطا در ثبت‌نام');
        }
      } else {
        setMessage('خطا در اتصال به سرور. لطفاً اتصال اینترنت خود را بررسی کنید.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-page">
      {showSpinner && <Spinner message="در حال انتقال..." />}

      <div className="register-container">
        {/* بخش ویژگی‌ها */}
        <div className="register-features">
          <h2 className="register-title">ثبت‌نام در سرویس مدیریت شبکه های اجتماعی</h2>
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
        <div className="register-form-section">
          <div className="register-form-wrapper">
            <h3 className="form-title">ثبت‌نام کاربر جدید</h3>

            {message && (
              <div className={`message ${message.includes('خطا') ? 'error' : 'success'}`}>
                {message}
              </div>
            )}

            <form onSubmit={handleSubmit} className="register-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="first_name">نام:</label>
                  <input
                    type="text"
                    id="first_name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    placeholder="نام خود را وارد کنید"
                    required
                    disabled={loading}
                    className={errors.first_name ? 'error-input' : ''}
                  />
                  {errors.first_name && (
                    <div className="field-error">{errors.first_name}</div>
                  )}
                </div>
                <div className="form-group">
                  <label htmlFor="last_name">نام خانوادگی:</label>
                  <input
                    type="text"
                    id="last_name"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleChange}
                    placeholder="نام خانوادگی خود را وارد کنید"
                    required
                    disabled={loading}
                    className={errors.last_name ? 'error-input' : ''}
                  />
                  {errors.last_name && (
                    <div className="field-error">{errors.last_name}</div>
                  )}
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="phone">شماره تلفن:</label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="09123456789"
                  required
                  disabled={loading}
                  className={errors.phone ? 'error-input' : ''}
                />
                {errors.phone && (
                  <div className="field-error">{errors.phone}</div>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="email">ایمیل:</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="ایمیل خود را وارد کنید"
                  dir="ltr"
                  required
                  disabled={loading}
                  className={errors.email ? 'error-input' : ''}
                />
                {errors.email && (
                  <div className="field-error">{errors.email}</div>
                )}
              </div>

              {/* فیلد رمز عبور با دکمه چشم و نوار قدرت */}
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
                    className={errors.password ? 'error-input' : ''}
                    dir="ltr"
                    inputMode="text"
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

                {/* نوار قدرت رمز عبور */}
                {formData.password && (
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
                {formData.password && strength.label === 'ضعیف' && (
                  <div className="password-hint error">
                    رمز عبور خیلی ضعیف است. از ترکیب حروف بزرگ، کوچک، عدد و کاراکتر خاص استفاده کنید.
                  </div>
                )}
                {formData.password && strength.label === 'متوسط' && (
                  <div className="password-hint">
                    رمز عبور متوسط است. رمز باید حاوی کاراکتر های بزرگ و کوچک،اعدادوکاراکتر های خاص مانند @$% باشد.
                  </div>
                )}
                {errors.password && !strength.label && (
                  <div className="field-error">{errors.password}</div>
                )}
              </div>

              {/* فیلد تکرار رمز عبور با دکمه چشم */}
              <div className="form-group password-group">
                <label htmlFor="password2">تکرار رمز عبور:</label>
                <div className="password-input-container">
                  <input
                    type={showPassword2 ? 'text' : 'password'}
                    id="password2"
                    name="password2"
                    value={formData.password2}
                    onChange={handleChange}
                    onKeyDown={handlePassword2KeyDown}
                    placeholder="تکرار رمز عبور خود را وارد کنید"
                    required
                    disabled={loading}
                    className={errors.password2 ? 'error-input' : ''}
                    dir="ltr"
                    inputMode="text"
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword2(prev => !prev)}
                    aria-label={showPassword2 ? 'مخفی کردن رمز عبور' : 'نمایش رمز عبور'}
                  >
                    {showPassword2 ? '👁️‍🗨️' : '🙈'}
                  </button>
                </div>
                {errors.password2 && (
                  <div className="field-error">{errors.password2}</div>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="register-btn"
              >
                {loading ? 'در حال ثبت‌نام...' : 'ثبت‌نام'}
              </button>
            </form>

            <div className="auth-links">
              <p>
                قبلاً حساب کاربری دارید؟{' '}
                <Link to="/login" className="auth-link">ورود به حساب</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;