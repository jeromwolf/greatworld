import { useEffect, useRef, useState, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'
import { WebSocketMessage } from '@/types/chat'

interface UseWebSocketProps {
  url: string
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Error) => void
}

export function useWebSocket({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  onError
}: UseWebSocketProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isReconnecting, setIsReconnecting] = useState(false)
  const socketRef = useRef<WebSocket | null>(null)
  const clientId = useRef(`client_${Math.random().toString(36).substr(2, 9)}`)
  const reconnectCount = useRef(0)
  const maxReconnectAttempts = 5
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    // 이미 연결 중이거나 연결되어 있으면 중복 연결 방지
    if (socketRef.current?.readyState === WebSocket.CONNECTING ||
        socketRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const ws = new WebSocket(`${url}/${clientId.current}`)
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setIsReconnecting(false)
        reconnectCount.current = 0  // 연결 성공 시 재연결 카운트 리셋
        onConnect?.()
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data) as WebSocketMessage
        onMessage?.(data)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        socketRef.current = null
        onDisconnect?.()
        
        // 최대 재연결 시도 횟수 체크
        if (reconnectCount.current < maxReconnectAttempts) {
          const backoffDelay = Math.min(1000 * Math.pow(2, reconnectCount.current), 30000)
          reconnectCount.current++
          
          console.log(`Reconnecting in ${backoffDelay}ms (attempt ${reconnectCount.current}/${maxReconnectAttempts})`)
          setIsReconnecting(true)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, backoffDelay)
        } else {
          console.log('Max reconnection attempts reached')
          setIsReconnecting(false)
          onError?.(new Error('최대 재연결 시도 횟수를 초과했습니다. 페이지를 새로고침해주세요.'))
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        onError?.(new Error('WebSocket connection error'))
      }

      socketRef.current = ws
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      onError?.(error as Error)
      setIsReconnecting(false)
    }
  }, [url, onMessage, onConnect, onDisconnect, onError])

  const sendMessage = useCallback((message: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        message,
        timestamp: new Date().toISOString()
      }))
      return true
    }
    return false
  }, [])

  const disconnect = useCallback(() => {
    // 재연결 타이머 취소
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    // WebSocket 연결 종료
    if (socketRef.current) {
      socketRef.current.close()
      socketRef.current = null
    }
    
    setIsConnected(false)
    setIsReconnecting(false)
    reconnectCount.current = 0
  }, [])

  // 수동 재연결 함수
  const reconnect = useCallback(() => {
    disconnect()
    reconnectCount.current = 0
    setTimeout(() => {
      connect()
    }, 100)
  }, [connect, disconnect])

  useEffect(() => {
    connect()
    
    return () => {
      disconnect()
    }
  }, []) // 의존성 배열에서 connect, disconnect 제거하여 무한 루프 방지

  return {
    isConnected,
    isReconnecting,
    sendMessage,
    disconnect,
    reconnect: connect
  }
}