import { SentimentSource } from '@/types/chat'
import { cn } from '@/lib/utils'

interface SentimentIndicatorProps {
  sentiment: number
  sources?: Record<string, SentimentSource>
}

export function SentimentIndicator({ sentiment, sources }: SentimentIndicatorProps) {
  const getSentimentColor = (score: number) => {
    if (score >= 0.6) return 'bg-green-500'
    if (score >= 0.2) return 'bg-green-400'
    if (score >= -0.2) return 'bg-yellow-400'
    if (score >= -0.6) return 'bg-orange-400'
    return 'bg-red-500'
  }

  const getSentimentLabel = (score: number) => {
    if (score >= 0.6) return '매우 긍정적'
    if (score >= 0.2) return '긍정적'
    if (score >= -0.2) return '중립적'
    if (score >= -0.6) return '부정적'
    return '매우 부정적'
  }

  const getSentimentEmoji = (score: number) => {
    if (score >= 0.6) return '🚀'
    if (score >= 0.2) return '📈'
    if (score >= -0.2) return '➖'
    if (score >= -0.6) return '📉'
    return '🐻'
  }

  return (
    <div className="mt-3 rounded-lg bg-gray-50 p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">감성 분석</span>
        <span className="flex items-center gap-2">
          <span className="text-lg">{getSentimentEmoji(sentiment)}</span>
          <span className="text-sm font-medium">{getSentimentLabel(sentiment)}</span>
        </span>
      </div>
      
      {/* 감성 점수 바 */}
      <div className="mb-3 h-6 w-full rounded-full bg-gray-200 overflow-hidden">
        <div
          className={cn(
            'h-full transition-all duration-500',
            getSentimentColor(sentiment)
          )}
          style={{ width: `${(sentiment + 1) * 50}%` }}
        />
      </div>
      
      {/* 데이터 소스별 분석 */}
      {sources && Object.keys(sources).length > 0 && (
        <div className="mt-3 space-y-2">
          <p className="text-xs font-medium text-gray-600">데이터 소스별 분석:</p>
          {Object.entries(sources).map(([source, data]) => (
            <div key={source} className="flex items-center justify-between text-xs">
              <span className="text-gray-600">
                {source === 'news' && '뉴스'}
                {source === 'reddit' && 'Reddit'}
                {source === 'disclosure' && '공시'}
                {source === 'stocktwits' && 'StockTwits'}
              </span>
              <div className="flex items-center gap-2">
                <span className={cn(
                  'px-2 py-0.5 rounded-full text-white text-xs',
                  getSentimentColor(data.sentiment)
                )}>
                  {data.sentiment > 0 ? '+' : ''}{data.sentiment.toFixed(2)}
                </span>
                {data.count && (
                  <span className="text-gray-500">({data.count}건)</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}