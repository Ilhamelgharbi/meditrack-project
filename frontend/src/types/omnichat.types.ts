// src/types/omnichat.types.ts
// Types for OmniChat AI Assistant - Following ai.types.ts patterns

export type OmniInputType = 'text' | 'voice' | 'image' | 'multimodal';

// Request type - matches ChatRequest pattern
export interface OmniChatRequest {
  message: string;
  input_type?: OmniInputType;
  audio_file?: Blob;
  image_file?: File;
  output_audio?: boolean;
  tts_provider?: string;
  tool_choice?: string;
}

// Response type - matches ChatResponse pattern
export interface OmniChatResponse {
  agent_response: string;
  transcription?: string | null;
  audio_path?: string | null;
  uploaded_audio_path?: string | null;
  auto_play?: boolean;
  image_encoded?: { base64: string } | null;
  tools_used?: string[] | null;
  intent?: string | null;
}

// Message type - matches ChatMessage pattern
export interface OmniChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  input_type?: OmniInputType;
  imageUrl?: string;
  audioUrl?: string;
  isAudioAutoPlay?: boolean;
  toolsUsed?: string[];
  intent?: string;
  transcription?: string;
}

// State type - matches ChatState pattern
export interface OmniChatState {
  messages: OmniChatMessage[];
  isLoading: boolean;
  error: string | null;
  isInitializing: boolean;
}

// Component Props
export interface OmniChatInputProps {
  onSend: (text: string, image: File | null, audioBlob: Blob | null, identifyPill?: boolean) => void;
  isLoading: boolean;
  identifyPillMode?: boolean;
  onTogglePillMode?: () => void;
}

export interface AudioPlayerProps {
  src: string;
  isUser: boolean;
  autoPlay?: boolean;
}

export interface CameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCapture: (file: File) => void;
}

export interface MessageBubbleProps {
  message: OmniChatMessage;
}

// Chat History Types
export interface ChatHistoryMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  input_type?: string | null;
  image_url?: string | null;
  audio_url?: string | null;
  tools_used?: string | null;
  intent?: string | null;
  timestamp?: string | null;
}

export interface ChatHistoryResponse {
  messages: ChatHistoryMessage[];
  total_count: number;
}
