import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import Spinner from '../Common/Spinner'; // import کردن اسپینر
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
  const [errors, setErrors] = useState({}); // برای نمایش خطاهای هر فیلد
  const [message, setMessage] = useState(''); // برای نمایش پیام کلی
  const [loading, setLoading] = useState(false);
  const [showSpinner, setShowSpinner] = useState(false); // state برای نمایش اسپینر
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // پاک کردن خطای فیلد وقتی کاربر شروع به تایپ کرد
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setErrors({});
    
    // اعتبارسنجی سمت فرانت‌اند
    let formErrors = {};
    if (!formData.first_name) {
      formErrors.first_name = 'نام الزامی است';
    }
    if (!formData.last_name) {
      formErrors.last_name = 'نام خانوادگی الزامی است';
    }
    if (!formData.phone) {
      formErrors.phone = 'شماره تلفن الزامی است';
    } else if (!/^\d{11}$/.test(formData.phone)) {
      formErrors.phone = 'شماره تلفن باید 11 رقمی باشد';
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
    }
    if (formData.password !== formData.password2) {
      formErrors.password2 = 'رمزهای عبور یکسان نیستند';
    }
    
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      setLoading(false);
      return;
    }
    
    try {
      const response = await api.post('/users/register/', 
        formData,
        { withCredentials: true }
      );
      setMessage(response.data.msg || 'ثبت‌نام موفق');
      
      // نمایش اسپینر و رفتن به صفحه وریفای ایمیل
      setShowSpinner(true);
      setTimeout(() => {
        navigate('/verify-email');
      }, 2000);
      
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Register error:', error);
      }
      
      // نمایش خطاهای سمت سرور
      if (error.response?.data) {
        const serverErrors = error.response.data;
        // اگر خطاهای فیلدها باشن
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
          // اگه خطای کلی باشه
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
      {/* نمایش اسپینر */}
      {showSpinner && <Spinner message="در حال انتقال به صفحه وریفای..." />}
      
      <div className="register-container">
        {/* بخش ویژگی‌ها */}
        <div className="register-features">
          <h2 className="register-title">ثبت‌نام در سرویس مدیریت شبکه های اجتماعی </h2>
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
                  placeholder="شماره تلفن خود را وارد کنید"
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
                  required
                  disabled={loading}
                  className={errors.email ? 'error-input' : ''}
                />
                {errors.email && (
                  <div className="field-error">{errors.email}</div>
                )}
              </div>
              
              <div className="form-group">
                <label htmlFor="password">رمز عبور:</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="رمز عبور خود را وارد کنید"
                  required
                  disabled={loading}
                  className={errors.password ? 'error-input' : ''}
                />
                {errors.password && (
                  <div className="field-error">{errors.password}</div>
                )}
              </div>
              
              <div className="form-group">
                <label htmlFor="password2">تکرار رمز عبور:</label>
                <input
                  type="password"
                  id="password2"
                  name="password2"
                  value={formData.password2}
                  onChange={handleChange}
                  placeholder="تکرار رمز عبور خود را وارد کنید"
                  required
                  disabled={loading}
                  className={errors.password2 ? 'error-input' : ''}
                />
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