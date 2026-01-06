// src/pages/OmniChat.tsx
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Bot, Trash2, Sparkles, Pill, Calendar, Activity, HelpCircle, MessageSquare } from 'lucide-react';
import { OmniMessageBubble } from '../components/chat/OmniMessageBubble';
import { OmniChatInput } from '../components/chat/OmniChatInput';
import { omniChatService } from '../services/omnichat.service';
import type { OmniChatMessage, OmniInputType } from '../types/omnichat.types';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { useAuth } from '../contexts/AuthContext';

// Simple UUID generator
const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
};

// Suggestion cards for patients
const PATIENT_SUGGESTIONS = [
  { icon: Pill, label: 'My Medications', prompt: 'Show me my current medications', color: 'bg-blue-500' },
  { icon: Calendar, label: 'Reminders', prompt: 'What are my medication reminders for today?', color: 'bg-emerald-500' },
  { icon: Activity, label: 'Adherence', prompt: 'How is my medication adherence this week?', color: 'bg-purple-500' },
  { icon: HelpCircle, label: 'Drug Info', prompt: 'Tell me about the side effects of my medications', color: 'bg-amber-500' },
];

const OmniChat: React.FC = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<OmniChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [identifyPillMode, setIdentifyPillMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Load chat history on mount
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
        imageUrl: msg.image_url || undefined,
        audioUrl: msg.audio_url || undefined,
        toolsUsed: msg.tools_used ? JSON.parse(msg.tools_used) : undefined,
        intent: msg.intent || undefined,
      }));
      
      setMessages(loadedMessages);
    } catch (error) {
      // Silent fail for history
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    loadChatHistory();
  }, [loadChatHistory]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const togglePillMode = () => setIdentifyPillMode(prev => !prev);

  const handleClearHistory = async () => {
    if (!confirm('Clear all chat history?')) return;
    try {
      await omniChatService.clearChatHistory();
      setMessages([]);
    } catch (error) {
      // Silent fail
    }
  };

  const handleSendMessage = async (text: string, image: File | null, audioBlob: Blob | null, identifyPill?: boolean) => {
    setIsLoading(true);

    let inputType: 'text' | 'voice' | 'image' | 'multimodal' = 'text';
    if (audioBlob && image) inputType = 'multimodal';
    else if (audioBlob) inputType = 'voice';
    else if (image) inputType = 'image';

    const userMsgId = generateId();
    let imageUrl = image ? URL.createObjectURL(image) : '';

    const newUserMessage: OmniChatMessage = {
      id: userMsgId,
      role: 'user',
      content: text || (audioBlob ? '🎤 Voice message' : '📷 Image'),
      timestamp: new Date(),
      input_type: inputType,
      imageUrl: imageUrl || undefined,
      audioUrl: audioBlob ? URL.createObjectURL(audioBlob) : undefined,
    };

    setMessages((prev) => [...prev, newUserMessage]);

    try {
      let messageText = text;
      if (identifyPill && image && !text.includes('identify')) {
        messageText = text ? `Please identify this pill: ${text}` : 'Please identify this pill from the image';
      }

      const response = await omniChatService.sendMessage({
        message: messageText,
        input_type: inputType,
        audio_file: audioBlob || undefined,
        image_file: image || undefined,
        output_audio: true,
      });

      const botMsgId = generateId();
      
      let botAudioUrl = undefined;
      if (response.audio_path) {
        botAudioUrl = omniChatService.getStreamUrl(response.audio_path);
      }

      let botImageUrl = undefined;
      if (response.image_encoded && response.image_encoded.base64) {
        botImageUrl = `data:image/jpeg;base64,${response.image_encoded.base64}`;
      }

      if (response.transcription && audioBlob) {
        setMessages(currentMessages => 
          currentMessages.map(msg => 
            msg.id === userMsgId ? { ...msg, content: `"${response.transcription}"`, transcription: response.transcription || undefined } : msg
          )
        );
      }

      const newBotMessage: OmniChatMessage = {
        id: botMsgId,
        role: 'assistant',
        content: response.agent_response,
        timestamp: new Date(),
        input_type: inputType,
        audioUrl: botAudioUrl,
        isAudioAutoPlay: response.auto_play,
        imageUrl: botImageUrl,
        toolsUsed: response.tools_used || [],
        intent: response.intent || undefined
      };

      setMessages((prev) => [...prev, newBotMessage]);

    } catch (error: unknown) {
      let displayError = "Sorry, I encountered an error. Please try again.";
      if (error instanceof Error) displayError = error.message;

      const errorMsg: OmniChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: `⚠️ ${displayError}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (prompt: string) => {
    handleSendMessage(prompt, null, null);
  };

  return (
    <DashboardLayout>
      <div className="flex flex-col h-[calc(100vh-6rem)] bg-gradient-to-b from-slate-50 to-white rounded-2xl overflow-hidden shadow-sm border border-slate-200">
        {/* Modern Header */}
        <header className="bg-white border-b border-slate-100 px-4 md:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
                <Bot size={22} />
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-800">MediTrack AI</h1>
              <p className="text-xs text-slate-500">Your personal health assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={handleClearHistory}
                className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                title="Clear chat"
              >
                <Trash2 size={18} />
              </button>
            )}
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-600 rounded-full text-xs font-medium">
              <Sparkles size={12} />
              <span>AI Powered</span>
            </div>
          </div>
        </header>

        {/* Messages Area */}
        <main ref={chatContainerRef} className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-6">
            {isLoadingHistory ? (
              <div className="flex flex-col items-center justify-center h-[50vh]">
                <div className="w-10 h-10 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <p className="mt-4 text-sm text-slate-500">Loading your conversation...</p>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[50vh] text-center">
                {/* Welcome Section */}
                <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-blue-50 rounded-2xl flex items-center justify-center mb-4 shadow-sm">
                  <MessageSquare size={28} className="text-blue-500" />
                </div>
                <h2 className="text-xl font-bold text-slate-800 mb-2">
                  Hi {user?.full_name?.split(' ')[0] || 'there'}! 👋
                </h2>
                <p className="text-slate-500 max-w-sm mb-8">
                  I'm your AI health assistant. Ask me about medications, health tips, or upload an image to identify a pill.
                </p>

                {/* Suggestion Cards */}
                <div className="grid grid-cols-2 gap-3 w-full max-w-md">
                  {PATIENT_SUGGESTIONS.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(suggestion.prompt)}
                      className="group flex items-center gap-3 p-4 bg-white border border-slate-200 rounded-xl hover:border-blue-300 hover:shadow-md hover:shadow-blue-100/50 transition-all text-left"
                    >
                      <div className={`p-2 ${suggestion.color} rounded-lg text-white group-hover:scale-110 transition-transform`}>
                        <suggestion.icon size={18} />
                      </div>
                      <span className="text-sm font-medium text-slate-700">{suggestion.label}</span>
                    </button>
                  ))}
                </div>

                {/* Quick Tips */}
                <div className="mt-8 flex flex-wrap justify-center gap-2 text-xs text-slate-400">
                  <span className="px-2 py-1 bg-slate-100 rounded-full">💬 Text</span>
                  <span className="px-2 py-1 bg-slate-100 rounded-full">🎤 Voice</span>
                  <span className="px-2 py-1 bg-slate-100 rounded-full">📷 Image</span>
                  <span className="px-2 py-1 bg-slate-100 rounded-full">💊 Pill ID</span>
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <OmniMessageBubble key={msg.id} message={msg} />
                ))}
                
                {/* Loading indicator */}
                {isLoading && (
                  <div className="flex items-start gap-2 mb-4">
                    <div className="w-8 h-8 bg-emerald-600 rounded-full flex items-center justify-center text-white">
                      <Bot size={16} />
                    </div>
                    <div className="bg-white border border-slate-100 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
                      <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        </main>

        {/* Pill Mode Banner */}
        {identifyPillMode && (
          <div className="bg-emerald-50 border-t border-emerald-100 px-4 py-2">
            <div className="max-w-3xl mx-auto flex items-center gap-2 text-emerald-700 text-sm">
              <Pill size={16} />
              <span className="font-medium">Pill Identification Mode</span>
              <span className="text-emerald-600">— Upload or photograph a pill to identify it</span>
            </div>
          </div>
        )}

        {/* Modern Input Area */}
        <div className="bg-white border-t border-slate-100 pt-2 pb-4">
          <OmniChatInput 
            onSend={handleSendMessage} 
            isLoading={isLoading} 
            identifyPillMode={identifyPillMode}
            onTogglePillMode={togglePillMode}
          />
        </div>
      </div>
    </DashboardLayout>
  );
};

export default OmniChat;
