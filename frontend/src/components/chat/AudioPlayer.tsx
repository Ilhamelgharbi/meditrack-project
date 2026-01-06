// src/components/chat/AudioPlayer.tsx
import React, { useEffect, useRef, useState, useMemo } from 'react';
import { Play, Pause, Bot, Mic } from 'lucide-react';
import type { AudioPlayerProps } from '../../types/omnichat.types';

// Format seconds into MM:SS
const formatTime = (seconds: number) => {
  if (!seconds || isNaN(seconds)) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ src, isUser, autoPlay }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const waveformRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  // Generate random bar heights for visualization
  const bars = useMemo(() => {
    return Array.from({ length: 36 }, () => Math.floor(Math.random() * 20) + 12);
  }, []);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (autoPlay) {
      audio.play().catch(e => console.log("Autoplay blocked:", e));
    }

    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };
    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onLoadedMetadata = () => {
      if (audio.duration !== Infinity) {
        setDuration(audio.duration);
      }
    };
    const onError = (e: Event) => {
      console.error('Audio load error:', e, 'src:', src);
    };

    audio.addEventListener('play', onPlay);
    audio.addEventListener('pause', onPause);
    audio.addEventListener('ended', onEnded);
    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('loadedmetadata', onLoadedMetadata);
    audio.addEventListener('error', onError);

    return () => {
      audio.removeEventListener('play', onPlay);
      audio.removeEventListener('pause', onPause);
      audio.removeEventListener('ended', onEnded);
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('loadedmetadata', onLoadedMetadata);
      audio.removeEventListener('error', onError);
    };
  }, [autoPlay, src]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!waveformRef.current || !audioRef.current || !duration) return;
    const rect = waveformRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.min(Math.max(x / rect.width, 0), 1);
    audioRef.current.currentTime = percentage * duration;
  };

  const progress = duration > 0 ? currentTime / duration : 0;

  const buttonClass = isUser 
    ? 'bg-black/10 text-white hover:bg-black/20' 
    : 'bg-gray-200 text-slate-500 pl-0.5 hover:bg-gray-300';
  
  const metadataColor = isUser ? 'text-blue-100' : 'text-slate-400';

  return (
    <div className="flex items-center gap-3 select-none min-w-[200px] sm:min-w-[260px]">
      <audio ref={audioRef} src={src} preload="metadata" className="hidden" />
      
      {/* Play/Pause Circle Button */}
      <button 
        onClick={togglePlay}
        className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all active:scale-95 ${buttonClass}`}
      >
        {isPlaying ? (
          <Pause size={18} fill="currentColor" />
        ) : (
          <Play size={18} fill="currentColor" className="ml-0.5" />
        )}
      </button>

      <div className="flex-1 flex flex-col gap-1 justify-center">
        {/* Waveform Visualization */}
        <div 
          ref={waveformRef}
          onClick={handleSeek}
          className="flex items-center gap-[2px] h-8 cursor-pointer group"
        >
          {bars.map((height, index) => {
            const barProgress = index / bars.length;
            const isPlayed = barProgress < progress;
            
            let barColor;
            if (isUser) {
              barColor = isPlayed ? 'bg-white' : 'bg-white/40';
            } else {
              barColor = isPlayed ? 'bg-blue-500' : 'bg-slate-300';
            }

            return (
              <div
                key={index}
                className={`w-[3px] sm:w-1 rounded-full transition-colors duration-100 ${barColor}`}
                style={{ height: `${height}px` }}
              />
            );
          })}
        </div>

        {/* Footer: Duration & Icon */}
        <div className={`flex items-center gap-1 text-[10px] font-medium leading-none ${metadataColor}`}>
           <span>{formatTime(currentTime || duration)}</span>
           <span className="opacity-60">•</span>
           {isUser ? <Mic size={10} className="opacity-80" /> : <Bot size={10} className="opacity-80" />}
        </div>
      </div>
    </div>
  );
};

export default AudioPlayer;
