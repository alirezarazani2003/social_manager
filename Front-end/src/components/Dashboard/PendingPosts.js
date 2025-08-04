import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import "./PendingPosts.css"; // یا اسم فایل CSS تو

const PendingPosts = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [channelCache, setChannelCache] = useState({});
  const [channelLoading, setChannelLoading] = useState({});

  useEffect(() => {
    fetchPendingPosts();
  }, []);

  const fetchPendingPosts = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/posts/', { withCredentials: true });
      const pendingPosts = response.data.results.filter(post =>
        post.status === 'pending' && !post.scheduled_time
      );
      setPosts(pendingPosts);
    } catch (error) {
      setError('خطا در دریافت پست‌های در حال ارسال');
      console.error('Error fetching pending posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchChannelInfo = async (channelId) => {
    if (channelCache[channelId]) return channelCache[channelId];
    if (channelLoading[channelId]) return null;

    setChannelLoading(prev => ({ ...prev, [channelId]: true }));
    try {
      const response = await api.get(`/channels/${channelId}/`, { withCredentials: true });
      const data = response.data;
      setChannelCache(prev => ({ ...prev, [channelId]: data }));
      return data;
    } catch (error) {
      console.error('Error fetching channel info:', error);
      return null;
    } finally {
      setChannelLoading(prev => ({ ...prev, [channelId]: false }));
    }
  };

  // تابع برای خلاصه کردن متن
  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const renderChannels = (channelIds) => {
    if (!Array.isArray(channelIds)) return 'بدون کانال';

    return channelIds.map((id) => {
      const cached = channelCache[id];
      if (cached) return `${cached.name} (@${cached.platform})`;
      if (!channelLoading[id]) fetchChannelInfo(id);
      return 'در حال بارگذاری...';
    }).join('، ');
  };

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

  if (loading) return <div>در حال بارگذاری پست‌های در حال ارسال...</div>;

  return (
    <div className="pending-posts">
      <h3 className="text-lg font-semibold mb-3">پست‌های در حال ارسال</h3>

      {error && (
        <div className="error text-red-600 mb-3">
          {error}
          <button
            onClick={fetchPendingPosts}
            className="ml-3 bg-red-200 text-red-800 px-2 py-1 rounded"
          >
            تلاش مجدد
          </button>
        </div>
      )}

      {posts.length === 0 ? (
        <p>پست در حال ارسالی یافت نشد</p>
      ) : (
        <div className="posts-list space-y-3">
          {posts.map(post => (
            <article key={post.id} className="post-item p-3 border rounded bg-white">
              {/* این خط تغییر کرده تا محتوا خلاصه نمایش داده بشه */}
              <p>{truncateText(post.content, 150)}</p>
              <div className="post-meta mt-2 flex justify-between text-sm text-gray-600">
                <span>کانال‌ها: {renderChannels(post.channels)}</span>
                <span className="status-badge px-2 py-1 rounded bg-yellow-300 text-yellow-900 font-semibold">
                  در حال ارسال
                </span>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};

export default PendingPosts;