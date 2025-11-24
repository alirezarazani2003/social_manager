import React, { useState, useEffect, useRef } from 'react';
import api from '../../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './AIChat.css';
let isSending = false;
const AIChat = () => {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showPromptsModal, setShowPromptsModal] = useState(false);
  const [savedPrompts, setSavedPrompts] = useState([]);
  const [promptForm, setPromptForm] = useState({ id: null, title: '', content: '' });
  const [modalError, setModalError] = useState('');
  const [expandedPromptId, setExpandedPromptId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await api.get('/chat/sessions/', { withCredentials: true });
      setSessions(response.data.data || []);
    } catch (err) {
      console.error('Error fetching sessions:', err);
      setError('خطا در بارگذاری لیست چت‌ها');
    }
  };

  const fetchSessionMessages = async (sessionId) => {
    try {
      const response = await api.get(`/chat/sessions/${sessionId}/messages/`, {
        withCredentials: true,
      });
      if (response.data.success && Array.isArray(response.data.data)) {
        setMessages(response.data.data);
      } else {
        setMessages([]);
      }
    } catch (err) {
      console.error('Error fetching messages:', err);
      setError('خطا در بارگذاری پیام‌ها');
      setMessages([]);
    }
  };

  const handleSessionSelect = async (session) => {
    setCurrentSession(session);
    await fetchSessionMessages(session.id);
    setSidebarOpen(false);
  };

  const handleNewChat = () => {
    setCurrentSession(null);
    setMessages([]);
    setInputMessage('');
    setSidebarOpen(false);
  };

  const deleteSession = async (sessionId) => {
    if (!window.confirm('آیا از حذف این چت اطمینان دارید؟')) return;

    try {
      await api.delete(`/chat/sessions/${sessionId}/`, { withCredentials: true });
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Error deleting session:', err);
      alert('حذف چت با خطا مواجه شد.');
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isSending) return;
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      content: inputMessage,
      role: 'user',
      created_at: new Date().toISOString(),
    };

    let sessionId = currentSession?.id;

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setError('');

    try {
      const response = await api.post(
        '/chat/chat/',
        { message: inputMessage, session_id: sessionId },
        { withCredentials: true, timeout: 300000 }
      );

      const botMessage = {
        content: response.data.data.ai_message.content,
        role: 'assistant',
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, botMessage]);

      // 🔥 ذخیره session_id در currentSession اگر چت جدید باشد
      if (!currentSession) {
        setCurrentSession({
          id: response.data.data.session_id,
          title: 'چت جدید', // در fetchSessions بعداً عنوان واقعی بارگذاری می‌شود
        });
      }

      // به‌روزرسانی لیست سشن‌ها
      fetchSessions();
    } catch (err) {
      console.error('Error sending message:', err);
      const errorMsg = err.response?.data?.message || 'ارسال پیام ناموفق بود';
      setError(errorMsg);

      setMessages((prev) => [
        ...prev,
        {
          content: 'متاسفانه مشکلی در ارسال پیام پیش آمد. لطفاً دوباره تلاش کنید.',
          role: 'system',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      isSending = false;
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(
      () => {
        alert('پیام با موفقیت کپی شد!');
      },
      (err) => {
        console.error('Failed to copy: ', err);
        alert('کپی ناموفق بود.');
      }
    );
  };

  const MarkdownRenderer = ({ content }) => (
    <div className="markdown-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );

  // --- مدیریت پرامپت‌ها ---

  const fetchSavedPrompts = async () => {
    try {
      const response = await api.get('/chat/prompts/', { withCredentials: true });
      if (response.data.success) {
        setSavedPrompts(response.data.data);
      }
    } catch (err) {
      setModalError('خطا در بارگذاری پرامپت‌ها');
    }
  };

  const createPrompt = async (data) => {
    try {
      const response = await api.post('/chat/prompts/', data, { withCredentials: true });
      if (response.data.success) {
        setSavedPrompts([response.data.data, ...savedPrompts]);
      }
    } catch (err) {
      setModalError('خطا در ایجاد پرامپت');
    }
  };

  const updatePrompt = async (data) => {
    try {
      const response = await api.put(`/chat/prompts/${data.id}/`, data, { withCredentials: true });
      if (response.data.success) {
        setSavedPrompts(savedPrompts.map(p => p.id === data.id ? response.data.data : p));
      }
    } catch (err) {
      setModalError('خطا در ویرایش پرامپت');
    }
  };

  const deletePrompt = async (id) => {
    if (!window.confirm('آیا از حذف این پرامپت اطمینان دارید؟')) return;
    try {
      await api.delete(`/chat/prompts/${id}/`, { withCredentials: true });
      setSavedPrompts(savedPrompts.filter(p => p.id !== id));
    } catch (err) {
      setModalError('خطا در حذف پرامپت');
    }
  };

  return (
    <div className="ai-chat-container">
      <div
        className={`overlay ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      <div className={`sessions-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sessions-header">
          <button onClick={handleNewChat} className="new-chat-button">
            + چت جدید
          </button>
        </div>
        <div className="sessions-list">
          {sessions.length === 0 ? (
            <div className="empty-sessions">هنوز چتی ندارید</div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item ${currentSession?.id === session.id ? 'active' : ''}`}
                onClick={() => handleSessionSelect(session)}
              >
                <div className="session-content">
                  <div className="session-title">{session.title}</div>
                  <div className="session-date">
                    {new Date(session.updated_at).toLocaleDateString('fa-IR')}
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                  className="delete-session-btn"
                  title="حذف چت"
                >
                  ×
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="chat-main">
        <div className="chat-header">
          <div>
            <h3>{currentSession?.title || 'چت با هوش مصنوعی'}</h3>
            <p>سوالات خود را بپرسید</p>
          </div>
          <div>
            <button
              className="menu-toggle"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              ☰
            </button>
            <button
              className="prompts-toggle"
              onClick={() => {
                fetchSavedPrompts();
                setShowPromptsModal(true);
              }}
              title="مدیریت پرامپت‌های ذخیره‌شده"
            >
              📝
            </button>
          </div>
        </div>
        <div className="hint-box">
         به دلیل شلوغ بودن سرور های هوش مصنوعی ممکن است با خطای : <b>خطا در ارسال پیام مواجه شوید</b>  . دراین صورت صفحه را رفرش کنید.
        </div>
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-chat">
              <div className="empty-chat-content">
                <div className="empty-chat-icon">🤖</div>
                <p>به چت هوش مصنوعی خوش آمدید</p>
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`message-wrapper ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}
                >
                  <div className={`message-bubble ${msg.role}`}>
                    <div className="message-content">
                      <MarkdownRenderer content={msg.content} />
                    </div>
                    <div className="message-time">
                      {new Date(msg.created_at).toLocaleTimeString('fa-IR', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                    {(msg.role === 'assistant' || msg.role === 'system') && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          copyToClipboard(msg.content);
                        }}
                        className="copy-button"
                        title="کپی پیام"
                      >
                        کپی
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="message-wrapper assistant-message">
                  <div className="message-bubble typing-indicator">در حال تایپ...</div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={sendMessage} className="message-form">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="پیام خود را بنویسید..."
            disabled={loading}
            className="message-input"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || loading}
            className="send-button"
          >
            ارسال
          </button>
        </form>
      </div>

      {/* پاپ‌آپ مدیریت پرامپت */}
      {showPromptsModal && (
        <div className="prompt-modal-overlay" onClick={() => setShowPromptsModal(false)}>
          <div className="prompt-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="prompt-modal-header">
              <h3>📝 پرامپت‌های ذخیره‌شده</h3>
              <button
                onClick={() => setShowPromptsModal(false)}
                className="prompt-modal-close"
              >
                ×
              </button>
            </div>

            {/* فرم افزودن/ویرایش */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!promptForm.title || !promptForm.content.trim()) {
                  setModalError('عنوان و متن پرامپت الزامی است');
                  return;
                }
                if (promptForm.id) {
                  updatePrompt(promptForm);
                } else {
                  createPrompt(promptForm);
                }
                setPromptForm({ id: null, title: '', content: '' });
                setModalError('');
              }}
              className="prompt-form-modal"
            >
              {modalError && <div className="prompt-error">{modalError}</div>}
              <input
                type="text"
                placeholder="عنوان پرامپت"
                value={promptForm.title}
                onChange={(e) => setPromptForm({ ...promptForm, title: e.target.value })}
                className="prompt-input"
              />
              <textarea
                placeholder="متن پرامپت..."
                value={promptForm.content}
                onChange={(e) => setPromptForm({ ...promptForm, content: e.target.value })}
                className="prompt-textarea"
                rows="3"
              />
              <button type="submit" className="prompt-submit-btn">
                {promptForm.id ? '✅ ویرایش' : '➕ افزودن'}
              </button>
            </form>

            {/* لیست پرامپت‌ها */}
            <div className="saved-prompts-list-accordion">
              {savedPrompts.length === 0 ? (
                <p className="no-prompts">هیچ پرامپتی ذخیره نشده</p>
              ) : (
                savedPrompts.map((p) => (
                  <div key={p.id} className="prompt-accordion-item">
                    {/* هدر: عنوان */}
                    <div
                      className="prompt-accordion-header"
                      onClick={() => {
                        if (expandedPromptId === p.id) {
                          setExpandedPromptId(null);
                        } else {
                          setExpandedPromptId(p.id);
                        }
                      }}
                    >
                      <span className="prompt-title">{p.title}</span>
                      <span className="prompt-toggle-icon">
                        {expandedPromptId === p.id ? '−' : '+'}
                      </span>
                    </div>

                    {/* بدنه: محتوا */}
                    <div
                      className={`prompt-accordion-body ${expandedPromptId === p.id ? 'expanded' : ''}`}
                    >
                      <div className="prompt-content-scrollable">
                        <pre>{p.content}</pre>
                      </div>
                      <div className="prompt-actions-sticky">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setInputMessage(p.content);
                            setShowPromptsModal(false);
                          }}
                          className="prompt-use-btn"
                        >
                          📥 استفاده
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setPromptForm(p);
                            setExpandedPromptId(null);
                          }}
                          className="prompt-edit-btn"
                        >
                          ✏️ ویرایش
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deletePrompt(p.id);
                          }}
                          className="prompt-delete-btn"
                        >
                          🗑 حذف
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIChat;
