// src/services/omnichat.service.ts
// OmniChat Service - Following ai.services.ts patterns using axios api instance
import api from './api';
import type { OmniChatRequest, OmniChatResponse, ChatHistoryResponse } from '../types/omnichat.types';

const API_URL = 'http://localhost:8000';

export const omniChatService = {
  /**
   * Send a multimodal message to the OmniChat assistant
   * Supports text, audio (Blob), and image (File) inputs
   */
  sendMessage: async (request: OmniChatRequest): Promise<OmniChatResponse> => {
    // Create FormData for multipart/form-data request
    const formData = new FormData();
    
    // Add text if provided
    if (request.message) {
      formData.append('text', request.message);
    }
    
    // Add audio file if provided (Blob with filename for FastAPI)
    if (request.audio_file) {
      formData.append('audio_file', request.audio_file, 'recording.webm');
    }
    
    // Add image file if provided
    if (request.image_file) {
      formData.append('image_file', request.image_file);
    }
    
    // Default values matching backend Pydantic model
    // Note: FastAPI parses "true"/"false" strings to boolean for Form fields
    formData.append('output_audio', request.output_audio === false ? 'false' : 'true');
    formData.append('tts_provider', request.tts_provider || 'gtts');
    formData.append('tool_choice', request.tool_choice || 'main');

    // Increase timeout for AI/LLM requests that may take longer due to retries
    const response = await api.post<OmniChatResponse>(
      `${API_URL}/assistant/query`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 180000, // 3 minutes timeout for AI requests with TTS
      }
    );
    return response.data;
  },

  /**
   * Check if OmniChat service is available
   */
  healthCheck: async (): Promise<boolean> => {
    try {
      await api.get(`${API_URL}/assistant/health`);
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Get stream URL for audio playback
   */
  getStreamUrl: (audioPath: string): string => {
    if (!audioPath) return '';
    // Extract filename from path (handle both forward and back slashes)
    const filename = audioPath.split(/[/\\]/).pop();
    return `${API_URL}/assistant/audio/stream/${filename}`;
  },

  /**
   * Get chat history for the current user
   */
  getChatHistory: async (limit = 50, offset = 0): Promise<ChatHistoryResponse> => {
    const response = await api.get<ChatHistoryResponse>(
      `${API_URL}/assistant/history`,
      { params: { limit, offset } }
    );
    return response.data;
  },

  /**
   * Clear all chat history for the current user
   */
  clearChatHistory: async (): Promise<{ message: string; deleted_count: number }> => {
    const response = await api.delete<{ message: string; deleted_count: number }>(
      `${API_URL}/assistant/history`
    );
    return response.data;
  },
};

// Export individual functions for convenience
export const { sendMessage, healthCheck, getStreamUrl, getChatHistory, clearChatHistory } = omniChatService;
