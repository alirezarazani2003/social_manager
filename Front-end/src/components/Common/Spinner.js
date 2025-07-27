// Spinner.js
import React from 'react';
import './Spinner.css';

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

export default Spinner;