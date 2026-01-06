// src/pages/patient/AIAssistant.tsx
// Using the proven OmniChat logic with improved UI
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Bot, Trash2, Pill, Sparkles, MessageSquare } from 'lucide-react';
import { OmniMessageBubble } from '../../components/chat/OmniMessageBubble';
import { OmniChatInput } from '../../components/chat/OmniChatInput';
import { omniChatService } from '../../services/omnichat.service';
import type { OmniChatMessage, OmniInputType } from '../../types/omnichat.types';
import { useAuth } from '../../contexts/AuthContext';

// Simple UUID generator
const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
};

const AIAssistant: React.FC = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<OmniChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [identifyPillMode, setIdentifyPillMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load chat history on mount
  const loadChatHistory = useCallback(async () => {
    try {
      setIsLoadingHistory(true);
      const history = await omniChatService.getChatHistory(100, 0);
      
      // Convert history messages to OmniChatMessage format
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
      console.error('Failed to load chat history:', error);
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
    if (!confirm('Are you sure you want to clear all chat history?')) return;
    try {
      await omniChatService.clearChatHistory();
      setMessages([]);
    } catch (error) {
      console.error('Failed to clear chat history:', error);
    }
  };

  const handleSendMessage = async (text: string, image: File | null, audioBlob: Blob | null, identifyPill?: boolean) => {
    setIsLoading(true);

    // Determine input type
    let inputType: 'text' | 'voice' | 'image' | 'multimodal' = 'text';
    if (audioBlob && image) {
      inputType = 'multimodal';
    } else if (audioBlob) {
      inputType = 'voice';
    } else if (image) {
      inputType = 'image';
    }

    // 1. Create Optimistic User Message
    const userMsgId = generateId();
    let imageUrl = '';
    if (image) {
      imageUrl = URL.createObjectURL(image);
    }

    const newUserMessage: OmniChatMessage = {
      id: userMsgId,
      role: 'user',
      content: text || (audioBlob ? 'Sent a voice message' : 'Sent an image'),
      timestamp: new Date(),
      input_type: inputType,
      imageUrl: imageUrl || undefined,
      audioUrl: audioBlob ? URL.createObjectURL(audioBlob) : undefined,
    };

    setMessages((prev) => [...prev, newUserMessage]);

    try {
      // 2. Call API using service pattern
      // If pill mode is on and image is provided, add identify instruction
      let messageText = text;
      if (identifyPill && image && !text.includes('identify')) {
        messageText = text ? `Please identify this pill: ${text}` : 'Please identify this pill from the image';
      }

      const response = await omniChatService.sendMessage({
        message: messageText,
        input_type: inputType,
        audio_file: audioBlob || undefined,
        image_file: image || undefined,
        output_audio: true, // Enable TTS audio response
      });

      // 3. Process Response
      const botMsgId = generateId();
      
      let botAudioUrl = undefined;
      // If the backend returns a path like 'uploads/tts/abc.mp3', convert to stream URL
      if (response.audio_path) {
        botAudioUrl = omniChatService.getStreamUrl(response.audio_path);
      }

      // Handle returned processed image if available
      let botImageUrl = undefined;
      if (response.image_encoded && response.image_encoded.base64) {
        botImageUrl = `data:image/jpeg;base64,${response.image_encoded.base64}`;
      }

      // If there was a transcription for audio input, update the user message content
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
      console.error(error);
      
      // Determine user-friendly error message
      let displayError = "Sorry, I encountered an error processing your request.";
      if (error instanceof Error) {
        displayError = error.message;
      }

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

  // Quick actions for common queries
  const quickActions = [
    { icon: '💊', label: 'My medications', query: 'Show me my medications' },
    { icon: '⏰', label: 'Today\'s reminders', query: 'What medications do I need to take today?' },
    { icon: '📊', label: 'My adherence', query: 'How is my medication adherence?' },
    { icon: '⚠️', label: 'Drug interactions', query: 'Are there any interactions between my medications?' },
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-gradient-to-br from-slate-50 to-blue-50/30 rounded-xl overflow-hidden shadow-lg border border-gray-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-200">
            <Bot size={26} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800 tracking-tight">AI Health Assistant</h1>
            <p className="text-sm text-slate-500">
              Hi {user?.full_name?.split(' ')[0] || 'there'}! Ask me anything about your health
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {messages.length > 0 && (
            <button
              onClick={handleClearHistory}
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              title="Clear chat history"
            >
              <Trash2 size={18} />
            </button>
          )}
          <div className="hidden md:flex items-center gap-2">
            <span className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-600 rounded-full text-xs font-semibold border border-emerald-100">
              <Sparkles size={12} />
              AI Ready
            </span>
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto px-4 md:px-6">
        <div className="max-w-4xl mx-auto py-6">
          {isLoadingHistory ? (
            <div className="flex flex-col items-center justify-center h-[50vh] text-center text-gray-400 space-y-4">
              <div className="animate-spin w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full"></div>
              <p className="text-sm text-gray-500">Loading your chat history...</p>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-6">
              {/* Welcome Icon */}
              <div className="w-24 h-24 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center">
                <MessageSquare size={42} className="text-blue-500" />
              </div>
              
              {/* Welcome Text */}
              <div className="space-y-2">
                <h3 className="text-xl font-semibold text-gray-700">How can I help you today?</h3>
                <p className="text-gray-500 max-w-md mx-auto">
                  I can answer questions about your medications, check reminders, identify pills from photos, and more.
                </p>
              </div>

              {/* Quick Actions */}
              <div className="mt-6 grid grid-cols-2 gap-3 w-full max-w-lg">
                {quickActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => handleSendMessage(action.query, null, null)}
                    className="flex items-center gap-3 px-4 py-3 text-left bg-white border border-gray-200 rounded-xl hover:bg-blue-50 hover:border-blue-200 transition-all group shadow-sm"
                  >
                    <span className="text-xl">{action.icon}</span>
                    <span className="text-sm font-medium text-gray-700 group-hover:text-blue-700">
                      {action.label}
                    </span>
                  </button>
                ))}
              </div>

              {/* Pill ID hint */}
              <div className="flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm mt-4">
                <Pill size={16} />
                <span>Click the pill icon below to identify a pill from a photo</span>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <OmniMessageBubble key={msg.id} message={msg} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <div className="bg-gradient-to-t from-white via-white to-transparent pt-4 pb-2">
        {identifyPillMode && (
          <div className="max-w-4xl mx-auto px-4 mb-2">
            <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-2.5 flex items-center gap-2 text-green-700 text-sm">
              <Pill size={16} className="shrink-0" />
              <span className="font-medium">Pill Identification Mode Active</span>
              <span className="text-green-600 hidden sm:inline">— Upload or take a photo of a pill to identify it</span>
              <button
                onClick={() => setIdentifyPillMode(false)}
                className="ml-auto text-green-600 hover:text-green-800"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
        <OmniChatInput 
          onSend={handleSendMessage} 
          isLoading={isLoading} 
          identifyPillMode={identifyPillMode}
          onTogglePillMode={togglePillMode}
        />
      </div>
    </div>
  );
};

export default AIAssistant;
