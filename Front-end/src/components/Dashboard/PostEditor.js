import React, { useState, useEffect } from 'react';
import api from '../../services/api';
const PostEditor = () => {
  const [channels, setChannels] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [content, setContent] = useState('');
  const [hasMedia, setHasMedia] = useState(false);
  const [isScheduled, setIsScheduled] = useState(false);
  const [scheduledTime, setScheduledTime] = useState('');
  const [mediaFiles, setMediaFiles] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  // دریافت لیست کانال‌ها
  useEffect(() => {
    const fetchChannels = async () => {
      try {
        const response = await api.get('/channels/', {
          withCredentials: true
        });
        
        // چک کردن اینکه آیا response.data یه آبجکت pagination هست یا آرایه
        let channelsData = [];
        if (Array.isArray(response.data)) {
          channelsData = response.data;
        } else if (response.data && Array.isArray(response.data.results)) {
          channelsData = response.data.results;
        } else {
          console.error('Expected array but got:', response.data);
          channelsData = [];
        }
        
        setChannels(channelsData);
      } catch (error) {
        console.error('Error fetching channels:', error);
        if (error.response?.status === 401) {
          // احتمالاً توکن منقضی شده
          window.location.href = '/login';
        }
      }
    };

    fetchChannels();
  }, []);

  // وقتی تیک "دارای مدیا" رو برمی‌داریم، فایل‌ها رو ریست کن
  useEffect(() => {
    if (!hasMedia) {
      setMediaFiles([]);
    }
  }, [hasMedia]);

  // تابع برای انتخاب/لغو انتخاب کانال
  const toggleChannel = (channelId) => {
    setSelectedChannels(prev =>
      prev.includes(channelId)
        ? prev.filter(id => id !== channelId)
        : [...prev, channelId]
    );
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    setMediaFiles(prev => [...prev, ...files]);
  };

  // تابع برای حذف فایل انتخاب‌شده
  const removeFile = (index) => {
    setMediaFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (selectedChannels.length === 0) {
      setMessage('لطفاً حداقل یک کانال انتخاب کنید');
      return;
    }

    if (!content && !hasMedia) {
      setMessage('لطفاً متن پست را وارد کنید یا فایل رسانه‌ای انتخاب کنید');
      return;
    }

    if (hasMedia && mediaFiles.length === 0) {
      setMessage('لطفاً فایل رسانه‌ای انتخاب کنید');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const formData = new FormData();
      
      // اضافه کردن محتوای متنی
      if (content) {
        formData.append('content', content);
      }
      else{
        formData.append('content','')
      }
      
      // انتخاب کانال‌ها (چند کانال)
      selectedChannels.forEach(channelId => {
        formData.append('channels', channelId);
      });

      // تعیین نوع پست
      if (hasMedia) {
        formData.append('types', 'media');
        // اضافه کردن فایل‌های رسانه‌ای
        mediaFiles.forEach(file => {
          formData.append('media_files', file);
        });
      } else {
        formData.append('types', 'text');
      }

      // اگر زمان‌بندی فعال باشه
      if (isScheduled && scheduledTime) {
        formData.append('scheduled_time', scheduledTime);
      }

      // ارسال به سرور با آدرس صحیح
      const response = await api.post('/posts/create/', formData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setMessage('پست با موفقیت ایجاد شد');
      setContent('');
      setMediaFiles([]);
      setHasMedia(false);
      setIsScheduled(false);
      setScheduledTime('');
      setSelectedChannels([]); // انتخاب کانال‌ها رو هم ریست کن
      
    } catch (error) {
      console.error('Error details:', error.response?.data);
      const errorMsg = error.response?.data?.types || 
                      error.response?.data?.detail || 
                      error.response?.data?.msg ||
                      error.response?.data ||
                      'خطا در ارسال پست';
      setMessage(Array.isArray(errorMsg) ? errorMsg[0] : 
                typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : 
                errorMsg || 'خطا در ارسال پست');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="post-editor" style={{ 
      padding: '20px',
      height: 'calc(100vh - 100px)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <h3 style={{ 
        margin: '0 0 20px 0',
        color: '#333',
        fontSize: '1.5rem'
      }}>
        ارسال پست جدید
      </h3>
      
      {message && (
        <div style={{ 
          padding: '10px', 
          margin: '10px 0',
          backgroundColor: message.includes('خطا') ? '#ffebee' : '#e8f5e8',
          border: `1px solid ${message.includes('خطا') ? '#f44336' : '#4caf50'}`,
          borderRadius: '4px'
        }}>
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* بخش اصلی فرم با اسکرول */}
        <div style={{ 
          flex: 1,
          overflowY: 'auto',
          paddingRight: '10px'
        }}>
          {/* انتخاب کانال‌ها */}
          <div className="channel-selection" style={{ marginBottom: '20px' }}>
            <h4 style={{ 
              margin: '0 0 10px 0',
              color: '#333',
              fontSize: '1.2rem'
            }}>
              انتخاب کانال‌ها:
            </h4>
            <div style={{
              maxHeight: '200px',
              overflowY: 'auto',
              border: '1px solid #ddd',
              padding: '10px',
              borderRadius: '4px',
              backgroundColor: '#f9f9f9'
            }}>
              {channels.length === 0 ? (
                <p>کانالی یافت نشد</p>
              ) : (
                channels.map(channel => (
                  <div key={channel.id} className="channel-checkbox" style={{ marginBottom: '10px' }}>
                    <label style={{ display: 'flex', alignItems: 'center' }}>
                      <input
                        type="checkbox"
                        id={`channel-${channel.id}`}
                        checked={selectedChannels.includes(channel.id)}
                        onChange={() => toggleChannel(channel.id)}
                        style={{ marginRight: '10px' }}
                      />
                      <span>{channel.name} ({channel.username})</span>
                    </label>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* محتوای متنی - textarea ساده */}
          <div className="content-section" style={{ marginBottom: '20px' }}>
            <label htmlFor="post-content" style={{ display: 'block', marginBottom: '5px' }}>
              متن پست:
            </label>
            <textarea
              id="post-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="متن پست خود را بنویسید..."
              rows="8"
              style={{
                width: '95%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontFamily: 'inherit',
                fontSize: '14px',
                resize: 'vertical'
              }}
            />
          </div>

          {/* نمایش پیش‌نمایش محتوا */}


          {/* نمایش پیش‌نمایش فایل‌ها - فقط وقتی تیک "دارای مدیا" زده شده */}
          {hasMedia && mediaFiles.length > 0 && (
            <div className="media-preview-section" style={{ marginBottom: '20px' }}>
              <h4 style={{ 
                margin: '0 0 10px 0',
                color: '#333',
                fontSize: '1.2rem'
              }}>
                فایل‌های انتخاب‌شده:
              </h4>
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '10px',
                border: '1px solid #ddd',
                padding: '10px',
                borderRadius: '4px',
                backgroundColor: '#f9f9f9'
              }}>
                {mediaFiles.map((file, index) => (
                  <div key={index} style={{
                    position: 'relative',
                    width: '100px',
                    height: '100px'
                  }}>
                    {file.type.startsWith('image/') ? (
                      // پیش‌نمایش عکس
                      <img
                        src={URL.createObjectURL(file)}
                        alt={file.name}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover',
                          borderRadius: '4px'
                        }}
                      />
                    ) : file.type.startsWith('video/') ? (
                      // پیش‌نمایش ویدیو
                      <div style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        backgroundColor: '#e0e0e0',
                        borderRadius: '4px',
                        fontSize: '24px'
                      }}>
                        🎥
                      </div>
                    ) : file.type.startsWith('audio/') ? (
                      // پیش‌نمایش صوت
                      <div style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        backgroundColor: '#e0e0e0',
                        borderRadius: '4px',
                        fontSize: '24px'
                      }}>
                        🎵
                      </div>
                    ) : (
                      // پیش‌نمایش فایل‌های دیگر
                      <div style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        backgroundColor: '#e0e0e0',
                        borderRadius: '4px',
                        fontSize: '24px'
                      }}>
                        📄
                      </div>
                    )}
                    <div style={{
                      position: 'absolute',
                      bottom: '2px',
                      left: '2px',
                      right: '2px',
                      backgroundColor: 'rgba(0,0,0,0.7)',
                      color: 'white',
                      fontSize: '10px',
                      padding: '2px',
                      borderRadius: '2px',
                      textAlign: 'center',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {file.name.length > 10 ? file.name.substring(0, 7) + '...' : file.name}
                    </div>
                    {/* دکمه حذف فایل */}
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      style={{
                        position: 'absolute',
                        top: '-5px',
                        right: '-5px',
                        background: '#f44336',
                        color: 'white',
                        border: 'none',
                        borderRadius: '50%',
                        width: '20px',
                        height: '20px',
                        cursor: 'pointer',
                        fontSize: '18px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                      aria-label={`حذف فایل ${file.name}`}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* گزینه تعیین وجود مدیا */}
          <div className="media-toggle" style={{ marginBottom: '20px' }}>
            <label style={{ display: 'flex', alignItems: 'center' }}>
              <input
                type="checkbox"
                checked={hasMedia}
                onChange={(e) => setHasMedia(e.target.checked)}
                style={{ marginRight: '10px' }}
              />
              <span>پست دارای فایل رسانه‌ای است</span>
            </label>
          </div>

          {/* آپلود فایل‌های رسانه‌ای - فقط وقتی گزینه تیک خورده */}
          {hasMedia && (
            <div className="media-section" style={{ marginBottom: '20px' }}>
              <label htmlFor="media-files" style={{ display: 'block', marginBottom: '5px' }}>
                فایل‌های رسانه‌ای:
              </label>
              <input
                id="media-files"
                type="file"
                multiple
                onChange={handleFileChange}
                accept="image/*,video/*,audio/*"
                className="file-input"
                style={{ marginBottom: '10px' }}
              />
              
              {mediaFiles.length > 0 && (
                <div className="uploaded-files">
                  <h5 style={{ 
                    margin: '0 0 10px 0',
                    color: '#333',
                    fontSize: '1.1rem'
                  }}>
                    فایل‌های انتخاب‌شده:
                  </h5>
                  <div className="files-list">
                    {mediaFiles.map((file, index) => (
                      <div key={index} className="file-item" style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '5px',
                        borderBottom: '1px solid #eee'
                      }}>
                        <span>{file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                        <button
                          type="button"
                          onClick={() => removeFile(index)}
                          className="remove-file-btn"
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#f44336',
                            cursor: 'pointer',
                            fontSize: '18px'
                          }}
                          aria-label={`حذف فایل ${file.name}`}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* زمان‌بندی */}
          <div className="schedule-section" style={{ marginBottom: '20px' }}>
            <label style={{ display: 'flex', alignItems: 'center' }}>
              <input
                type="checkbox"
                checked={isScheduled}
                onChange={(e) => setIsScheduled(e.target.checked)}
                style={{ marginRight: '10px' }}
              />
              <span>زمان‌بندی ارسال</span>
            </label>
            
            {isScheduled && (
              <div style={{ marginTop: '10px' }}>
                <label htmlFor="scheduled-time" style={{ display: 'block', marginBottom: '5px' }}>
                  زمان ارسال:
                </label>
                <input
                  id="scheduled-time"
                  type="datetime-local"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  className="schedule-input"
                  dir="ltr"
                  style={{
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}
                />
              </div>
            )}
          </div>
        </div>

        {/* دکمه ارسال - همیشه در پایین قرار بگیره */}
        <div className="submit-section" style={{ 
          marginTop: '20px',
          paddingTop: '20px',
          borderTop: '1px solid #eee'
        }}>
          <button 
            type="submit" 
            disabled={loading}
            style={{
              padding: '10px 20px',
              backgroundColor: loading ? '#ccc' : '#4caf50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'در حال ارسال...' : 'ارسال پست'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PostEditor;