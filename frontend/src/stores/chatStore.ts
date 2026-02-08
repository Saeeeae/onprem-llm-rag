/**
 * Chat Store using Zustand
 */
import { create } from 'zustand';
import { apiClient, Source } from '../api/client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
}

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  currentSources: Source[];
  topK: number;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  sendQuery: (query: string) => Promise<void>;
  setTopK: (k: number) => void;
  clearChat: () => void;
}

const generateId = () => Math.random().toString(36).substring(7);

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  currentSources: [],
  topK: 5,

  addMessage: (message) => {
    const newMessage: Message = {
      ...message,
      id: generateId(),
      timestamp: new Date(),
    };
    set((state) => ({ messages: [...state.messages, newMessage] }));
  },

  sendQuery: async (query: string) => {
    const { addMessage, topK } = get();

    // Add user message
    addMessage({ role: 'user', content: query });

    set({ isLoading: true, currentSources: [] });

    try {
      let assistantContent = '';
      let sources: Source[] = [];

      // Stream response
      for await (const chunk of apiClient.queryStream({ query, top_k: topK })) {
        if (chunk.type === 'sources' && chunk.documents) {
          sources = chunk.documents;
          set({ currentSources: sources });
        } else if (chunk.type === 'token' && chunk.content) {
          assistantContent += chunk.content;
          // Update the last assistant message or create new one
          set((state) => {
            const messages = [...state.messages];
            const lastMessage = messages[messages.length - 1];

            if (lastMessage?.role === 'assistant') {
              messages[messages.length - 1] = {
                ...lastMessage,
                content: assistantContent,
                sources,
              };
            } else {
              messages.push({
                id: generateId(),
                role: 'assistant',
                content: assistantContent,
                sources,
                timestamp: new Date(),
              });
            }
            return { messages };
          });
        }
      }
    } catch (error) {
      addMessage({
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    } finally {
      set({ isLoading: false });
    }
  },

  setTopK: (k: number) => set({ topK: k }),

  clearChat: () => set({ messages: [], currentSources: [] }),
}));
