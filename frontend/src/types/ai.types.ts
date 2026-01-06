// src/types/ai.types.ts
export type InputType = 'text' | 'voice' | 'image' | 'multimodal';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  input_type: InputType;
  emergency_detected?: boolean;
  medication_handled?: boolean;
  transcription?: string;
  image_encoded?: { base64: string };
  audio_path?: string;
  auto_play?: boolean;
}

export interface ChatRequest {
  message: string;
  input_type?: InputType;
  audio_file?: File;
  image_file?: File;
}

export interface ChatResponse {
  agent_response: string;
  transcription?: string | null;
  audio_path?: string | null;
  auto_play?: boolean;
  image_encoded?: { base64: string } | null;
  tools_used?: string[];
  intent?: string;
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  isInitializing: boolean;
}

export interface ChatContextType {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string, inputType?: InputType) => Promise<void>;
  clearMessages: () => void;
  isInitializing: boolean;
}
