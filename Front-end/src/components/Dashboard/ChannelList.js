import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './ChannelList.css'
const ChannelList = () => {
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingChannel, setEditingChannel] = useState(null); // برای مدیریت ویرایش

  useEffect(() => {
    fetchChannels();
  }, []);

  const fetchChannels = async () => {
    setLoading(true);
    setError('');
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
      const errorMsg = error.response?.data?.detail || 'خطا در دریافت لیست کانال‌ها';
      setError(errorMsg);
      console.error('Error fetching channels:', error);
    } finally {
      setLoading(false);
    }
  };

  const addChannel = async (channelData) => {
    setLoading(true); // فقط برای بخش فرم
    setError('');

    try {
      const response = await api.post('/channels/create/', channelData, {
        withCredentials: true
      });
      const newChannel = response.data;
      setChannels(prevChannels => [...prevChannels, newChannel]);
      return { success: true };
    } catch (error) {
      const errorMsg = error.response?.data?.detail ||
        error.response?.data?.reason ||
        error.response?.data?.username || // اگر خطای مربوط به username بود
        error.response?.data?.name ||    // اگر خطای مربوط به name بود
        'خطا در اضافه کردن کانال';
      setError(typeof errorMsg === 'object' ? Object.values(errorMsg)[0] : errorMsg);
      return {
        success: false,
        message: typeof errorMsg === 'object' ? Object.values(errorMsg)[0] : errorMsg
      };
    } finally {
      setLoading(false);
    }
  };

  const updateChannel = async (channelId, channelData) => {
    setLoading(true); // فقط برای بخش فرم
    setError('');

    try {
      const response = await api.put(`/channels/${channelId}/`, channelData, {
        withCredentials: true
      });
      const updatedChannel = response.data;
      setChannels(prevChannels =>
        prevChannels.map(channel =>
          channel.id === channelId ? updatedChannel : channel
        )
      );
      setEditingChannel(null);
      return { success: true };
    } catch (error) {
      const errorMsg = error.response?.data?.detail ||
        error.response?.data?.reason ||
        error.response?.data?.username ||
        error.response?.data?.name ||
        'خطا در ویرایش کانال';
      setError(typeof errorMsg === 'object' ? Object.values(errorMsg)[0] : errorMsg);
      return {
        success: false,
        message: typeof errorMsg === 'object' ? Object.values(errorMsg)[0] : errorMsg
      };
    } finally {
      setLoading(false);
    }
  };

  const deleteChannel = async (channelId) => {
    if (!window.confirm('آیا از حذف این کانال مطمئن هستید؟')) {
      return { success: false, message: 'عملیات لغو شد' };
    }

    setError('');

    try {
      await api.delete(`/channels/${channelId}/`, {
        withCredentials: true
      });
      setChannels(prevChannels => prevChannels.filter(channel => channel.id !== channelId));
      
      // اگر کانالی که داریم ویرایش می‌کردیم حذف شد
      if (editingChannel && editingChannel.id === channelId) {
        setEditingChannel(null);
      }
      return { success: true };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'خطا در حذف کانال';
      setError(errorMsg);
      return { success: false, message: errorMsg };
    }
  };

  if (loading && channels.length === 0) {
    return <div className="channel-list-loading">در حال بارگذاری کانال‌ها...</div>;
  }

  return (
    <div className="channel-list">
      <div className="channel-list-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h3 style={{ margin: 0 }}>کانال‌های من</h3>
          <button
            onClick={fetchChannels}
            className="refresh-btn"
            title="بروزرسانی لیست"
            disabled={loading}
            style={{
              padding: '2px 6px',
              fontSize: '12px',
              backgroundColor: '#f5f5f5',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            ↻
          </button>
        </div>
        {editingChannel ? (
          <button onClick={() => setEditingChannel(null)} className="cancel-edit-btn">
            لغو ویرایش
          </button>
        ) : (
          <AddChannelForm onAdd={addChannel} isLoading={loading} />
        )}
      </div>

      {error && <div className="error">{error}</div>}

      <div className="channels">
        {channels.length === 0 ? (
          <p>کانالی ثبت نشده است</p>
        ) : (
          channels.map(channel => (
            <div key={channel.id} className="channel-item">
              {editingChannel && editingChannel.id === channel.id ? (
                <EditChannelForm
                  channel={channel}
                  onUpdate={updateChannel}
                  onCancel={() => setEditingChannel(null)}
                  isLoading={loading}
                />
              ) : (
                <>
                  <label htmlFor={`channel-${channel.id}`} style={{ flex: 1, cursor: 'pointer' }}>
                    <span className="channel-name">{channel.name}</span>
                    <span className="channel-username">({channel.username})</span>
                    <span className={`channel-status ${channel.is_verified ? 'verified' : 'not-verified'}`}>
                      {channel.is_verified ? '✓ وریفای شده' : '✗ وریفای نشده'}
                    </span>
                  </label>
                  <div className="channel-actions">
                    <button
                      onClick={() => setEditingChannel(channel)}
                      className="edit-btn"
                      aria-label={`ویرایش کانال ${channel.name}`}
                      style={{
                        padding: '2px 6px',
                        fontSize: '12px',
                        backgroundColor: '#ff9800',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        marginRight: '5px'
                      }}
                    >
                      ویرایش
                    </button>
                    <button
                      onClick={() => deleteChannel(channel.id)}
                      className="delete-btn"
                      aria-label={`حذف کانال ${channel.name}`}
                      style={{
                        padding: '2px 6px',
                        fontSize: '12px',
                        backgroundColor: '#f44336',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer'
                      }}
                    >
                      حذف
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// فرم اضافه کردن کانال جدید
const AddChannelForm = ({ onAdd, isLoading }) => {
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    username: '',
    platform: 'telegram'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();

    const result = await onAdd(formData);

    if (result.success) {
      setFormData({ name: '', username: '', platform: 'telegram' });
      setShowForm(false);
    } else {
      alert(result.message);
    }
  };

  if (!showForm) {
    return (
      <button
        onClick={() => setShowForm(true)}
        className="add-channel-btn"
        disabled={isLoading}
        style={{
          padding: '4px 8px',
          fontSize: '12px',
          backgroundColor: '#4caf50',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: isLoading ? 'not-allowed' : 'pointer'
        }}
      >
        + اضافه کردن کانال
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="add-channel-form" style={{
      backgroundColor: '#f5f5f5',
      padding: '10px',
      borderRadius: '4px',
      marginTop: '10px'
    }}>
      <div className="form-group" style={{ marginBottom: '10px' }}>
        <input
          type="text"
          placeholder="نام کانال"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '5px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            boxSizing: 'border-box'
          }}
        />
      </div>
      <div className="form-group" style={{ marginBottom: '10px' }}>
        <input
          type="text"
          placeholder="شناسه کانال (مثل @channel)"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          required
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '5px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            boxSizing: 'border-box'
          }}
        />
      </div>
      <div className="form-group" style={{ marginBottom: '10px' }}>
        <select
          value={formData.platform}
          onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '5px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            boxSizing: 'border-box'
          }}
        >
          <option value="telegram">تلگرام</option>
          <option value="bale">بله</option>
        </select>
      </div>
      <div className="form-actions" style={{ display: 'flex', gap: '5px' }}>
        <button 
          type="submit" 
          disabled={isLoading}
          style={{
            padding: '5px 10px',
            backgroundColor: isLoading ? '#ccc' : '#4caf50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          {isLoading ? 'در حال اضافه...' : 'اضافه کردن'}
        </button>
        <button 
          type="button" 
          onClick={() => setShowForm(false)}
          disabled={isLoading}
          style={{
            padding: '5px 10px',
            backgroundColor: '#757575',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          انصراف
        </button>
      </div>
    </form>
  );
};

// فرم ویرایش کانال
const EditChannelForm = ({ channel, onUpdate, onCancel, isLoading }) => {
  const [formData, setFormData] = useState({
    name: channel.name,
    username: channel.username,
    platform: channel.platform
  });

  const handleSubmit = async (e) => {
    e.preventDefault();

    const result = await onUpdate(channel.id, formData);

    if (!result.success) {
      // خطا در state اصلی ChannelList نمایش داده می‌شه
    }
  };

  return (
    <form onSubmit={handleSubmit} className="edit-channel-form" style={{
      backgroundColor: '#f5f5f5',
      padding: '10px',
      borderRadius: '4px',
      marginTop: '10px'
    }}>
      <div className="form-group" style={{ marginBottom: '10px' }}>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '5px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            boxSizing: 'border-box'
          }}
        />
      </div>
      <div className="form-group" style={{ marginBottom: '10px' }}>
        <input
          type="text"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          required
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '5px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            boxSizing: 'border-box'
          }}
        />
      </div>
      <div className="form-group" style={{ marginBottom: '10px' }}>
        <select
          value={formData.platform}
          onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '5px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            boxSizing: 'border-box'
          }}
        >
          <option value="telegram">تلگرام</option>
          <option value="bale">بله</option>
        </select>
      </div>
      <div className="form-actions" style={{ display: 'flex', gap: '5px' }}>
        <button 
          type="submit" 
          disabled={isLoading}
          style={{
            padding: '5px 10px',
            backgroundColor: isLoading ? '#ccc' : '#4caf50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          {isLoading ? 'در حال ویرایش...' : 'ذخیره'}
        </button>
        <button 
          type="button" 
          onClick={onCancel}
          disabled={isLoading}
          style={{
            padding: '5px 10px',
            backgroundColor: '#757575',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          انصراف
        </button>
      </div>
    </form>
  );
};

export default ChannelList;