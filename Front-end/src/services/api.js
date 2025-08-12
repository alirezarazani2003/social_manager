// api.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // برای ارسال کوکی‌ها
  timeout: 10000, // 10 ثانیه
});

// مدیریت خطاها شامل 401 و 429
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 429) {
      console.warn('Too many requests! Redirecting to warning page...');
      window.location.href = '/warning';
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        await axios.post(
          `${API_BASE_URL}/auth/token/refresh/`,
          {},
          { withCredentials: true }
        );

        // بعد از موفقیت در refresh، درخواست اصلی دوباره ارسال میشه
        return api(originalRequest);
      } catch (refreshError) {
        console.log('Refresh failed, logging out...');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default api;