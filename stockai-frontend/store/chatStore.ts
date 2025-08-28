import { create } from 'zustand'
import { Message } from '@/types/chat'

interface ChatStore {
  messages: Message[]
  isTyping: boolean
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void
  setTyping: (isTyping: boolean) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isTyping: false,
  
  addMessage: (message) => {
    const newMessage: Message = {
      ...message,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date()
    }
    
    set((state) => ({
      messages: [...state.messages, newMessage]
    }))
  },
  
  setTyping: (isTyping) => set({ isTyping }),
  
  clearMessages: () => set({ messages: [] })
}))