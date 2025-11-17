import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import MediaGallery from './MediaGallery'; // فرض می‌کنیم این کامپوننت وجود دارد
import DatePicker from "react-multi-date-picker";
import TimePicker from "react-multi-date-picker/plugins/time_picker";
import persian from "react-date-object/calendars/persian";
import persian_fa from "react-date-object/locales/persian_fa";

const ScheduledPosts = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({
    content: '',
    scheduled_time: null,
    hasMedia: false,
    selectedMedia: [],
    selectedChannels: [],
    isScheduled: false
  });
  const [channels, setChannels] = useState([]);
  const [showMediaGallery, setShowMediaGallery] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchScheduledPosts();
    fetchChannels();
  }, []);

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

  const fetchChannels = async () => {
    try {
      const response = await api.get('/channels/', { withCredentials: true });
      let channelsData = [];
      if (Array.isArray(response.data)) {
        channelsData = response.data;
      } else if (response.data && Array.isArray(response.data.results)) {
        channelsData = response.data.results;
      }
      setChannels(channelsData);
    } catch (error) {
      console.error('Error fetching channels:', error);
    }
  };

  const openEditModal = (post) => {
    setEditData({
      content: post.content || '',
      scheduled_time: post.scheduled_time ? new Date(post.scheduled_time) : null,
      hasMedia: post.types === 'media',
      selectedMedia: post.existing_media || [],
      selectedChannels: post.channels || [],
      isScheduled: !!post.scheduled_time
    });
    setEditingId(post.id);
  };

  const removeSelectedMedia = (mediaId) => {
    setEditData(prev => ({
      ...prev,
      selectedMedia: prev.selectedMedia.filter(media => media.id !== mediaId)
    }));
  };

  const handleSaveEdit = async () => {
    if (editData.selectedChannels.length === 0) {
      setMessage('لطفاً حداقل یک کانال انتخاب کنید');
      return;
    }
    if (!editData.content && !editData.hasMedia) {
      setMessage('لطفاً متن پست را وارد کنید یا فایل رسانه‌ای انتخاب کنید');
      return;
    }
    if (editData.hasMedia && editData.selectedMedia.length === 0) {
      setMessage('لطفاً فایل رسانه‌ای از گالری انتخاب کنید');
      return;
    }

    // ✅ بررسی زمان قبل از ارسال
    let scheduledIsoDate = null;
    if (editData.isScheduled && editData.scheduled_time) {
      let dateObj = editData.scheduled_time;

      if (typeof dateObj.toDate === 'function') {
        dateObj = dateObj.toDate(); // تبدیل از react-multi-date-picker
      }

      if (!(dateObj instanceof Date)) {
        setMessage('فرمت تاریخ انتخاب شده نامعتبر است.');
        return;
      }

      // بررسی اینکه آیا زمان انتخاب شده قبل از زمان فعلی است
      const now = new Date();
      if (dateObj <= now) {
        setMessage('زمان ارسال نمی‌تواند در گذشته باشد. لطفاً یک زمان آینده انتخاب کنید.');
        return;
      }

      scheduledIsoDate = dateObj.toISOString();
    }

    try {
      const formData = new FormData();

      if (editData.content) {
        formData.append('content', editData.content);
      } else {
        formData.append('content', '');
      }

      editData.selectedChannels.forEach(channelId => {
        formData.append('channels', channelId);
      });

      if (editData.hasMedia) {
        formData.append('types', 'media');
        editData.selectedMedia.forEach(media => {
          formData.append('existing_media_ids', media.id);
        });
      } else {
        formData.append('types', 'text');
      }

      if (scheduledIsoDate) {
        formData.append('scheduled_time', scheduledIsoDate);
      } else {
        formData.append('scheduled_time', '');
      }

      await api.patch(`/posts/${editingId}/`, formData, {
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // بروزرسانی وضعیت در لیست
      setPosts(prev =>
        prev.map(post =>
          post.id === editingId
            ? {
                ...post,
                content: editData.content,
                scheduled_time: scheduledIsoDate,
                channels: editData.selectedChannels,
                existing_media: editData.selectedMedia,
                types: editData.hasMedia ? 'media' : 'text'
              }
            : post
        )
      );

      setEditingId(null);
      setMessage('پست با موفقیت ویرایش شد');
    } catch (err) {
      console.error(err);
      // ❌ اصلاً خطای سرور را نشان نده، فقط پیام عمومی
      setMessage('خطا در ویرایش پست. لطفاً دوباره تلاش کنید.');
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setMessage('');
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
              <p className="mb-2">{truncateText(post.content, 150)}</p>
              <div className="post-meta mt-2 flex justify-between text-sm text-gray-600 flex-wrap gap-2">
                <p>زمان ارسال: {new Date(post.scheduled_time).toLocaleString('fa-IR')}</p>
              </div>
              <div className="mt-2 flex gap-2">
                <button
                  onClick={() => openEditModal(post)}
                  className="px-3 py-1 rounded bg-blue-500 text-white text-sm hover:bg-blue-600"
                >
                  ویرایش
                </button>
                <button
                  onClick={() => handleCancel(post.id)}
                  disabled={cancellingId === post.id}
                  className={`px-3 py-1 rounded text-white font-medium text-sm ${
                    cancellingId === post.id
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-red-500 hover:bg-red-600'
                  }`}
                >
                  {cancellingId === post.id ? 'در حال لغو...' : 'لغو ارسال'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal ویرایش */}
      {editingId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-5 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-3">ویرایش پست</h3>

            {message && (
              <div className={`p-2 mb-3 rounded ${
                message.includes('خطا') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
              }`}>
                {message}
              </div>
            )}

            {/* انتخاب کانال */}
            <div className="mb-4">
              <h4 className="font-medium mb-2">انتخاب کانال‌ها:</h4>
              <div className="max-h-40 overflow-y-auto border rounded p-2">
                {channels.length === 0 ? (
                  <p>کانالی یافت نشد</p>
                ) : (
                  channels.map(channel => (
                    <label key={channel.id} className="block mb-1">
                      <input
                        type="checkbox"
                        checked={editData.selectedChannels.includes(channel.id)}
                        onChange={() => {
                          if (editData.selectedChannels.includes(channel.id)) {
                            setEditData(prev => ({
                              ...prev,
                              selectedChannels: prev.selectedChannels.filter(id => id !== channel.id)
                            }));
                          } else {
                            setEditData(prev => ({
                              ...prev,
                              selectedChannels: [...prev.selectedChannels, channel.id]
                            }));
                          }
                        }}
                      />
                      <span className="mr-2">{channel.name}</span>
                    </label>
                  ))
                )}
              </div>
            </div>

            {/* محتوا */}
            <div className="mb-4">
              <label className="block mb-1">متن پست:</label>
              <textarea
                value={editData.content}
                onChange={(e) => setEditData(prev => ({ ...prev, content: e.target.value }))}
                rows="4"
                className="w-full p-2 border rounded"
                placeholder="متن پست را وارد کنید..."
              />
            </div>

            {/* تیک مدیا */}
            <div className="mb-4">
              <label>
                <input
                  type="checkbox"
                  checked={editData.hasMedia}
                  onChange={(e) => setEditData(prev => ({ ...prev, hasMedia: e.target.checked }))}
                />
                <span className="mr-2">پست دارای فایل رسانه‌ای است</span>
              </label>
            </div>

            {/* مدیا */}
            {editData.hasMedia && (
              <div className="mb-4">
                <div className="flex gap-2 mb-2">
                  <button
                    type="button"
                    onClick={() => setShowMediaGallery(true)}
                    className="px-3 py-1 bg-blue-500 text-white rounded"
                  >
                    انتخاب از گالری
                  </button>
                </div>

                {editData.selectedMedia.length > 0 && (
                  <div className="border rounded p-2">
                    <h5 className="font-medium">فایل‌های انتخاب‌شده:</h5>
                    {editData.selectedMedia.map(media => (
                      <div key={media.id} className="flex justify-between items-center p-1 bg-green-100 rounded mb-1">
                        <span>📁 {media.title}</span>
                        <button
                          type="button"
                          onClick={() => removeSelectedMedia(media.id)}
                          className="text-red-500"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* زمان‌بندی */}
            <div className="mb-4">
              <label>
                <input
                  type="checkbox"
                  checked={editData.isScheduled}
                  onChange={(e) => setEditData(prev => ({ ...prev, isScheduled: e.target.checked }))}
                />
                <span className="mr-2">زمان‌بندی ارسال</span>
              </label>
              {editData.isScheduled && (
                <div className="mt-2">
                  <DatePicker
                    value={editData.scheduled_time}
                    onChange={(date) => setEditData(prev => ({ ...prev, scheduled_time: date }))}
                    format="YYYY/MM/DD HH:mm"
                    calendar={persian}
                    locale={persian_fa}
                    plugins={[<TimePicker position="bottom" />]}
                    className="w-full p-2 border rounded"
                  />
                </div>
              )}
            </div>

            {/* دکمه‌ها */}
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleSaveEdit}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              >
                ذخیره
              </button>
              <button
                onClick={handleCancelEdit}
                className="px-4 py-2 bg-gray-400 text-white rounded hover:bg-gray-500"
              >
                لغو
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal گالری */}
      <MediaGallery
        isOpen={showMediaGallery}
        onClose={() => setShowMediaGallery(false)}
        onMediaSelect={(media) => {
          setEditData(prev => ({ ...prev, selectedMedia: media }));
          setShowMediaGallery(false);
        }}
        selectedMedia={editData.selectedMedia}
      />
    </div>
  );
};

export default ScheduledPosts;