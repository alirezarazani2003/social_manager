import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import MediaGallery from './MediaGallery';

const PostEditor = () => {
  const [channels, setChannels] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [content, setContent] = useState('');
  const [hasMedia, setHasMedia] = useState(false);
  const [isScheduled, setIsScheduled] = useState(false);
  const [scheduledTime, setScheduledTime] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  // Stateهای جدید برای مدیریت گالری
  const [showMediaGallery, setShowMediaGallery] = useState(false);
  const [selectedMedia, setSelectedMedia] = useState([]); // آرایه‌ای از مدیاهای انتخاب‌شده از گالری

  // دریافت لیست کانال‌ها
  useEffect(() => {
    const fetchChannels = async () => {
      try {
        const response = await api.get('/channels/', {
          withCredentials: true
        });
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
          window.location.href = '/login';
        }
      }
    };
    fetchChannels();
  }, []);

  // وقتی تیک "دارای مدیا" رو برمی‌داریم، فایل‌ها رو ریست کن
  useEffect(() => {
    if (!hasMedia) {
      setSelectedMedia([]); // ریست کردن مدیاهای انتخاب‌شده از گالری
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

  const removeSelectedMedia = (mediaId) => {
    setSelectedMedia(prev => prev.filter(media => media.id !== mediaId));
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
    // بررسی اینکه حداقل یک فایل (فقط از گالری) انتخاب شده باشد
    if (hasMedia && selectedMedia.length === 0) { // تغییر: فقط selectedMedia چک می‌شه
      setMessage('لطفاً فایل رسانه‌ای از گالری انتخاب کنید');
      return;
    }
    setLoading(true);
    setMessage('');
    try {
      const formData = new FormData();
      // اضافه کردن محتوای متنی
      if (content) {
        formData.append('content', content);
      } else {
        formData.append('content', '');
      }
      // انتخاب کانال‌ها (چند کانال)
      selectedChannels.forEach(channelId => {
        formData.append('channels', channelId);
      });
      // تعیین نوع پست
      if (hasMedia) {
        formData.append('types', 'media');
        selectedMedia.forEach(media => {
          formData.append('existing_media_ids', media.id);
        });
        // === پایان تغییر ===
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
      setSelectedMedia([]); // ریست کردن مدیاهای انتخاب‌شده از گالری
      setHasMedia(false);
      setIsScheduled(false);
      setScheduledTime('');
      setSelectedChannels([]);
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
      {/* پاپ‌آپ گالری مدیا */}
      <MediaGallery
        isOpen={showMediaGallery}
        onClose={() => setShowMediaGallery(false)}
        onMediaSelect={setSelectedMedia} // انتظار داره یک آرایه از مدیاها دریافت کنه
        selectedMedia={selectedMedia} // برای نمایش مدیاهای انتخاب‌شده در گالری
      />
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
                      <span>{channel.name} ({channel.username} - {channel.platform}) </span>
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
          {/* بخش مدیا - فقط وقتی گزینه تیک خورده */}
          {hasMedia && (
            <div className="media-section" style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>
                فایل‌های رسانه‌ای:
              </label>
              {/* فقط دکمه انتخاب از گالری */}
              <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowMediaGallery(true)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#2196f3',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  انتخاب از گالری
                </button>
              </div>
              {/* نمایش فایل‌های انتخاب‌شده - فقط از گالری */}
              {selectedMedia.length > 0 && ( // تغییر: فقط selectedMedia
                <div style={{
                  border: '1px solid #ddd',
                  padding: '10px',
                  borderRadius: '4px',
                  backgroundColor: '#f9f9f9'
                }}>
                  <h5>فایل‌های انتخاب‌شده:</h5>
                  {/* مدیاهای انتخاب‌شده از گالری */}
                  <div>
                    <strong>از گالری:</strong>
                    {selectedMedia.map((media) => (
                      <div key={`selected-${media.id}`} style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '5px',
                        backgroundColor: '#e8f5e8',
                        borderRadius: '4px',
                        marginBottom: '5px'
                      }}>
                        <span>📁 {media.title}</span>
                        <button
                          type="button" // مهم: type button باشد تا فرم submit نشه
                          onClick={() => removeSelectedMedia(media.id)}
                          style={{ background: 'none', border: 'none', color: '#f44336' }}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                  {/* // حذف شد: بخش فایل‌های جدید */}
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
