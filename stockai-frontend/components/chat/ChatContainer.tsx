'use client'

import { useEffect, useRef } from 'react'
import { useChatStore } from '@/store/chatStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { TypingIndicator } from './TypingIndicator'
import { ChatExamples } from './ChatExamples'
import { WebSocketMessage } from '@/types/chat'

export function ChatContainer() {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, isTyping, addMessage, setTyping } = useChatStore()
  
  const { isConnected, isReconnecting, sendMessage, reconnect } = useWebSocket({
    url: 'ws://localhost:8200/ws',
    onMessage: (data: WebSocketMessage) => {
      setTyping(false)
      addMessage({
        type: data.type as 'bot' | 'system',
        content: data.message,
        data: data.data,
        nluResult: data.nlu_result
      })
    },
    onConnect: () => {
      console.log('Connected to StockAI')
    },
    onDisconnect: () => {
      console.log('Disconnected from StockAI')
      addMessage({
        type: 'system',
        content: '서버와의 연결이 끊어졌습니다. 재연결을 시도합니다...'
      })
    },
    onError: (error) => {
      console.error('WebSocket error:', error)
      addMessage({
        type: 'system',
        content: '연결 오류가 발생했습니다.'
      })
    }
  })

  const handleSendMessage = (message: string) => {
    if (!isConnected) {
      addMessage({
        type: 'system',
        content: '서버와 연결되지 않았습니다. 잠시 후 다시 시도해주세요.'
      })
      return
    }

    // 사용자 메시지 추가
    addMessage({
      type: 'user',
      content: message
    })

    // 서버로 메시지 전송
    const sent = sendMessage(message)
    if (sent) {
      setTyping(true)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-blue-600">StockAI</h1>
            <p className="text-sm text-gray-600">AI 기반 실시간 주식 분석 서비스</p>
          </div>
          <div className="flex items-center gap-2">
            {!isConnected && !isReconnecting && (
              <button
                onClick={reconnect}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                재연결
              </button>
            )}
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : isReconnecting ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <span className="text-sm text-gray-600">
                {isConnected ? '연결됨' : isReconnecting ? '재연결 중...' : '연결 끊김'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <h2 className="mb-4 text-2xl font-semibold text-gray-700">
                무엇을 도와드릴까요?
              </h2>
              <ChatExamples onExampleClick={handleSendMessage} />
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl p-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isTyping && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="mx-auto w-full max-w-3xl">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={!isConnected}
          placeholder={
            isConnected
              ? "주식에 대해 물어보세요... (예: 삼성전자 주가 분석해줘)"
              : "서버에 연결 중..."
          }
        />
      </div>
    </div>
  )
}