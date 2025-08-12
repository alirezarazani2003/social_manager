// pages/ThrottleWarning.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

function ThrottleWarning() {
  const navigate = useNavigate();
  const location = useLocation();

  // خواندن query param ?wait=...
  const queryParams = new URLSearchParams(location.search);
  const serverWait = parseInt(queryParams.get('wait'), 10);
  const waitTime = isNaN(serverWait) ? 120 : serverWait;

  const [timeLeft, setTimeLeft] = useState(waitTime);

  // کاهش زمان هر ثانیه
  useEffect(() => {
    if (timeLeft <= 0) {
      navigate(-1);
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, navigate]);

  const goBack = () => {
    navigate(-1);
  };

  // درصد پیشرفت بار
  const progress = ((waitTime - timeLeft) / waitTime) * 100;

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        {/* آیکون هشدار */}
        <div style={styles.iconContainer}>
          <svg style={styles.icon} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M12 9V13M12 17H12.01M11.94 5.06C9.09 5.22 6.74 6.67 5.18 9.02C3.62 11.38 3.06 14.43 3.64 17.32C4.22 20.21 5.89 22.69 8.26 24H15.74C18.11 22.69 19.78 20.21 20.36 17.32C20.94 14.43 20.38 11.38 18.82 9.02C17.26 6.67 14.91 5.22 12.06 5.06L11.94 5.06Z"
              fill="#c62828"
            />
          </svg>
        </div>

        <h1 style={styles.title}>هشدار ترافیک بالا</h1>
        <p style={styles.message}>
          ترافیک غیرمعمول از سمت شما شناسایی شد.
        </p>
        <p style={styles.subMessage}>
          لطفاً <strong style={{ color: '#c62828' }}>{timeLeft}</strong> ثانیه دیگر صبر کنید.
        </p>

        {/* بار پیشرفت */}
        <div style={styles.progressBarContainer}>
          <div style={{ ...styles.progressBar, width: `${progress}%` }}></div>
        </div>

        {/* دکمه یا پیام */}
        {timeLeft > 0 ? (
          <p style={styles.timer}>بازگشت خودکار در {timeLeft} ثانیه...</p>
        ) : (
          <button onClick={goBack} style={styles.button}>
            بازگشت به صفحه قبل
          </button>
        )}

        <small style={styles.tip}>
          این محدودیت برای حفاظت از سرویس اعمال شده است.
        </small>
      </div>
    </div>
  );
}

const styles = {
  container: {
    direction: 'rtl',
    textAlign: 'center',
    background: 'linear-gradient(135deg, #ffebee 0%, #f3e5f5 100%)',
    minHeight: '100vh',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    margin: 0,
    padding: 0,
    animation: 'fadeIn 0.6s ease-out',
  },

  card: {
    backgroundColor: '#ffffff',
    borderRadius: '20px',
    padding: '40px 30px',
    width: '90%',
    maxWidth: '420px',
    boxShadow: '0 12px 32px rgba(244, 67, 54, 0.2)',
    border: '1px solid #ef9a9a',
    backdropFilter: 'blur(10px)',
    transform: 'scale(1)',
    animation: 'scaleIn 0.5s ease-out',
  },

  iconContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: '20px',
  },

  icon: {
    width: '60px',
    height: '60px',
    color: '#c62828',
  },

  title: {
    margin: '0 0 12px 0',
    fontSize: '1.6rem',
    color: '#c62828',
    fontWeight: '700',
    lineHeight: '1.3',
  },

  message: {
    margin: '0 0 8px 0',
    fontSize: '1.15rem',
    color: '#333',
    lineHeight: '1.5',
  },

  subMessage: {
    margin: '12px 0 24px 0',
    fontSize: '1.05rem',
    color: '#555',
    fontWeight: '500',
  },

  progressBarContainer: {
    width: '100%',
    height: '6px',
    backgroundColor: '#ffe0e0',
    borderRadius: '3px',
    overflow: 'hidden',
    marginBottom: '16px',
  },

  progressBar: {
    height: '100%',
    backgroundColor: '#c62828',
    transition: 'width 1s linear',
    borderRadius: '3px',
  },

  timer: {
    fontSize: '0.95rem',
    color: '#666',
    marginBottom: '16px',
    fontWeight: '500',
  },

  button: {
    backgroundColor: '#c62828',
    color: 'white',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: 'bold',
    marginBottom: '12px',
    transition: 'background-color 0.3s, transform 0.2s',
    boxShadow: '0 4px 10px rgba(198, 40, 40, 0.2)',
  },

  buttonHover: {
    backgroundColor: '#b71c1c',
    transform: 'translateY(-2px)',
  },

  tip: {
    display: 'block',
    marginTop: '16px',
    fontSize: '0.85rem',
    color: '#888',
    lineHeight: '1.4',
  },
};

// استایل‌های CSS درونی برای انیمیشن (میتونی به CSS خارجی منتقلش کنی)
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  @keyframes scaleIn {
    from { transform: scale(0.9); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
  }
  ${Object.keys(styles.button).includes('Hover') ? `[style*="cursor: pointer"] {
    transition: all 0.2s;
  }
  [style*="cursor: pointer"]:hover {
    background-color: ${styles.buttonHover.backgroundColor};
    transform: ${styles.buttonHover.transform};
  }` : ''}
`;
document.head.appendChild(styleSheet);

export default ThrottleWarning;