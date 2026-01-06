// src/pages/ChatBot.tsx - Admin AI Assistant
import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useAi } from '../hooks/useAi';
import { 
  Bot, User, Send, Mic, Image as ImageIcon, X, Loader2, 
  Trash2, Sparkles, Users, BarChart3, FileText, Settings,
  StopCircle, Camera, Pill, MessageSquare
} from 'lucide-react';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { CameraModal } from '../components/chat/CameraModal';
import { AudioPlayer } from '../components/chat/AudioPlayer';

// Admin suggestions
const ADMIN_SUGGESTIONS = [
  { icon: Users, label: 'Patient Overview', prompt: 'Show me an overview of all patients', color: 'bg-blue-500' },
  { icon: BarChart3, label: 'Adherence Stats', prompt: 'What are the overall medication adherence statistics?', color: 'bg-emerald-500' },
  { icon: FileText, label: 'Recent Activity', prompt: 'Show me recent patient activity and logs', color: 'bg-purple-500' },
  { icon: Settings, label: 'System Status', prompt: 'What is the current system status?', color: 'bg-amber-500' },
];

const ChatBot: React.FC = () => {
  const { user } = useAuth();
  const {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
    isInitializing,
    messagesEndRef,
    lastResponse
  } = useAi();

  const [inputMessage, setInputMessage] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [identifyPillMode, setIdentifyPillMode] = useState(false);
  
  const imageInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const audioPlayerRef = useRef<HTMLAudioElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [inputMessage]);

  // Play audio when response has audio
  useEffect(() => {
    if (lastResponse?.audio_path && lastResponse?.auto_play && audioPlayerRef.current) {
      const audioUrl = `http://localhost:8000/assistant/audio/stream/${lastResponse.audio_path.split('/').pop()}`;
      audioPlayerRef.current.src = audioUrl;
      audioPlayerRef.current.play().catch(() => {});
    }
  }, [lastResponse]);

  // Recording functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
        await sendMessage('', 'voice', audioFile, undefined);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingDuration(0);
      timerRef.current = window.setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } catch (err) {
      alert("Could not access microphone. Please check permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if ((!inputMessage.trim() && !imageFile) || isLoading) return;

    let inputType: 'text' | 'voice' | 'image' | 'multimodal' = 'text';
    if (imageFile) inputType = 'image';

    let messageText = inputMessage;
    if (identifyPillMode && imageFile && !inputMessage.includes('identify')) {
      messageText = inputMessage ? `Please identify this pill: ${inputMessage}` : 'Please identify this pill from the image';
    }

    await sendMessage(messageText || '', inputType, undefined, imageFile || undefined);
    
    setInputMessage('');
    clearImageFile();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setImagePreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleCameraCapture = (file: File) => {
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setIsCameraOpen(false);
  };

  const clearImageFile = () => {
    setImageFile(null);
    setImagePreview(null);
    if (imageInputRef.current) imageInputRef.current.value = '';
  };

  const handleSuggestionClick = (prompt: string) => {
    sendMessage(prompt, 'text');
  };

  if (isInitializing) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-[60vh]">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="mt-4 text-slate-600">Initializing AI Assistant...</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <CameraModal 
        isOpen={isCameraOpen} 
        onClose={() => setIsCameraOpen(false)} 
        onCapture={handleCameraCapture} 
      />
      
      <div className="flex flex-col h-[calc(100vh-6rem)] bg-gradient-to-b from-slate-50 to-white rounded-2xl overflow-hidden shadow-sm border border-slate-200">
        {/* Header */}
        <header className="bg-white border-b border-slate-100 px-4 md:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
                <Bot size={22} />
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-800">Admin AI Assistant</h1>
              <p className="text-xs text-slate-500">Healthcare management assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={clearMessages}
                className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                title="Clear chat"
              >
                <Trash2 size={18} />
              </button>
            )}
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 text-indigo-600 rounded-full text-xs font-medium">
              <Sparkles size={12} />
              <span>Admin Mode</span>
            </div>
          </div>
        </header>

        {/* Messages Area */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-6">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[50vh] text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-indigo-100 to-indigo-50 rounded-2xl flex items-center justify-center mb-4 shadow-sm">
                  <MessageSquare size={28} className="text-indigo-500" />
                </div>
                <h2 className="text-xl font-bold text-slate-800 mb-2">
                  Welcome, {user?.full_name?.split(' ')[0] || 'Admin'}! 👋
                </h2>
                <p className="text-slate-500 max-w-sm mb-8">
                  I'm your admin assistant. Ask me about patients, analytics, or upload images for pill identification.
                </p>

                <div className="grid grid-cols-2 gap-3 w-full max-w-md">
                  {ADMIN_SUGGESTIONS.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(suggestion.prompt)}
                      className="group flex items-center gap-3 p-4 bg-white border border-slate-200 rounded-xl hover:border-indigo-300 hover:shadow-md hover:shadow-indigo-100/50 transition-all text-left"
                    >
                      <div className={`p-2 ${suggestion.color} rounded-lg text-white group-hover:scale-110 transition-transform`}>
                        <suggestion.icon size={18} />
                      </div>
                      <span className="text-sm font-medium text-slate-700">{suggestion.label}</span>
                    </button>
                  ))}
                </div>

                <div className="mt-8 flex flex-wrap justify-center gap-2 text-xs text-slate-400">
                  <span className="px-2 py-1 bg-slate-100 rounded-full">💬 Text</span>
                  <span className="px-2 py-1 bg-slate-100 rounded-full">🎤 Voice</span>
                  <span className="px-2 py-1 bg-slate-100 rounded-full">📷 Image</span>
                  <span className="px-2 py-1 bg-slate-100 rounded-full">💊 Pill ID</span>
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex mb-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`flex max-w-[85%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'} gap-2 items-end`}>
                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-indigo-600 text-white'
                      }`}>
                        {message.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                      </div>
                      
                      <div className={`p-3 md:p-4 rounded-2xl text-sm ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white rounded-tr-none'
                          : 'bg-white border border-slate-100 text-slate-700 rounded-tl-none shadow-sm'
                      }`}>
                        {message.image_encoded?.base64 && (
                          <img
                            src={`data:image/png;base64,${message.image_encoded.base64}`}
                            alt="Response"
                            className="max-w-full h-auto rounded-lg mb-2"
                          />
                        )}
                        
                        <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                        
                        {message.transcription && (
                          <div className="mt-2 p-2 bg-slate-100 rounded-lg text-xs text-slate-600">
                            <span className="font-medium">Transcription:</span> {message.transcription}
                          </div>
                        )}
                        
                        {/* Audio Player for assistant responses */}
                        {message.role === 'assistant' && message.audio_path && (
                          <div className="mt-2">
                            <AudioPlayer 
                              src={`http://localhost:8000/assistant/audio/stream/${message.audio_path.split('/').pop()}`}
                              isUser={false}
                              autoPlay={message.auto_play}
                            />
                          </div>
                        )}
                        
                        <div className="flex justify-end mt-1">
                          <span className={`text-[10px] ${message.role === 'user' ? 'text-blue-200' : 'text-slate-400'}`}>
                            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex items-start gap-2 mb-4">
                    <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center text-white">
                      <Bot size={16} />
                    </div>
                    <div className="bg-white border border-slate-100 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
                      <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
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

        {/* Input Area */}
        <div className="bg-white border-t border-slate-100 pt-2 pb-4">
          <div className="w-full max-w-3xl mx-auto px-4">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-lg shadow-slate-200/50 overflow-hidden">
              
              {/* Image Preview */}
              {imagePreview && (
                <div className="p-3 bg-slate-50 border-b border-slate-100">
                  <div className="relative inline-block">
                    <img 
                      src={imagePreview} 
                      alt="Preview" 
                      className="h-20 w-20 object-cover rounded-xl border-2 border-white shadow-sm" 
                    />
                    <button 
                      onClick={clearImageFile}
                      className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-md"
                    >
                      <X size={14} />
                    </button>
                  </div>
                  {identifyPillMode && (
                    <span className="ml-3 text-xs text-emerald-600 font-medium">💊 Ready to identify</span>
                  )}
                </div>
              )}

              {/* Input Row */}
              <div className="flex items-end gap-1 p-2">
                <input
                  ref={imageInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  className="hidden"
                />
                
                <div className="flex items-center gap-0.5">
                  <button 
                    onClick={() => imageInputRef.current?.click()}
                    disabled={isLoading || isRecording}
                    className="p-2.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all disabled:opacity-40"
                    title="Upload image"
                  >
                    <ImageIcon size={20} />
                  </button>

                  <button 
                    onClick={() => setIsCameraOpen(true)}
                    disabled={isLoading || isRecording}
                    className="p-2.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all disabled:opacity-40"
                    title="Take photo"
                  >
                    <Camera size={20} />
                  </button>

                  <button 
                    onClick={() => setIdentifyPillMode(!identifyPillMode)}
                    disabled={isLoading || isRecording}
                    className={`p-2.5 rounded-xl transition-all disabled:opacity-40 ${
                      identifyPillMode 
                        ? 'bg-emerald-100 text-emerald-600' 
                        : 'text-slate-400 hover:text-emerald-600 hover:bg-emerald-50'
                    }`}
                    title={identifyPillMode ? 'Pill ID Mode: ON' : 'Enable Pill ID'}
                  >
                    <Pill size={20} />
                  </button>
                </div>

                <div className="flex-1 min-w-0">
                  {isRecording ? (
                    <div className="h-11 flex items-center px-4 bg-red-50 rounded-xl border border-red-200">
                      <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse mr-3" />
                      <span className="text-red-600 font-medium text-sm">
                        Recording {formatDuration(recordingDuration)}
                      </span>
                    </div>
                  ) : (
                    <textarea
                      ref={textareaRef}
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Message Admin AI..."
                      disabled={isLoading}
                      rows={1}
                      className="w-full bg-slate-50 border-0 rounded-xl py-2.5 px-4 text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:bg-white resize-none text-sm leading-relaxed"
                      style={{ minHeight: '44px', maxHeight: '120px' }}
                    />
                  )}
                </div>

                <div className="flex items-center gap-1">
                  <button
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={isLoading || !!imageFile}
                    className={`p-2.5 rounded-xl transition-all ${
                      isRecording 
                        ? 'bg-red-500 text-white hover:bg-red-600 shadow-md shadow-red-200' 
                        : 'text-slate-400 hover:text-indigo-600 hover:bg-indigo-50'
                    } disabled:opacity-40`}
                    title={isRecording ? "Stop recording" : "Voice message"}
                  >
                    {isRecording ? <StopCircle size={20} /> : <Mic size={20} />}
                  </button>

                  {!isRecording && (
                    <button
                      onClick={() => handleSendMessage()}
                      disabled={isLoading || (!inputMessage.trim() && !imageFile)}
                      className="p-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 active:scale-95 transition-all disabled:opacity-40 disabled:hover:bg-indigo-600 shadow-md shadow-indigo-200"
                    >
                      {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                    </button>
                  )}
                </div>
              </div>
            </div>

            <p className="text-center text-xs text-slate-400 mt-2">
              Press Enter to send • Shift+Enter for new line
            </p>
          </div>
        </div>
      </div>
      
      <audio ref={audioPlayerRef} style={{ display: 'none' }} />
    </DashboardLayout>
  );
};

export default ChatBot;
