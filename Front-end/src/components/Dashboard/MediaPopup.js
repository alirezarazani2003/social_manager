import React from 'react';
import { createPortal } from 'react-dom';

const MediaPopup = ({ post, onClose }) => {
  const attachments = post.attachments || [];

  const renderMedia = (attachment, index) => {
    const fileUrl = attachment.file;
    const fileType = fileUrl?.split('.').pop().toLowerCase();

    if (!fileUrl) return null;

    if (['jpg', 'jpeg', 'png', 'gif'].includes(fileType)) {
      return <img src={fileUrl} alt={`media-${index}`} className="media-image" />;
    }

    if (['mp4', 'webm', 'ogg'].includes(fileType)) {
      return <video src={fileUrl} controls className="media-video" />;
    }

    if (['mp3', 'wav', 'ogg'].includes(fileType)) {
      return <audio src={fileUrl} controls className="media-audio" />;
    }

    // سایر فایل‌ها مثل PDF، ZIP، ...
    return (
      <div className="media-file">
        <div className="media-file-icon">📄</div>
        <a
          href={fileUrl}
          target="_blank"
          rel="noopener noreferrer"
          download
          className="media-download-link"
        >
          دانلود فایل
        </a>
      </div>
    );
  };

  const popupContent = (
    <div className="media-popup-overlay" onClick={onClose}>
      <div className="media-popup-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-popup-btn" onClick={onClose}>×</button>
        <h3>مدیاهای پست {post.id}</h3>
        {attachments.length > 0 ? (
          <div className="media-list">
            {attachments.map((att, index) => (
              <div key={index} className="media-item">
                {renderMedia(att, index)}
              </div>
            ))}
          </div>
        ) : (
          <p>مدیایی یافت نشد.</p>
        )}
      </div>
    </div>
  );

  return popupContent;

};

export default MediaPopup;
