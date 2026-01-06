// src/hooks/useAi.ts
import { useState, useCallback, useRef, useEffect } from 'react';
import type { ChatMessage, ChatState, InputType, ChatResponse } from '../types/ai.types';
import { aiService } from '../services/ai.services';

// Simple UUID generator
const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

export const useAi = () => {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    isInitializing: true,
  });
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [state.messages]);

  // Initialize chat
  useEffect(() => {
    const initializeChat = async () => {
      try {
        const isHealthy = await aiService.healthCheck();
        if (isHealthy) {
          setState(prev => ({ ...prev, isInitializing: false }));
        } else {
          setState(prev => ({
            ...prev,
            isInitializing: false,
            error: 'AI service is currently unavailable'
          }));
        }
      } catch (error) {
        setState(prev => ({
          ...prev,
          isInitializing: false,
          error: 'Failed to connect to AI service'
        }));
      }
    };

    initializeChat();
  }, []);

  // Send a message to the AI
  const sendMessage = useCallback(async (
    content: string, 
    inputType: InputType = 'text',
    audioFile?: File,
    imageFile?: File
  ) => {
    if (!content.trim()) return;

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      input_type: inputType,
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    try {
      // Send to backend
      const response = await aiService.sendMessage({
        message: content.trim(),
        input_type: inputType,
        audio_file: audioFile,
        image_file: imageFile,
      });

      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: response.agent_response,
        timestamp: new Date(),
        input_type: inputType,
        emergency_detected: false,
        medication_handled: response.tools_used?.includes('get_user_medications'),
        transcription: response.transcription || undefined,
        image_encoded: response.image_encoded || undefined,
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        isLoading: false,
      }));

      setLastResponse(response);

    } catch (error: unknown) {
      const errorMessage = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
                          'Failed to send message. Please try again.';

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));

      // Add error message to chat
      const errorChatMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: `❌ Error: ${errorMessage}`,
        timestamp: new Date(),
        input_type: 'text',
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, errorChatMessage],
      }));
    }
  }, []);

  // Clear all messages
  const clearMessages = useCallback(() => {
    setState(prev => ({
      ...prev,
      messages: [],
      error: null,
    }));
  }, []);

  return {
    ...state,
    sendMessage,
    clearMessages,
    messagesEndRef,
    lastResponse,
  };
};
