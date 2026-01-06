// src/components/chat/CameraModal.tsx
import React, { useRef, useState, useEffect } from 'react';
import { X, Camera, RefreshCw, Check, SwitchCamera } from 'lucide-react';
import type { CameraModalProps } from '../../types/omnichat.types';

export const CameraModal: React.FC<CameraModalProps> = ({ isOpen, onClose, onCapture }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<'user' | 'environment'>('environment');

  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
  }, [isOpen, facingMode]);

  const startCamera = async () => {
    // Stop any existing stream before starting a new one
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facingMode }
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setError(null);
      setCapturedImage(null);
    } catch (err) {
      console.error("Camera error:", err);
      setError("Unable to access camera. Please check permissions or ensure you are using HTTPS.");
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  };

  const toggleCamera = () => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
  };

  const capture = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    // Set canvas dimensions to match video stream
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
      setCapturedImage(dataUrl);
    }
  };

  const retake = () => {
    setCapturedImage(null);
  };

  const confirm = () => {
    if (!capturedImage) return;
    
    // Convert DataURL to File
    fetch(capturedImage)
      .then(res => res.blob())
      .then(blob => {
        const file = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
        onCapture(file);
      });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] bg-black flex flex-col animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex justify-between items-center p-4 bg-black/50 absolute top-0 w-full z-10 text-white backdrop-blur-sm">
        <button onClick={onClose} className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
          <X size={24} />
        </button>
        <span className="font-semibold tracking-wide">Take Photo</span>
        
        {!capturedImage && !error ? (
          <button 
            onClick={toggleCamera} 
            className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
            title="Switch Camera"
          >
            <SwitchCamera size={24} />
          </button>
        ) : (
          <div className="w-10"></div> 
        )}
      </div>

      {/* Main View */}
      <div className="flex-1 relative flex items-center justify-center bg-black overflow-hidden w-full">
        {error ? (
          <div className="text-white text-center p-6 max-w-sm">
            <Camera size={48} className="mx-auto mb-4 text-gray-500" />
            <p className="mb-4 text-gray-300">{error}</p>
            <button onClick={onClose} className="px-6 py-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors">
              Close Camera
            </button>
          </div>
        ) : capturedImage ? (
          <img src={capturedImage} alt="Captured" className="w-full h-full object-contain" />
        ) : (
          <video 
            ref={videoRef} 
            autoPlay 
            playsInline 
            muted
            className={`w-full h-full object-cover ${facingMode === 'user' ? 'scale-x-[-1]' : ''}`}
          />
        )}
        <canvas ref={canvasRef} className="hidden" />
      </div>

      {/* Controls */}
      <div className="p-8 bg-black/80 backdrop-blur-md flex justify-center items-center gap-12 safe-area-bottom">
        {capturedImage ? (
          <>
            <button 
              onClick={retake}
              className="flex flex-col items-center gap-2 text-gray-300 hover:text-white transition-colors"
            >
              <div className="p-4 rounded-full bg-white/10">
                <RefreshCw size={24} />
              </div>
              <span className="text-xs font-medium">Retake</span>
            </button>
            <button 
              onClick={confirm}
              className="flex flex-col items-center gap-2 text-white hover:text-blue-200 transition-colors"
            >
              <div className="p-4 rounded-full bg-blue-600 shadow-lg shadow-blue-900/50">
                <Check size={32} />
              </div>
              <span className="text-xs font-medium">Use Photo</span>
            </button>
          </>
        ) : (
          !error && (
            <button 
              onClick={capture}
              className="w-20 h-20 rounded-full border-4 border-white/80 flex items-center justify-center hover:bg-white/10 transition-all active:scale-95"
            >
              <div className="w-16 h-16 bg-white rounded-full"></div>
            </button>
          )
        )}
      </div>
    </div>
  );
};

export default CameraModal;
