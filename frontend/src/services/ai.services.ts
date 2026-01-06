// src/services/ai.services.ts
import api from './api';
import type { ChatRequest, ChatResponse } from '../types/ai.types';

const API_URL = 'http://localhost:8000';

export const aiService = {
  /**
   * Send a message to the AI assistant
   */
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    // Create FormData for multipart/form-data request
    const formData = new FormData();
    
    // Add text if provided
    if (request.message) {
      formData.append('text', request.message);
    }
    
    // Add audio file if provided
    if (request.audio_file) {
      formData.append('audio_file', request.audio_file);
    }
    
    // Add image file if provided
    if (request.image_file) {
      formData.append('image_file', request.image_file);
    }
    
    formData.append('output_audio', 'true');
    formData.append('tool_choice', 'main');

    const response = await api.post<ChatResponse>(
      `${API_URL}/assistant/query`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Check if AI service is available
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
   * Stream audio from the backend
   */
  streamAudio: (filename: string): string => {
    return `${API_URL}/assistant/audio/stream/${filename}`;
  },
};
