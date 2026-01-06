// src/components/chat/OmniMessageBubble.tsx
import React from 'react';
import { Bot, User, Cpu, Sparkles, FileText, Pill } from 'lucide-react';
import type { MessageBubbleProps } from '../../types/omnichat.types';
import { AudioPlayer } from './AudioPlayer';

// Format tool names for display
const formatToolName = (tool: string): string => {
  // Replace underscores with spaces and capitalize each word
  return tool
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

// Get icon for specific tool types
const getToolIcon = (tool: string) => {
  if (tool.includes('medication')) return Pill;
  if (tool.includes('document') || tool.includes('medical')) return FileText;
  return Cpu;
};

export const OmniMessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[95%] sm:max-w-[80%] md:max-w-[70%] ${isUser ? 'flex-row-reverse' : 'flex-row'} gap-2 items-end`}>
        
        {/* External Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm overflow-hidden ${
          isUser ? 'bg-blue-600 text-white' : 'bg-emerald-600 text-white'
        }`}>
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </div>

        {/* Bubble Content */}
        <div className={`flex flex-col relative shadow-sm text-sm md:text-base transition-all ${
          isUser 
            ? 'bg-blue-600 text-white rounded-2xl rounded-tr-none' 
            : 'bg-white border border-gray-100 text-slate-700 rounded-2xl rounded-tl-none'
        } ${message.audioUrl ? 'p-3' : 'p-3 md:p-4'}`}>
          
          {/* Metadata Badges (Assistant only) - Always show when available */}
          {!isUser && (message.intent || (message.toolsUsed && message.toolsUsed.length > 0)) && (
            <div className="flex flex-wrap gap-2 mb-3">
              {message.intent && (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-[10px] uppercase font-bold tracking-wide bg-emerald-50 text-emerald-600 border border-emerald-100">
                  <Sparkles size={10} />
                  {message.intent}
                </span>
              )}
              {message.toolsUsed?.map((tool, idx) => {
                const IconComponent = getToolIcon(tool);
                return (
                  <span key={idx} className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-[10px] uppercase font-bold tracking-wide bg-blue-50 text-blue-600 border border-blue-100">
                    <IconComponent size={10} />
                    {formatToolName(tool)}
                  </span>
                );
              })}
            </div>
          )}

          {/* Image Attachment */}
          {message.imageUrl && (
            <div className="mb-2 relative group overflow-hidden rounded-lg border border-black/5 bg-black/5">
              <img 
                src={message.imageUrl} 
                alt="Attachment" 
                className="max-w-full h-auto object-cover max-h-80 w-full" 
              />
            </div>
          )}

          {/* Text Content */}
          {message.content && !message.audioUrl && (
            <p className="whitespace-pre-wrap leading-relaxed break-words">
              {message.content}
            </p>
          )}

          {/* Audio Player (Custom WhatsApp Style) */}
          {message.audioUrl && (
            <AudioPlayer 
              src={message.audioUrl} 
              isUser={isUser} 
              autoPlay={message.isAudioAutoPlay} 
            />
          )}

          {/* Text Content WITH Audio (Caption) */}
          {message.content && message.audioUrl && message.role === 'assistant' && (
             <div className="mt-2 pt-2 border-t border-gray-100 text-sm opacity-90">
                {message.content}
             </div>
          )}
          
          {/* Timestamp (Only for text messages, Audio has its own timer) */}
          {!message.audioUrl && (
            <div className={`flex justify-end mt-1`}>
              <span className={`text-[10px] ${isUser ? 'text-blue-100/80' : 'text-slate-400'}`}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OmniMessageBubble;
