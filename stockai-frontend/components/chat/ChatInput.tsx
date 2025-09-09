import { useState, KeyboardEvent } from 'react'
import { Send } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({ 
  onSendMessage, 
  disabled = false,
  placeholder = "주식에 대해 물어보세요... (예: 삼성전자 주가 분석해줘)"
}: ChatInputProps) {
  const [message, setMessage] = useState('')

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex items-center gap-2 border-t bg-white p-4">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          "flex-1 rounded-full border border-gray-300 px-4 py-2",
          "focus:border-blue-500 focus:outline-none",
          "disabled:bg-gray-100 disabled:cursor-not-allowed"
        )}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !message.trim()}
        className={cn(
          "rounded-full bg-blue-600 p-2 text-white transition-colors",
          "hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500",
          "disabled:bg-gray-300 disabled:cursor-not-allowed"
        )}
      >
        <Send size={20} />
      </button>
    </div>
  )
}