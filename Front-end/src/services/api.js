// import axios from 'axios';

// const API_BASE_URL = 'http://localhost:8899/api';

// const api = axios.create({
//   baseURL: API_BASE_URL,
//   withCredentials: true,
//   headers: {
//     'Content-Type': 'application/json',
//   },
// });

// // اضافه کردن توکن به درخواست‌ها
// api.interceptors.request.use((config) => {
//   const token = localStorage.getItem('access_token');
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });

// // مدیریت refresh token به صورت خودکار
// api.interceptors.response.use(
//   (response) => response,
//   async (error) => {
//     const originalRequest = error.config;
    
//     // اگر خطای 401 بود و درخواست refresh نبود
//     if (error.response?.status === 401 && !originalRequest._retry) {
//       originalRequest._retry = true;
      
//       try {
//         // درخواست refresh توکن از طریق کوکی
//         const refreshResponse = await axios.post(
//           `${API_BASE_URL}/auth/token/refresh/`,
//           {},
//           { withCredentials: true }
//         );
        
//         // اگر refresh موفق بود، درخواست اصلی رو دوباره ارسال کن
//         return api(originalRequest);
        
//       } catch (refreshError) {
//         // اگر refresh هم ناموفق بود، از حساب کاربری خارج شو
//         console.log('Refresh token expired or invalid, logging out...');
//         window.location.href = '/login';
//       }
//     }
    
//     return Promise.reject(error);
//   }
// );

// export default api;

import axios from 'axios';

const API_BASE_URL = 'http://192.168.1.102:9999/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // مهم: این خط کوکی‌ها رو فعال می‌کنه
  timeout: 10000, // 10 ثانیه timeout
});

// مدیریت refresh token به صورت خودکار
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // اگر خطای 401 بود و درخواست refresh نبود
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // درخواست refresh توکن از طریق کوکی
        await axios.post(
          `${API_BASE_URL}/auth/token/refresh/`,
          {},
          { withCredentials: true } // مهم: این خط کوکی refresh رو می‌فرسته
        );
        
        // اگر refresh موفق بود، درخواست اصلی رو دوباره ارسال کن
        return api(originalRequest);
        
      } catch (refreshError) {
        // اگر refresh هم ناموفق بود، به صفحه لاگین برو
        console.log('Refresh token expired or invalid, logging out...');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;