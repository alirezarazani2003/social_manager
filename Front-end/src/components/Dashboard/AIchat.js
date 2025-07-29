import React, { useState, useEffect, useRef } from 'react';
import api from '../../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './AIChat.css';

const AIChat = () => {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false); // برای کنترل سایدبار موبایل
  const messagesEndRef = useRef(null);

  // اسکرول به آخرین پیام
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // دریافت لیست سشن‌ها
  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await api.get('/chat/sessions/', {
        withCredentials: true
      });
      setSessions(response.data.data || []);
      // انتخاب اولین سشن یا ایجاد سشن جدید
      if (response.data.data && response.data.data.length > 0) {
        const firstSession = response.data.data[0];
        setCurrentSession(firstSession);
        fetchSessionMessages(firstSession.id);
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
      setError('خطا در دریافت لیست چت‌ها');
    }
  };

  const fetchSessionMessages = async (sessionId) => {
    try {
      const response = await api.get(`/chat/sessions/${sessionId}/messages/`, {
        withCredentials: true
      });
      setMessages(response.data.data || []);
    } catch (error) {
      console.error('Error fetching session messages:', error);
      setError('خطا در دریافت پیام‌های چت');
    }
  };

  const createNewSession = async (title = 'چت جدید') => {
    try {
      const response = await api.post('/chat/sessions/', 
        { title },
        { withCredentials: true }
      );
      const newSession = response.data.data;
      setSessions(prev => [newSession, ...prev]);
      setCurrentSession(newSession);
      setMessages([]);
      return newSession.id;
    } catch (error) {
      console.error('Error creating new session:', error);
      setError('خطا در ایجاد چت جدید');
      return null;
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    // اگر سشن فعال نداریم، یکی ایجاد کن
    let sessionId = currentSession?.id;
    if (!sessionId) {
      sessionId = await createNewSession(inputMessage.substring(0, 30) + '...');
      if (!sessionId) return;
    }

    const userMessage = {
      content: inputMessage,
      role: 'user',
      created_at: new Date().toISOString()
    };

    // اضافه کردن پیام کاربر به لیست
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/chat/chat/', 
        { 
          message: inputMessage,
          session_id: sessionId
        },
        { withCredentials: true,
          timeout: 60000
        }
      );

      const botMessage = {
        content: response.data.data.ai_message.content,
        role: 'assistant',
        created_at: new Date().toISOString()
      };

      // اضافه کردن پاسخ ربات به لیست
      setMessages(prev => [...prev, botMessage]);

      // به‌روزرسانی لیست سشن‌ها اگر لازم باشه
      if (!currentSession) {
        fetchSessions();
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMsg = error.response?.data?.message || 'خطا در ارسال پیام';
      setError(errorMsg);
      
      // اضافه کردن پیام خطا به لیست
      const errorMessage = {
        content: 'متاسفانه مشکلی در ارسال پیام پیش آمد. لطفاً دوباره تلاش کنید.',
        role: 'system',
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = async () => {
    await createNewSession();
    setSidebarOpen(false); // بستن سایدبار در موبایل
  };

  const handleSessionSelect = async (session) => {
    setCurrentSession(session);
    await fetchSessionMessages(session.id);
    setSidebarOpen(false); // بستن سایدبار در موبایل
  };

  // کامپوننت برای رندر مارک‌داون
  const MarkdownRenderer = ({ content }) => (
    <div className="markdown-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );

  return (
    <div className="ai-chat-container">
      {/* اورلی برای موبایل */}
      <div 
        className={`overlay ${sidebarOpen ? 'open' : ''}`} 
        onClick={() => setSidebarOpen(false)}
      />
      
      {/* سایدبار سشن‌ها */}
      <div className={`sessions-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sessions-header">
          <button
            onClick={handleNewChat}
            className="new-chat-button"
          >
            + چت جدید
          </button>
        </div>
        
        <div className="sessions-list">
          {sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => handleSessionSelect(session)}
              className={`session-item ${currentSession?.id === session.id ? 'active' : ''}`}
            >
              <div className="session-title">
                {session.title}
              </div>
              <div className="session-date">
                {new Date(session.updated_at).toLocaleDateString('fa-IR')}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ناحیه اصلی چت */}
      <div className="chat-main">
        {/* هدر چت */}
        <div className="chat-header">
          <div>
            <h3>
              {currentSession?.title || 'چت با هوش مصنوعی'}
            </h3>
            <p>
              با ربات ما صحبت کنید و سوالات خود را بپرسید
            </p>
          </div>
          <button 
            className="menu-toggle" 
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            ☰
          </button>
        </div>

        {/* نمایش پیام‌ها */}
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-chat">
              <div className="empty-chat-content">
                <div className="empty-chat-icon">🤖</div>
                <p>به چت با هوش مصنوعی خوش آمدید!</p>
                <p>سوالات خود را بپرسید تا ربات به شما پاسخ دهد.</p>
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`message-wrapper ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
                >
                  <div className={`message-bubble ${message.role}`}>
                    <div className="message-content">
                      <MarkdownRenderer content={message.content} />
                    </div>
                    <div className="message-time">
                      {new Date(message.created_at).toLocaleTimeString('fa-IR', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="message-wrapper assistant-message">
                  <div className="message-bubble typing-indicator">
                    <div className="message-content">
                      در حال تایپ...
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* نمایش خطا */}
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* فرم ارسال پیام */}
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
    </div>
  );
};

export default AIChat;