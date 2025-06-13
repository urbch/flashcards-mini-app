import React, { useEffect } from 'react';
import './Toast.css';

const Toast = ({ id, message, type = 'info', duration = 2000, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(id);
    }, duration);
    return () => clearTimeout(timer);
  }, [id, duration, onClose]);

  return (
    <div className={`toast toast-${type}`}>
      <span>{message}</span>
      <button className="toast-close" onClick={() => onClose(id)}>
        ×
      </button>
    </div>
  );
};

export default Toast;
