// src/components/chat/OmniChatInput.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Image as ImageIcon, X, Loader2, StopCircle, Camera, Pill } from 'lucide-react';
import { CameraModal } from './CameraModal';
import type { OmniChatInputProps } from '../../types/omnichat.types';

export const OmniChatInput: React.FC<OmniChatInputProps> = ({ 
  onSend, 
  isLoading, 
  identifyPillMode, 
  onTogglePillMode 
}) => {
  const [text, setText] = useState('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  
  // Camera State
  const [isCameraOpen, setIsCameraOpen] = useState(false);

  // Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  
  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [text]);

  // Clean up previews
  useEffect(() => {
    return () => {
      if (imagePreview) URL.revokeObjectURL(imagePreview);
    };
  }, [imagePreview]);

  // Handle Image Selection
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleCameraCapture = (file: File) => {
    setSelectedImage(file);
    setImagePreview(URL.createObjectURL(file));
    setIsCameraOpen(false);
  };

  const removeImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Handle Recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        handleSend(audioBlob); 
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

  // Handle Submission
  const handleSend = (audioBlob: Blob | null = null) => {
    if ((!text.trim() && !selectedImage && !audioBlob) || isLoading) return;

    onSend(text, selectedImage, audioBlob, identifyPillMode);
    
    setText('');
    removeImage();
    audioChunksRef.current = [];
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4">
      <CameraModal 
        isOpen={isCameraOpen} 
        onClose={() => setIsCameraOpen(false)} 
        onCapture={handleCameraCapture} 
      />

      {/* Main Input Container */}
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
                onClick={removeImage}
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
          
          {/* Action Buttons Group */}
          <div className="flex items-center gap-0.5">
            {/* File Upload */}
            <input 
              type="file" 
              accept="image/*" 
              className="hidden" 
              ref={fileInputRef} 
              onChange={handleImageSelect} 
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading || isRecording}
              className="p-2.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all disabled:opacity-40"
              title="Upload image"
            >
              <ImageIcon size={20} />
            </button>

            {/* Camera Button */}
            <button 
              onClick={() => setIsCameraOpen(true)}
              disabled={isLoading || isRecording}
              className="p-2.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all disabled:opacity-40"
              title="Take photo"
            >
              <Camera size={20} />
            </button>

            {/* Pill Identify Toggle */}
            {onTogglePillMode && (
              <button 
                onClick={onTogglePillMode}
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
            )}
          </div>

          {/* Text Input / Recording Display */}
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
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message MediTrack AI..."
                disabled={isLoading}
                rows={1}
                className="w-full bg-slate-50 border-0 rounded-xl py-2.5 px-4 text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:bg-white resize-none text-sm leading-relaxed"
                style={{ minHeight: '44px', maxHeight: '120px' }}
              />
            )}
          </div>

          {/* Voice Record / Send Button */}
          <div className="flex items-center gap-1">
            {/* Voice Record */}
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isLoading || !!selectedImage}
              className={`p-2.5 rounded-xl transition-all ${
                isRecording 
                  ? 'bg-red-500 text-white hover:bg-red-600 shadow-md shadow-red-200' 
                  : 'text-slate-400 hover:text-blue-600 hover:bg-blue-50'
              } disabled:opacity-40`}
              title={isRecording ? "Stop recording" : "Voice message"}
            >
              {isRecording ? <StopCircle size={20} /> : <Mic size={20} />}
            </button>

            {/* Send Button */}
            {!isRecording && (
              <button
                onClick={() => handleSend()}
                disabled={isLoading || (!text.trim() && !selectedImage)}
                className="p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 active:scale-95 transition-all disabled:opacity-40 disabled:hover:bg-blue-600 shadow-md shadow-blue-200"
              >
                {isLoading ? (
                  <Loader2 size={20} className="animate-spin" />
                ) : (
                  <Send size={20} />
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Helper Text */}
      <p className="text-center text-xs text-slate-400 mt-2">
        Press Enter to send • Shift+Enter for new line
      </p>
    </div>
  );
};

export default OmniChatInput;
