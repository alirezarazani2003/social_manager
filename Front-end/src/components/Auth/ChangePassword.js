import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import './ChangePassword.css'; // استایل بهتر

const ChangePassword = () => {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  // نمایش رمز عبور
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const navigate = useNavigate();

  // تشخیص کاراکتر فارسی
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

    if (passedChecks === 5 && password.length >= 10) {
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

  // فقط اگر شرایط برقرار باشد، فرم قابل ارسال است
  const isFormValid = () => {
    return (
      strength.label === 'بسیار قوی' &&
      newPassword === confirmPassword
    );
  };

  // ولیدیشن کیبورد فارسی
  const handleOldPasswordKeyDown = (e) => {
    if (isPersianChar(e.key)) {
      e.preventDefault();
      setMessage('لطفاً کیبورد خود را به حالت انگلیسی تغییر دهید');
    } else if (message.includes('کیبورد')) {
      setMessage('');
    }
  };

  const handleNewPasswordKeyDown = (e) => {
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

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    // ولیدیشن فرانت‌اند
    if (!oldPassword) {
      setMessage('رمز عبور فعلی الزامی است');
      setLoading(false);
      return;
    }

    if (/[آ-ی]/.test(oldPassword)) {
      setMessage('رمز عبور فعلی نباید شامل کاراکتر فارسی باشد');
      setLoading(false);
      return;
    }

    if (strength.label !== 'بسیار قوی') {
      setMessage('رمز عبور جدید باید بسیار قوی باشد');
      setLoading(false);
      return;
    }

    if (newPassword !== confirmPassword) {
      setMessage('رمزهای عبور جدید با هم مطابقت ندارند');
      setLoading(false);
      return;
    }

    if (/[آ-ی]/.test(newPassword)) {
      setMessage('رمز عبور جدید نباید شامل کاراکتر فارسی باشد');
      setLoading(false);
      return;
    }

    try {
      const response = await api.post('/auth/change-password/', {
        old_password: oldPassword,
        new_password: newPassword
      });
      setMessage(response.data.msg || 'رمز عبور با موفقیت تغییر کرد');

      // ریست فرم
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowOldPassword(false);
      setShowNewPassword(false);
      setShowConfirmPassword(false);

      // هدایت به داشبورد
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (error) {
      const errorMsg = error.response?.data?.msg || 'خطا در تغییر رمز عبور';
      setMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="change-password-page">
      <div className="change-password-container">
        <h2 className="form-title">تغییر رمز عبور</h2>

        {message && (
          <div className={`message ${message.includes('خطا') || message.includes('کیبورد') ? 'error' : 'success'}`}>
            {message}
          </div>
        )}

        <form onSubmit={handleChangePassword} className="change-password-form">
          {/* فیلد رمز عبور فعلی */}
          <div className="form-group password-group">
            <label htmlFor="old-password">رمز عبور فعلی:</label>
            <div className="password-input-container">
              <input
                type={showOldPassword ? 'text' : 'password'}
                id="old-password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                onKeyDown={handleOldPasswordKeyDown}
                placeholder="رمز عبور فعلی خود را وارد کنید"
                required
                disabled={loading}
                dir="ltr"
                inputMode="text"
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowOldPassword(prev => !prev)}
                aria-label={showOldPassword ? 'مخفی کردن رمز عبور' : 'نمایش رمز عبور'}
              >
                {showOldPassword ? '👁️‍🗨️' : '🙈'}
              </button>
            </div>
          </div>

          {/* فیلد رمز عبور جدید */}
          <div className="form-group password-group">
            <label htmlFor="new-password">رمز عبور جدید:</label>
            <div className="password-input-container">
              <input
                type={showNewPassword ? 'text' : 'password'}
                id="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                onKeyDown={handleNewPasswordKeyDown}
                placeholder="رمز عبور جدید بسیار قوی وارد کنید"
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
                رمز عبور متوسط است. رمز باید حاوی کاراکتر های بزرگ و کوچک،اعدادوکاراکتر های خاص مانند @$% باشد.
              </div>
            )}
          </div>

          {/* فیلد تکرار رمز عبور */}
          <div className="form-group password-group">
            <label htmlFor="confirm-password">تکرار رمز عبور جدید:</label>
            <div className="password-input-container">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirm-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                onKeyDown={handleConfirmPasswordKeyDown}
                placeholder="رمز عبور جدید را دوباره وارد کنید"
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
            {newPassword && confirmPassword && newPassword !== confirmPassword && (
              <div className="field-error">رمزهای عبور با هم مطابقت ندارند</div>
            )}
          </div>

          {/* دکمه‌ها */}
          <div className="form-actions">
            <button
              type="submit"
              disabled={loading || !isFormValid()}
              className="change-password-btn"
            >
              {loading ? 'در حال تغییر...' : 'تغییر رمز عبور'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="cancel-btn"
              disabled={loading}
            >
              انصراف
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangePassword;