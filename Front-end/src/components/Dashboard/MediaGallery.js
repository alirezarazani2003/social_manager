// src/components/Dashboard/MediaGallery.js
import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './MediaGallery.css'; // اضافه کردن CSS جدا

const MediaGallery = ({ isOpen, onClose, onMediaSelect, selectedMedia }) => {
  const [mediaFiles, setMediaFiles] = useState([]);
  const [storageInfo, setStorageInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedMediaIds, setSelectedMediaIds] = useState([]);

  useEffect(() => {
    if (isOpen) {
      fetchUserMedia();
      fetchStorageInfo();
      setSelectedMediaIds(selectedMedia?.map(m => m.id) || []);
    }
  }, [isOpen, selectedMedia]);

  const fetchUserMedia = async () => {
    try {
      const response = await api.get('/posts/media/user-media/user_media_list/', {
        withCredentials: true
      });
      setMediaFiles(response.data);
    } catch (error) {
      console.error('Error fetching media:', error);
    }
  };

  const fetchStorageInfo = async () => {
    try {
      const response = await api.get('/posts/media/user-media/storage_info/', {
        withCredentials: true
      });
      setStorageInfo(response.data);
    } catch (error) {
      console.error('Error fetching storage info:', error);
    }
  };

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', files[0]);
      
      await api.post('/posts/media/user-media/', formData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      fetchUserMedia();
      fetchStorageInfo();
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMediaToggle = (media) => {
    setSelectedMediaIds(prev => 
      prev.includes(media.id) 
        ? prev.filter(id => id !== media.id) 
        : [...prev, media.id]
    );
  };

  const handleConfirmSelection = () => {
    const selectedMedias = mediaFiles.filter(media => selectedMediaIds.includes(media.id));
    onMediaSelect(selectedMedias);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="media-overlay">
      <div className="media-container">
        <div className="media-header">
          <h3>گالری مدیای من</h3>
          <button onClick={onClose} className="media-close-btn">×</button>
        </div>

        <div className="media-content">
          {storageInfo && (
            <div className="storage-info">
              <div className="storage-text">
                <span>فضای استفاده‌شده: {storageInfo.used_space_mb} MB</span>
                <span>فضای کل: {storageInfo.total_space_mb} MB</span>
              </div>
              <div className="storage-bar">
                <div 
                  className={`storage-progress ${storageInfo.used_percentage > 80 ? 'danger' : 'safe'}`}
                  style={{ width: `${storageInfo.used_percentage}%` }}
                />
              </div>
            </div>
          )}

          <div className="upload-section">
            <label htmlFor="gallery-upload">آپلود فایل جدید:</label>
            <input
              id="gallery-upload"
              type="file"
              onChange={handleFileUpload}
              accept="*/*"
              disabled={loading}
            />
            {loading && <p className="upload-loading">در حال آپلود...</p>}
          </div>

          <div className="media-gallery">
            <h4>فایل‌های من:</h4>
            {mediaFiles.length === 0 ? (
              <p>فایلی یافت نشد. اولین فایل خود را آپلود کنید.</p>
            ) : (
              <div className="media-grid">
                {mediaFiles.map(media => (
                  <div 
                    key={media.id}
                    onClick={() => handleMediaToggle(media)}
                    className={`media-item ${selectedMediaIds.includes(media.id) ? 'selected' : ''}`}
                  >
                    {media.media_type === 'image' ? (
                      <img src={media.file_url} alt={media.title} />
                    ) : (
                      <div className="media-placeholder">
                        {media.media_type === 'video' ? '🎥' : '📄'}
                      </div>
                    )}
                    <div className="media-title">{media.title}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="media-footer">
          <button onClick={onClose} className="cancel-btn">انصراف</button>
          <button 
            onClick={handleConfirmSelection}
            disabled={selectedMediaIds.length === 0}
            className={`confirm-btn ${selectedMediaIds.length === 0 ? 'disabled' : ''}`}
          >
            انتخاب ({selectedMediaIds.length})
          </button>
        </div>
      </div>
    </div>
  );
};

export default MediaGallery;
