// src/pages/admin/AIAssistant.tsx
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Bot, Trash2, Send, Loader2, Sparkles, Users, Pill, 
  Activity, ClipboardList
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { omniChatService } from '../../services/omnichat.service';
import type { OmniChatMessage, OmniInputType } from '../../types/omnichat.types';

const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
};

const AdminAIAssistant: React.FC = () => {
  const [messages, setMessages] = useState<OmniChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load chat history
  const loadChatHistory = useCallback(async () => {
    try {
      setIsLoadingHistory(true);
      const history = await omniChatService.getChatHistory(100, 0);
      
      const loadedMessages: OmniChatMessage[] = history.messages.map((msg) => ({
        id: msg.id.toString(),
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
        input_type: (msg.input_type as OmniInputType) || 'text',
        toolsUsed: msg.tools_used ? JSON.parse(msg.tools_used) : undefined,
        intent: msg.intent || undefined,
      }));
      
      setMessages(loadedMessages);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    loadChatHistory();
  }, [loadChatHistory]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleClearHistory = async () => {
    if (!confirm('Are you sure you want to clear all chat history?')) return;
    try {
      await omniChatService.clearChatHistory();
      setMessages([]);
    } catch (error) {
      console.error('Failed to clear chat history:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    setIsLoading(true);

    const userMsgId = generateId();
    const newUserMessage: OmniChatMessage = {
      id: userMsgId,
      role: 'user',
      content: inputText,
      timestamp: new Date(),
      input_type: 'text',
    };

    setMessages(prev => [...prev, newUserMessage]);
    const textToSend = inputText;
    setInputText('');

    try {
      const response = await omniChatService.sendMessage({
        message: textToSend,
        output_audio: false,
        tool_choice: 'main',
      });

      const assistantMessage: OmniChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: response.agent_response || 'I could not process your request.',
        timestamp: new Date(),
        input_type: 'text',
        toolsUsed: response.tools_used || undefined,
        intent: response.intent || undefined,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: OmniChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        input_type: 'text',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Admin-specific quick actions
  const quickActions = [
    { icon: <Users className="w-4 h-4" />, label: 'All patients', query: 'Show me all patients' },
    { icon: <Activity className="w-4 h-4" />, label: 'Low adherence', query: 'Which patients have low medication adherence?' },
    { icon: <Pill className="w-4 h-4" />, label: 'Medications overview', query: 'Give me an overview of medications in the catalog' },
    { icon: <ClipboardList className="w-4 h-4" />, label: 'Pending assignments', query: 'Are there any pending medication assignments?' },
  ];

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Bot className="w-7 h-7 text-blue-600" />
            Admin AI Assistant
          </h1>
          <p className="text-slate-500 mt-1">
            Manage patients, analyze adherence, and get insights
          </p>
        </div>
        <Button 
          variant="ghost" 
          size="sm"
          onClick={handleClearHistory}
          className="text-gray-500"
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Clear History
        </Button>
      </div>

      {/* Chat Container */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {isLoadingHistory ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-blue-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Admin AI Assistant
              </h2>
              <p className="text-gray-500 max-w-md mb-6">
                I can help you manage patients, assign medications, analyze adherence patterns, 
                and provide insights about your patient population.
              </p>
              
              {/* Quick Actions Grid */}
              <div className="grid grid-cols-2 gap-3 max-w-md">
                {quickActions.map((action, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInputText(action.query)}
                    className="flex items-center gap-2 px-4 py-3 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg text-sm transition-colors text-left"
                  >
                    <span className="text-blue-600">{action.icon}</span>
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <AdminMessageBubble key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                    <Bot className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-100">
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Ask about patients, medications, or adherence..."
                rows={1}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                style={{ minHeight: '48px', maxHeight: '120px' }}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={isLoading || !inputText.trim()}
              className={`p-3 rounded-lg transition-colors ${
                isLoading || !inputText.trim()
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>

          {/* Quick actions */}
          {messages.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {quickActions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={() => setInputText(action.query)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 hover:bg-gray-100 text-gray-600 rounded-full text-xs transition-colors"
                >
                  {action.icon}
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

// Admin Message Bubble
interface AdminMessageBubbleProps {
  message: OmniChatMessage;
}

const AdminMessageBubble: React.FC<AdminMessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
        isUser ? 'bg-violet-600' : 'bg-blue-100'
      }`}>
        {isUser ? (
          <span className="text-white text-sm font-medium">A</span>
        ) : (
          <Bot className="w-5 h-5 text-blue-600" />
        )}
      </div>

      <div className={`max-w-[70%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-4 py-3 rounded-2xl ${
          isUser 
            ? 'bg-violet-600 text-white rounded-tr-none' 
            : 'bg-gray-100 text-gray-900 rounded-tl-none'
        }`}>
          <div className="whitespace-pre-wrap break-all">
            {message.content}
          </div>
        </div>

        {message.toolsUsed && message.toolsUsed.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {message.toolsUsed.map((tool, idx) => (
              <span 
                key={idx}
                className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full"
              >
                {tool}
              </span>
            ))}
          </div>
        )}

        <div className={`text-xs text-gray-400 mt-1 ${isUser ? 'text-right' : ''}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};

export default AdminAIAssistant;
