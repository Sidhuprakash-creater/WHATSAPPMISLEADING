import { create } from 'zustand';

export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  type?: 'text' | 'url' | 'image' | 'video';
  analysisResult?: any;
  progressStep?: {
    step: string;
    message: string;
    progress: number;
  };
};

interface ChatState {
  messages: Message[];
  isAnalyzing: boolean;
  history: any[];
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setAnalyzing: (val: boolean) => void;
  recordAnalysis: (result: any) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your Misinformation Detector. Send me any news, link, or image from WhatsApp that you find suspicious, and I'll analyze it for you.",
      timestamp: Date.now(),
    },
  ],
  isAnalyzing: false,
  history: [],
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  updateMessage: (id, updates) => 
    set((state) => ({
      messages: state.messages.map((m) => (m.id === id ? { ...m, ...updates } : m)),
    })),
  setAnalyzing: (val) => set({ isAnalyzing: val }),
  recordAnalysis: (result) => set((state) => ({ 
    history: [result, ...state.history].slice(0, 50) 
  })),
}));
