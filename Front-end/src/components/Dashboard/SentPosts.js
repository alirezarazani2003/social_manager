import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
const SentPosts = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [postsPerPage] = useState(10);
  const [selectedPost, setSelectedPost] = useState(null); // برای مدیریت پاپ‌آپ مدیا

  // State برای ذخیره اطلاعات کانال‌ها
  const [channelCache, setChannelCache] = useState({}); // {channelId: channelData}
  const [channelLoading, setChannelLoading] = useState({}); // {channelId: boolean}

  useEffect(() => {
    fetchSentPosts(currentPage);
  }, [currentPage]);

  const fetchSentPosts = useCallback(async (page = 1) => {
  try {
    const response = await api.get(`/posts/?page=${page}&page_size=${postsPerPage}`, {
      withCredentials: true
    });

    const sentPosts = response.data.results.filter(post =>
      post.status === 'sent'
    );

    setPosts(sentPosts);
    setTotalPages(Math.ceil(response.data.count / postsPerPage));
  } catch (error) {
    setError('خطا در دریافت پست‌های ارسال‌شده');
    console.error('Error fetching sent posts:', error);
  } finally {
    setLoading(false);
  }
}, [postsPerPage]);

  // تابع برای گرفتن اطلاعات کانال از سرور
  const fetchChannelInfo = async (channelId) => {
    // اگر اطلاعات کانال قبلاً گرفته شده، از cache استفاده کن
    if (channelCache[channelId]) {
      return channelCache[channelId];
    }
    
    // اگر داره گرفته می‌شه، صبر کن
    if (channelLoading[channelId]) {
      return null;
    }
    
    // شروع گرفتن اطلاعات کانال
    setChannelLoading(prev => ({...prev, [channelId]: true}));
    
    try {
      const response = await api.get(`/channels/${channelId}/`, {
        withCredentials: true
      });
      const channelData = response.data;
      
      // ذخیره در cache
      setChannelCache(prev => ({...prev, [channelId]: channelData}));
      
      return channelData;
    } catch (error) {
      console.error(`Error fetching channel ${channelId}:`, error);
      return null;
    } finally {
      setChannelLoading(prev => ({...prev, [channelId]: false}));
    }
  };

  // تابع برای نمایش پاپ‌آپ مدیا
  const showMediaPopup = (post) => {
    setSelectedPost(post);
  };

  // تابع برای بستن پاپ‌آپ
  const closeMediaPopup = () => {
    setSelectedPost(null);
  };

  // تابع برای خلاصه کردن متن
  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
  };

  if (loading) return <div>در حال بارگذاری پست‌های ارسال‌شده...</div>;

  return (
    <div className="sent-posts">
      <h3>پست‌های ارسال‌شده</h3>
      
      {error && <div className="error">{error}</div>}
      
      {posts.length === 0 ? (
        <p>پست ارسال‌شده‌ای یافت نشد</p>
      ) : (
        <div className="posts-list">
          {posts.map(post => (
            <div key={post.id} className="post-item">
              <div className="post-content">
                <p>{truncateText(post.content,4096 )}</p>
                <div className="post-meta">
                  <div className="post-channels">
                    <strong>کانال‌ها:</strong>
                    {/* نمایش چند کانال */}
                    <div className="channels-list">
                      {Array.isArray(post.channels) ? (
                        post.channels.map(channelId => (
                          <span key={channelId} className="channel-badge">
                            {channelCache[channelId] ? (
                              `${channelCache[channelId].name} (${channelCache[channelId].username})`
                            ) : channelLoading[channelId] ? (
                              'در حال بارگذاری...'
                            ) : (
                              // اگر اطلاعات کانال هنوز نیومده، بیخود گرفتش
                              (() => {
                                fetchChannelInfo(channelId);
                                return 'در حال بارگذاری...';
                              })()
                            )}
                          </span>
                        ))
                      ) : (
                        // اگه فقط یه کانال باشه (ساختار قدیمی)
                        <span className="channel-badge">
                          {channelCache[post.channel] ? (
                            `${channelCache[post.channel].name} (${channelCache[post.channel].username})`
                          ) : channelLoading[post.channel] ? (
                            'در حال بارگذاری...'
                          ) : (
                            // اگر اطلاعات کانال هنوز نیومده، بیخود گرفتش
                            (() => {
                              fetchChannelInfo(post.channel);
                              return 'در حال بارگذاری...';
                            })()
                          )}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="post-type">
                    <strong>نوع:</strong>
                    <span>{post.types === 'media' ? 'رسانه' : 'متن'}</span>
                  </div>
                  <div className="post-date">
                    <strong>تاریخ ارسال:</strong>
                    <span>{new Date(post.sent_at).toLocaleString('fa-IR')}</span>
                  </div>
                  {/* اگر پست دارای مدیا باشه، دکمه‌ای برای نمایش پاپ‌آپ */}
                  {post.types === 'media' && post.attachments && post.attachments.length > 0 && (
                    <button 
                      onClick={() => showMediaPopup(post)}
                      className="view-media-btn"
                    >
                      نمایش مدیا
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* صفحه‌بندی */}
      {totalPages > 1 && (
        <div className="pagination">
          <button 
            onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
          >
            قبلی
          </button>
          <span>
            صفحه {currentPage} از {totalPages}
          </span>
          <button 
            onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
          >
            بعدی
          </button>
        </div>
      )}

      {/* پاپ‌آپ نمایش مدیا */}
      {selectedPost && (
        <MediaPopup post={selectedPost} onClose={closeMediaPopup} />
      )}
    </div>
  );
};

// کامپوننت پاپ‌آپ نمایش مدیا
const MediaPopup = ({ post, onClose }) => {
  // فرض می‌کنیم attachments شامل اطلاعات فایل‌هاست
  // مثلاً: [{id: 1, file: "http://...", ...}]
  const attachments = post.attachments || [];

  return (
    <div className="media-popup-overlay" onClick={onClose}>
      <div className="media-popup-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-popup-btn" onClick={onClose}>×</button>
        <h3>مدیاهای پست {post.id}</h3>
        {attachments.length > 0 ? (
          <div className="media-list">
            {attachments.map((attachment, index) => {
              // فرض: attachment.file یه URL هست
              const fileUrl = attachment.file; 
              const fileType = attachment.file ? attachment.file.split('.').pop().toLowerCase() : '';
              
              return (
                <div key={index} className="media-item">
                  {fileType === 'jpg' || fileType === 'jpeg' || fileType === 'png' || fileType === 'gif' ? (
                    // پیش‌نمایش عکس
                    <img
                      src={fileUrl}
                      alt={`Attachment ${index + 1}`}
                      className="media-image"
                    />
                  ) : fileType === 'mp4' || fileType === 'webm' || fileType === 'ogg' ? (
                    // پیش‌نمایش ویدیو
                    <video src={fileUrl} controls className="media-video" />
                  ) : fileType === 'mp3' || fileType === 'wav' || fileType === 'ogg' ? (
                    // پیش‌نمایش صوت
                    <audio src={fileUrl} controls className="media-audio" />
                  ) : (
                    // پیش‌نمایش فایل‌های دیگر
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

                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p>مدیایی یافت نشد.</p>
        )}
      </div>
    </div>
  );
};

export default SentPosts;