import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './MediaGallery.css'; // ایمپورت فایل CSS

const MediaGallery = ({ isOpen, onClose, onMediaSelect, selectedMedia }) => {
  const [mediaFiles, setMediaFiles] = useState([]);
  const [storageInfo, setStorageInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null); // برای نمایش لودینگ روی دکمه حذف
  // مدیریت IDهای انتخاب‌شده در گالری
  const [selectedMediaIds, setSelectedMediaIds] = useState([]);

  // دریافت فایل‌های قبلی و اطلاعات فضا
  useEffect(() => {
    if (isOpen) {
      fetchUserMedia();
      fetchStorageInfo();
      // مقداردهی اولیه انتخاب‌ها از والد
      setSelectedMediaIds(selectedMedia?.map(m => m.id) || []);
    }
  }, [isOpen, selectedMedia]); // وابستگی به selectedMedia برای همگام‌سازی

  const fetchUserMedia = async () => {
    try {
      const response = await api.get('/posts/media/user-media/user_media_list/', {
        withCredentials: true
      });
      setMediaFiles(response.data);
    } catch (error) {
      console.error('Error fetching media:', error);
      // می‌توانید یک پیام خطا به والد بفرستید
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
      // فقط اولین فایل انتخابی آپلود می‌شه (برای سادگی)
      formData.append('file', files[0]);
      
      await api.post('/posts/media/user-media/', formData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      // آپدیت لیست و فضای باقی‌مانده
      fetchUserMedia();
      fetchStorageInfo();
      
    } catch (error) {
      console.error('Error uploading file:', error);
      // می‌توانید یک پیام خطا به کاربر نشان دهید
    } finally {
      setLoading(false);
    }
  };

  // تابع جدید برای حذف فایل
  const handleDeleteMedia = async (mediaId) => {
    if (!window.confirm('آیا از حذف این فایل مطمئن هستید؟')) {
      return; // اگر کاربر کنسل کرد، عملیات متوقف شود
    }

    setDeletingId(mediaId); // شروع لودینگ روی دکمه حذف
    try {
      await api.delete(`/posts/media/user-media/${mediaId}/`, {
        withCredentials: true
      });
      // موفقیت: آپدیت لیست و فضای باقی‌مانده
      fetchUserMedia();
      fetchStorageInfo();
      // اگر فایل حذف‌شده انتخاب‌شده بود، از لیست انتخاب‌ها هم حذف کن
      setSelectedMediaIds(prev => prev.filter(id => id !== mediaId));
      // اگر فایل حذف‌شده در selectedMedia پدر (در PostEditor) هست، باید اونجا هم آپدیت بشه
      // ولی چون MediaGallery مستقله، این کار در PostEditor با useEffect انجام میشه
    } catch (error) {
      console.error('Error deleting media:', error);
      alert('حذف فایل با خطا مواجه شد.');
    } finally {
      setDeletingId(null); // پایان لودینگ
    }
  };


  const handleMediaToggle = (media) => {
    setSelectedMediaIds(prev => {
      if (prev.includes(media.id)) {
        // اگر انتخاب‌شده بود، حذف کن
        return prev.filter(id => id !== media.id);
      } else {
        // اگر انتخاب نشده بود، اضافه کن
        return [...prev, media.id];
      }
    });
  };

  const handleConfirmSelection = () => {
    // پیدا کردن آبجکت‌های کامل مدیاهای انتخاب‌شده
    const selectedMedias = mediaFiles.filter(media => selectedMediaIds.includes(media.id));
    // ارسال آرایه کامل مدیاها به پدر
    onMediaSelect(selectedMedias);
    onClose();
  };

  // اگر پاپ‌آپ باز نیست، چیزی رندر نکن
  if (!isOpen) return null;

  return (
    <div className="media-gallery-overlay">
      <div className="media-gallery-modal">
        {/* هدر پاپ‌آپ */}
        <div className="media-gallery-header">
          <h3>گالری مدیای من</h3>
          <button 
            onClick={onClose}
            className="media-gallery-close-btn"
            aria-label="بستن گالری"
          >
            ×
          </button>
        </div>

        {/* محتوای پاپ‌آپ */}
        <div className="media-gallery-content">
          {/* اطلاعات فضا */}
          {storageInfo && (
            <div className="media-gallery-storage-info">
              <div className="media-gallery-storage-text">
                <span>فضای استفاده‌شده: {storageInfo.used_space_mb} MB</span>
                <span>فضای کل: {storageInfo.total_space_mb} MB</span>
              </div>
              <div className="media-gallery-storage-bar">
                <div 
                  className="media-gallery-storage-fill"
                  style={{ 
                    width: `${storageInfo.used_percentage}%`,
                    backgroundColor: storageInfo.used_percentage > 80 ? '#f44336' : '#4caf50'
                  }}
                />
              </div>
            </div>
          )}

          {/* آپلود جدید */}
          <div className="media-gallery-upload-section">
            <label htmlFor="gallery-upload" className="media-gallery-upload-label">
               آپلود فایل جدید:
            </label>
            <input
              id="gallery-upload"
              type="file"
              onChange={handleFileUpload}
              accept="image/*,video/*,audio/*"
              disabled={loading}
              className="media-gallery-upload-input"
            />
            {loading && <p className="media-gallery-upload-loading">در حال آپلود...</p>}
          </div>

          {/* گالری فایل‌ها */}
          <div className="media-gallery-files-section">
            <h4>فایل‌های من:</h4>
            {mediaFiles.length === 0 ? (
              <p className="media-gallery-empty-message">فایلی یافت نشد. اولین فایل خود را آپلود کنید.</p>
            ) : (
              <div className="media-gallery-grid">
                {mediaFiles.map(media => (
                  <div 
                    key={media.id}
                    className={`media-gallery-item ${selectedMediaIds.includes(media.id) ? 'media-gallery-item-selected' : ''}`}
                  >
                    {/* قسمت قابل کلیک برای انتخاب */}
                    <div 
                      onClick={() => handleMediaToggle(media)}
                      className="media-gallery-item-content"
                    >
                      {media.media_type === 'image' ? (
                        <img 
                          src={media.file_url} 
                          alt={media.title}
                          className="media-gallery-item-image"
                        />
                      ) : (
                        <div className="media-gallery-item-icon">
                          {media.media_type === 'video' ? '🎥' : '📄'}
                        </div>
                      )}
                      <div className="media-gallery-item-title">
                        {media.title}
                      </div>
                    </div>
                    
                    {/* دکمه حذف */}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation(); // جلوگیری از کلیک روی والد (برای انتخاب)
                        handleDeleteMedia(media.id);
                      }}
                      disabled={deletingId === media.id}
                      className="media-gallery-delete-btn"
                      aria-label={`حذف فایل ${media.title}`}
                    >
                      {deletingId === media.id ? '...' : '×'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* فوتر پاپ‌آپ */}
        <div className="media-gallery-footer">
          <button 
            onClick={onClose}
            className="media-gallery-cancel-btn"
          >
            انصراف
          </button>
          <button 
            onClick={handleConfirmSelection}
            disabled={selectedMediaIds.length === 0}
            className={`media-gallery-confirm-btn ${selectedMediaIds.length === 0 ? 'media-gallery-confirm-btn-disabled' : ''}`}
          >
            انتخاب ({selectedMediaIds.length})
          </button>
        </div>
      </div>
    </div>
  );
};

export default MediaGallery;