import React, { useEffect, useState } from 'react';
import api from '../../services/api';


const ScheduledPosts = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState(null);
  const [error, setError] = useState('');

  // State برای ذخیره اطلاعات کانال‌ها (مشابه SentPosts و FailedPosts)
  const [channelCache, setChannelCache] = useState({});
  const [channelLoading, setChannelLoading] = useState({});

  useEffect(() => {
    fetchScheduledPosts();
  }, []);

  // useEffect برای بارگذاری اطلاعات کانال‌ها (مشابه SentPosts و FailedPosts)
  useEffect(() => {
    const loadChannelData = async () => {
      if (posts.length === 0) return;

      // گرفتن لیست IDهای کانال‌ها از پست‌ها
      const channelIds = posts
        .map(post => post.channel) // فرض می‌کنیم post.channel یه ID هست
        .filter(Boolean); // فیلتر کردن مقادیر null/undefined

      // پیدا کردن کانال‌هایی که هنوز در cache نیستن و داره لود نمیشن
      const uncachedChannels = channelIds.filter(id =>
        !channelCache[id] && !channelLoading[id]
      );

      // برای هر کانال uncached، درخواست اطلاعات بفرست
      uncachedChannels.forEach(id => fetchChannelInfo(id));
    };

    loadChannelData();
  }, [posts]); // هر وقت posts تغییر کنه، این useEffect اجرا بشه

  const fetchScheduledPosts = async () => {
    try {
      const res = await api.get('/posts/', { withCredentials: true });
      const scheduled = res.data?.results?.filter(
        p => p.status === 'pending' && p.scheduled_time
      );
      setPosts(scheduled || []);
      setError('');
    } catch (err) {
      console.error(err);
      setError('خطا در بارگذاری پست‌ها');
    } finally {
      setLoading(false);
    }
  };

  // تابع برای گرفتن اطلاعات کانال از سرور (مشابه SentPosts و FailedPosts)
  const fetchChannelInfo = async (channelId) => {
    // اگر اطلاعات کانال قبلاً گرفته شده، از cache استفاده کن
    if (channelCache[channelId]) {
      return;
    }

    // اگر داره گرفته می‌شه، صبر کن
    if (channelLoading[channelId]) {
      return;
    }

    // شروع گرفتن اطلاعات کانال
    setChannelLoading(prev => ({ ...prev, [channelId]: true }));

    try {
      const response = await api.get(`/channels/${channelId}/`, {
        withCredentials: true
      });
      const channelData = response.data;

      // ذخیره در cache
      setChannelCache(prev => ({ ...prev, [channelId]: channelData }));
    } catch (error) {
      console.error(`Error fetching channel ${channelId}:`, error);
    } finally {
      setChannelLoading(prev => ({ ...prev, [channelId]: false }));
    }
  };

  const handleCancel = async (id) => {
    const confirmed = window.confirm('آیا از لغو این پست مطمئن هستید؟');
    if (!confirmed) return;

    setCancellingId(id);
    try {
      await api.post(`/posts/${id}/cancel/`, null, { withCredentials: true });
      setPosts(prev => prev.filter(post => post.id !== id));
      alert('پست با موفقیت لغو شد.');
    } catch (err) {
      console.error(err);
      alert('خطا در لغو پست');
    } finally {
      setCancellingId(null);
    }
  };

  // تابع برای خلاصه کردن متن
  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  if (loading) return <div className="loading">در حال بارگذاری...</div>;

  return (
    <div className="scheduled-posts">
      <h3 className="text-lg font-semibold mb-3">پست‌های زمان‌بندی‌شده</h3>

      {error && <p className="error text-red-600 mb-3">{error}</p>}

      {posts.length === 0 ? (
        <p className="empty">هیچ پست زمان‌بندی‌شده‌ای وجود ندارد.</p>
      ) : (
        <div className="posts-list space-y-3">
          {posts.map((post) => (
            <div key={post.id} className="post-item p-3 border rounded bg-white">
              {/* نمایش خلاصه محتوا */}
              <p className="mb-2">{truncateText(post.content, 150)}</p>
              <div className="post-meta mt-2 flex justify-between text-sm text-gray-600 flex-wrap gap-2">
                <p>زمان ارسال: {new Date(post.scheduled_time).toLocaleString('fa-IR')}</p>
              </div>
              <button
                onClick={() => handleCancel(post.id)}
                disabled={cancellingId === post.id}
                className={`mt-2 px-3 py-1 rounded text-white font-medium text-sm ${
                  cancellingId === post.id
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-red-500 hover:bg-red-600'
                }`}
              >
                {cancellingId === post.id ? 'در حال لغو...' : 'لغو ارسال'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ScheduledPosts;