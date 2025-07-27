import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './components/Auth/Login';
import LoginOTP from './components/Auth/LoginOTP';
import Register from './components/Auth/Register';
import ResetPassword from './components/Auth/ResetPassword';
import VerifyEmail from './components/Auth/VerifyEmail'; // اضافه شد
import ChangePassword from './components/Auth/ChangePassword';
import Dashboard from './components/Dashboard/Dashboard';
import ProtectedRoute from './components/HOC/ProtectedRoute';
import './App.css';
import './fonts.css'
import Profile from './components/Dashboard/Profile';
import NotFound from './components/Common/NotFound';
function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/login" element={<Login />} />
          <Route path="/login-otp" element={<LoginOTP />} />
          <Route path="/register" element={<Register />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/verify-email" element={<VerifyEmail />} /> 
          <Route path="/change-password" element={<ChangePassword />} />
          <Route path="/dashboard/*" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;