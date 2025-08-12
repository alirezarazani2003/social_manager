import React, { useState, useEffect } from 'react';
import api from '../../services/api'; // مسیر واقعی فایل axios شما

const MediaUploader = ({ onFilesChange, currentFiles = [] }) => {
  const [storageInfo, setStorageInfo] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({}); // { fileId: percent }
  const [error, setError] = useState('');
  const [isUploading, setIsUploading] = useState(false); 

  // 🔗 استفاده از API متدهای رجیستر شده در router
  const USER_MEDIA_URL = '/media/user-media/';
  const STORAGE_INFO_URL = `${USER_MEDIA_URL}storage_info/`;

  // --- 1. دریافت اطلاعات فضا ---
  useEffect(() => {
    const fetchStorageInfo = async () => {
      try {
        const res = await api.get(STORAGE_INFO_URL);
        setStorageInfo(res.data);
      } catch (err) {
        console.error('Error fetching storage info:', err);
        setError('خطا در دریافت اطلاعات فضا');
      }
    };
    fetchStorageInfo();
  }, []);

  // --- 2. تبدیل حجم به مگابایت ---
  const bytesToMB = (bytes) => (bytes / (1024 * 1024)).toFixed(2);

  // --- 3. چک کردن فضای کافی ---
  const hasEnoughSpace = (fileSize) => {
    if (!storageInfo) return false;
    return storageInfo.used_space + fileSize <= storageInfo.total_space;
  };

  const isSpaceFull = storageInfo && storageInfo.used_space >= storageInfo.total_space;

  // --- 4. آپلود فایل ---
  const handleFileChange = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0 || isSpaceFull) return;

    // بررسی فضا برای هر فایل
    for (const file of files) {
      if (!hasEnoughSpace(file.size)) {
        setError(`فایل "${file.name}" فضای کافی ندارد.`);
        setTimeout(() => setError(''), 3000);
        return;
      }
    }

    setIsUploading(true);
    const newFiles = [];

    for (const file of files) {
      const fileId = URL.createObjectURL(file);
      setUploadProgress((prev) => ({ ...prev, [fileId]: 0 }));

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await api.post(USER_MEDIA_URL, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress((prev) => ({ ...prev, [fileId]: percent }));
          },
        });

        // ✅ فایل با موفقیت آپلود شد
        const uploadedFile = {
          id: response.data.id,
          name: response.data.file_name || file.name,
          size: file.size,
          file_url: response.data.file,
          uploaded_at: response.data.uploaded_at,
        };

        newFiles.push(uploadedFile);

        // 📦 به‌روزرسانی فضای استفاده‌شده
        setStorageInfo((prev) =>
          prev ? { ...prev, used_space: prev.used_space + file.size } : null
        );

        // 🧹 پاک کردن پیشرفت
        setUploadProgress((prev) => {
          const updated = { ...prev };
          delete updated[fileId];
          return updated;
        });
      } catch (err) {
        const errorMsg = err.response?.data?.error || 'آپلود ناموفق';
        console.error(`Upload failed for ${file.name}:`, errorMsg);
        alert(`"${file.name}": ${errorMsg}`);

        setUploadProgress((prev) => {
          const updated = { ...prev };
          delete updated[fileId];
          return updated;
        });
      }
    }

    // 🚀 به‌روزرسانی لیست فایل‌ها در فرانت
    onFilesChange((prev) => [...prev, ...newFiles]);
    setIsUploading(false);
    e.target.value = null; // پاک کردن input
  };

  // --- 5. حذف فایل ---
  const removeFile = async (fileId) => {
    if (!window.confirm('آیا از حذف این فایل مطمئن هستید؟')) return;

    try {
      await api.delete(`${USER_MEDIA_URL}${fileId}/`);

      // 🔽 حذف از لیست فرانت
      const removedFile = currentFiles.find(f => f.id === fileId);
      onFilesChange((prev) => prev.filter((f) => f.id !== fileId));

      // 🔽 کاهش فضای استفاده‌شده
      if (removedFile && storageInfo) {
        setStorageInfo({
          ...storageInfo,
          used_space: storageInfo.used_space - removedFile.size,
        });
      }

      // 🔽 اگر فایل محلی بود (blob URL)
      if (removedFile.file_url.startsWith('blob:')) {
        URL.revokeObjectURL(removedFile.file_url);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'حذف ناموفق';
      console.error('Error deleting file:', err);
      alert(`حذف فایل ناموفق بود: ${errorMsg}`);
    }
  };

  return (
    <div className="media-uploader">
      {/* نمایش خطا */}
      {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}

      {/* اطلاعات فضا */}
      {storageInfo && (
        <div className="storage-info" style={{ marginBottom: '15px', fontSize: '14px' }}>
          <p>
            فضای استفاده‌شده: {bytesToMB(storageInfo.used_space)} / {bytesToMB(storageInfo.total_space)} مگابایت
          </p>
          <div
            style={{
              width: '100%',
              height: '10px',
              backgroundColor: '#eee',
              borderRadius: '5px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${Math.min((storageInfo.used_space / storageInfo.total_space) * 100, 100)}%`,
                height: '100%',
                backgroundColor:
                  storageInfo.used_space / storageInfo.total_space > 0.9 ? '#dc3545' : '#0d6efd',
                transition: 'width 0.3s ease',
              }}
            ></div>
          </div>
          {isSpaceFull && (
            <p style={{ color: '#dc3545', fontWeight: 'bold', marginTop: '5px' }}>
              ❌ فضای شما پر شده است.
            </p>
          )}
        </div>
      )}

      {/* اینپوت آپلود */}
      <input
        type="file"
        multiple
        onChange={handleFileChange}
        accept="*/*"
        className="file-input"
        disabled={isSpaceFull || isUploading}
        style={{
          display: 'block',
          marginBottom: '10px',
          padding: '8px',
          width: '100%',
          border: '1px solid #ccc',
          borderRadius: '4px',
        }}
      />

      {isUploading && (
        <p style={{ fontSize: '12px', color: '#0d6efd' }}>در حال آپلود فایل‌ها...</p>
      )}

      {/* لیست فایل‌ها */}
      {currentFiles.length > 0 && (
        <div className="uploaded-files" style={{ marginTop: '20px' }}>
          <h5>فایل‌های آپلود شده:</h5>
          <div
            className="files-list"
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            {currentFiles.map((file) => (
              <div
                key={file.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  backgroundColor: '#f9f9f9',
                  fontSize: '14px',
                }}
              >
                <div style={{ flex: 1 }}>
                  <div>{file.name}</div>
                  <small style={{ color: '#666' }}>{bytesToMB(file.size)} MB</small>
                </div>

                {/* نوار پیشرفت */}
                {uploadProgress[file.id] !== undefined ? (
                  <div
                    style={{
                      width: '100px',
                      height: '6px',
                      backgroundColor: '#eee',
                      borderRadius: '3px',
                      overflow: 'hidden',
                      margin: '0 10px',
                    }}
                  >
                    <div
                      style={{
                        width: `${uploadProgress[file.id]}%`,
                        height: '100%',
                        backgroundColor: '#28a745',
                        transition: 'width 0.2s',
                      }}
                    ></div>
                  </div>
                ) : (
                  <span style={{ color: '#28a745', fontSize: '12px' }}>آپلود شد</span>
                )}

                {/* دکمه حذف */}
                <button
                  type="button"
                  onClick={() => removeFile(file.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    fontSize: '1.2rem',
                    cursor: 'pointer',
                    color: '#dc3545',
                    marginLeft: '5px',
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MediaUploader;