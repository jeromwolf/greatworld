import { Message } from '@/types/chat'
import { cn } from '@/lib/utils'
import { SentimentIndicator } from './SentimentIndicator'

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.type === 'user'
  const isBot = message.type === 'bot'
  const isSystem = message.type === 'system'

  // 마크다운 스타일 렌더링
  const renderContent = (content: string) => {
    return content
      .replace(/\*\*(.+?)\*\*/g, '<strong class="text-blue-600 font-semibold">$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br />')
      .replace(/• /g, '&bull; ')
  }

  return (
    <div
      className={cn(
        'mb-4 flex',
        isUser && 'justify-end',
        isBot && 'justify-start',
        isSystem && 'justify-center'
      )}
    >
      <div
        className={cn(
          'max-w-[70%] rounded-lg px-4 py-2',
          isUser && 'bg-blue-600 text-white',
          isBot && 'bg-white border border-gray-200 shadow-sm',
          isSystem && 'bg-blue-50 text-blue-800 text-sm'
        )}
      >
        <div 
          className="whitespace-pre-wrap"
          dangerouslySetInnerHTML={{ __html: renderContent(message.content) }}
        />
        
        {/* 감성 분석 결과 표시 */}
        {message.data?.sentiment !== undefined && (
          <SentimentIndicator 
            sentiment={message.data.sentiment}
            sources={message.data.sources}
          />
        )}
        
        {/* 디버그 모드에서 NLU 결과 표시 */}
        {message.nluResult && process.env.NODE_ENV === 'development' && (
          <details className="mt-2">
            <summary className="cursor-pointer text-xs text-gray-500">분석 상세</summary>
            <div className="mt-1 rounded bg-gray-50 p-2 text-xs font-mono">
              <p>의도: {message.nluResult.intent}</p>
              <p>신뢰도: {(message.nluResult.confidence * 100).toFixed(1)}%</p>
              {message.nluResult.entities && Object.keys(message.nluResult.entities).length > 0 && (
                <pre className="mt-1">{JSON.stringify(message.nluResult.entities, null, 2)}</pre>
              )}
            </div>
          </details>
        )}
        
        <p className={cn('mt-2 text-xs opacity-70', isUser && 'text-right')}>
          {message.timestamp.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </p>
      </div>
    </div>
  )
}