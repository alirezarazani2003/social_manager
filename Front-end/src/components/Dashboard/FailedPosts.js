import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import "./FailedPosts.css"

const FailedPosts = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [postsPerPage] = useState(10);
  const [retryingPosts, setRetryingPosts] = useState({});
  const [selectedPost, setSelectedPost] = useState(null); // برای مدیریت پاپ‌آپ مدیا

  // Cache اطلاعات کانال‌ها (channelId → channelData)
  const [channelCache, setChannelCache] = useState({});
  const [channelLoading, setChannelLoading] = useState({});

  useEffect(() => {
    fetchFailedPosts(currentPage);
  }, [currentPage]);

  // useEffect برای بارگذاری اطلاعات کانال‌ها
  useEffect(() => {
    const loadChannelData = async () => {
      if (posts.length === 0) return;
      
      const channelIds = posts.flatMap(post => 
        Array.isArray(post.channels) ? post.channels : [post.channel]
      ).filter(Boolean);
      
      const uncachedChannels = channelIds.filter(id => 
        !channelCache[id] && !channelLoading[id]
      );
      
      uncachedChannels.forEach(id => fetchChannelInfo(id));
    };

    loadChannelData();
  }, [posts]);

  const fetchFailedPosts = async (page = 1) => {
    try {
      setLoading(true);
      const response = await api.get(`/posts/?page=${page}&page_size=${postsPerPage}&status=failed`, {
        withCredentials: true,
      });

      setPosts(response.data.results);
      setTotalPages(Math.ceil(response.data.count / postsPerPage));
      setError('');
    } catch (error) {
      setError('خطا در دریافت پست‌های ناموفق');
      console.error('Error fetching failed posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchChannelInfo = async (channelId) => {
    if (channelCache[channelId] || channelLoading[channelId]) return;

    setChannelLoading((prev) => ({ ...prev, [channelId]: true }));
    try {
      const response = await api.get(`/channels/${channelId}/`, {
        withCredentials: true,
      });
      const channelData = response.data;
      setChannelCache((prev) => ({ ...prev, [channelId]: channelData }));
    } catch (error) {
      console.error(`Error fetching channel ${channelId}:`, error);
    } finally {
      setChannelLoading((prev) => ({ ...prev, [channelId]: false }));
    }
  };

  const parseErrorMessage = (rawMessage) => {
    if (!rawMessage) return 'خطای نامشخص';
    const match = rawMessage.match(/TelegramError:\s*(.+)/i);
    const detail = match ? match[1].trim() : rawMessage;
    return translateError(detail);
  };

  const translateError = (message) => {
    if (message.includes('Text is too long')) return 'متن پیام بیش از حد مجاز است';
    if (message.includes('chat not found')) return 'چت یا کانال یافت نشد';
    if (message.includes('bot was blocked')) return 'ربات توسط کاربر مسدود شده است';
    if (message.includes('PEER_ID_INVALID')) return 'شناسه کانال معتبر نیست';
    if (message.includes('Message is too long')) return 'پیام بیش از حد طولانی است';
    if (message.includes('wrong file identifier')) return 'فایل آپلود شده معتبر نیست';
    if (message.includes('file reference expired')) return 'لینک فایل منقضی شده است';
    return message;
  };

  const getErrorSolution = (errorMessage) => {
    if (errorMessage.includes('Text is too long') || errorMessage.includes('message too long')) {
      return 'متن پست را کوتاه کنید یا به چند پست کوچکتر تقسیم کنید.';
    }
    if (errorMessage.includes('chat not found') || errorMessage.includes('PEER_ID_INVALID')) {
      return 'از صحت شناسه کانال و دسترسی ربات به کانال اطمینان حاصل کنید.';
    }
    if (errorMessage.includes('bot was blocked')) {
      return 'کاربر باید ربات را آن‌بلوک کند یا پست را به کانال دیگری ارسال کنید.';
    }
    if (errorMessage.includes('wrong file identifier') || errorMessage.includes('file reference expired')) {
      return 'فایل را دوباره آپلود کنید و پست را مجدداً ارسال نمایید.';
    }
    return 'پست را دوباره ارسال کنید. اگر مشکل ادامه داشت، با پشتیبانی تماس بگیرید.';
  };

  const retryPost = async (postId) => {
    try {
      setRetryingPosts(prev => ({ ...prev, [postId]: true }));
      
      await api.post(`/posts/${postId}/retry/`, {}, {
        withCredentials: true,
      });
      
      setPosts(prev => prev.filter(post => post.id !== postId));
      alert('پست با موفقیت به صف ارسال مجدد اضافه شد!');
      
    } catch (error) {
      console.error('Error retrying post:', error);
      alert('خطا در ارسال مجدد پست. لطفاً دوباره تلاش کنید.');
    } finally {
      setRetryingPosts(prev => ({ ...prev, [postId]: false }));
    }
  };

  const deletePost = async (postId) => {
    if (!window.confirm('آیا از حذف این پست ناموفق اطمینان دارید؟')) return;
    
    try {
      await api.delete(`/posts/${postId}/`, {
        withCredentials: true,
      });
      
      setPosts(prev => prev.filter(post => post.id !== postId));
      alert('پست با موفقیت حذف شد.');
      
    } catch (error) {
      console.error('Error deleting post:', error);
      alert('خطا در حذف پست.');
    }
  };

  // تابع برای خلاصه کردن متن
  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
  };

  // تابع برای نمایش پاپ‌آپ مدیا
  const showMediaPopup = (post) => {
    setSelectedPost(post);
  };

  // تابع برای بستن پاپ‌آپ
  const closeMediaPopup = () => {
    setSelectedPost(null);
  };

  if (loading) return <div>در حال بارگذاری پست‌های ناموفق...</div>;

  return (
    <div className="failed-posts">
      <h3>پست‌های ناموفق</h3>
      <p className="text-gray-600 mb-4">در این بخش می‌توانید پست‌هایی که با خطا مواجه شده‌اند را مشاهده و مجدد ارسال کنید.</p>

      {error && <div className="error text-red-500 p-3 bg-red-100 rounded mb-4">{error}</div>}

      {posts.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-green-600 text-lg">🎊 هیچ پست ناموفقی یافت نشد!</p>
          <p className="text-gray-500 mt-2">همه پست‌های شما با موفقیت ارسال شده‌اند.</p>
        </div>
      ) : (
        <div className="posts-list">
          {posts.map((post) => (
            <div key={post.id} className="post-item border p-4 mb-4 rounded bg-red-50 shadow-sm hover:shadow-md transition-shadow">
              <div className="post-content">
                <div className="flex justify-between items-start mb-3">
                  <h4 className="font-semibold text-gray-800">پست #{post.id}</h4>
                  <span className="text-xs bg-red-200 text-red-800 px-2 py-1 rounded">
                    {new Date(post.created_at).toLocaleString('fa-IR')}
                  </span>
                </div>
                
                {/* نمایش خلاصه محتوا */}
                <p className="mb-3 text-gray-800 bg-white p-3 rounded border">
                  {truncateText(post.content, 150)}
                </p>

                <div className="post-meta text-sm text-gray-700 space-y-2">
                  <div>
                    <strong className="text-gray-800">کانال مقصد:</strong>
                    <div className="channels-list mt-1 flex flex-wrap gap-2">
                      {Array.isArray(post.channels) ? (
                        post.channels.map((channelId) => (
                          <span key={channelId} className="channel-badge inline-block bg-white px-2 py-1 rounded border text-xs">
                            {channelCache[channelId] ? (
                              `${channelCache[channelId].name} (${channelCache[channelId].username})`
                            ) : channelLoading[channelId] ? (
                              'در حال بارگذاری...'
                            ) : (
                              'در حال بارگذاری...'
                            )}
                          </span>
                        ))
                      ) : (
                        <span className="channel-badge inline-block bg-white px-2 py-1 rounded border text-xs">
                          {channelCache[post.channel] ? (
                            `${channelCache[post.channel].name} (${channelCache[post.channel].username})`
                          ) : channelLoading[post.channel] ? (
                            'در حال بارگذاری...'
                          ) : (
                            'در حال بارگذاری...'
                          )}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* نمایش نوع پست */}
                  <div className="flex items-center gap-2">
                    <strong className="text-gray-800">نوع:</strong>
                    <span className={post.types === 'media' ? 'bg-blue-100 text-blue-800 px-2 py-1 rounded' : 'bg-gray-100 text-gray-800 px-2 py-1 rounded'}>
                      {post.types === 'media' ? 'رسانه' : 'متن'}
                    </span>
                    
                    {/* دکمه نمایش مدیا برای پست‌های مدیایی */}
                    {post.types === 'media' && post.attachments && post.attachments.length > 0 && (
                      <button 
                        onClick={() => showMediaPopup(post)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        نمایش مدیا
                      </button>
                    )}
                  </div>

                  {post.error_message && (
                    <div className="error-message bg-red-100 border-r-4 border-red-500 p-3 rounded">
                      <div className="font-semibold text-red-700 mb-1">خطا: {parseErrorMessage(post.error_message)}</div>
                      <div className="text-red-600 text-sm mt-2">
                        <strong>راهنمای رفع مشکل:</strong> {getErrorSolution(parseErrorMessage(post.error_message))}
                      </div>
                    </div>
                  )}

                  {/* دکمه‌های عملیات */}
                  <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t">
                    <button
                      onClick={() => retryPost(post.id)}
                      disabled={retryingPosts[post.id]}
                      className={`px-4 py-2 rounded text-white font-medium flex items-center gap-2 ${
                        retryingPosts[post.id] 
                          ? 'bg-gray-400 cursor-not-allowed' 
                          : 'bg-green-500 hover:bg-green-600'
                      }`}
                    >
                      {retryingPosts[post.id] ? (
                        <>
                          <span className="animate-spin">🔄</span>
                          در حال ارسال...
                        </>
                      ) : (
                        <>
                          <span>↻</span>
                          ارسال مجدد
                        </>
                      )}
                    </button>
                    
                    <button
                      onClick={() => deletePost(post.id)}
                      className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 font-medium flex items-center gap-2"
                    >
                      <span>🗑️</span>
                      حذف پست
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* صفحه‌بندی */}
      {totalPages > 1 && (
        <div className="pagination flex justify-center items-center gap-4 my-6">
          <button 
            onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
            className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300 hover:bg-blue-600 transition-colors"
          >
            قبلی
          </button>
          <span className="text-gray-700 bg-gray-100 px-4 py-2 rounded">
            صفحه {currentPage} از {totalPages}
          </span>
          <button 
            onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300 hover:bg-blue-600 transition-colors"
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

// کامپوننت پاپ‌آپ نمایش مدیا (مشابه SentPosts)
const MediaPopup = ({ post, onClose }) => {
  const attachments = post.attachments || [];

  return (
    <div className="media-popup-overlay" onClick={onClose}>
      <div className="media-popup-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-popup-btn" onClick={onClose}>×</button>
        <h3 className="text-lg font-semibold mb-4">مدیاهای پست #{post.id}</h3>
        {attachments.length > 0 ? (
          <div className="media-list">
            {attachments.map((attachment, index) => {
              const fileUrl = attachment.file; 
              const fileName = attachment.file ? attachment.file.split('/').pop() : 'ناشناخته';
              const fileType = attachment.file ? attachment.file.split('.').pop().toLowerCase() : '';
              
              return (
                <div key={index} className="media-item mb-4 p-2 border rounded">
                  <div className="text-sm text-gray-600 mb-2">{fileName}</div>
                  {fileType === 'jpg' || fileType === 'jpeg' || fileType === 'png' || fileType === 'gif' ? (
                    <img
                      src={fileUrl}
                      alt={`Attachment ${index + 1}`}
                      className="media-image max-w-full h-auto rounded"
                    />
                  ) : fileType === 'mp4' || fileType === 'webm' || fileType === 'ogg' ? (
                    <video src={fileUrl} controls className="media-video max-w-full rounded" />
                  ) : fileType === 'mp3' || fileType === 'wav' || fileType === 'ogg' ? (
                    <audio src={fileUrl} controls className="media-audio w-full" />
                  ) : (
                    <div className="media-file flex items-center gap-2">
                      <div className="media-file-icon text-2xl">📄</div>
                      <a
                        href={fileUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        download
                        className="media-download-link text-blue-600 hover:text-blue-800 underline"
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
          <p className="text-gray-500">مدیایی یافت نشد.</p>
        )}
      </div>
    </div>
  );
};

export default FailedPosts;