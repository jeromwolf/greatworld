export interface Message {
  id: string
  type: 'user' | 'bot' | 'system'
  content: string
  timestamp: Date
  data?: AnalysisData
  nluResult?: NLUResult
}

export interface NLUResult {
  intent: string
  confidence: number
  entities?: Record<string, any>
}

export interface AnalysisData {
  sentiment?: number
  sources?: Record<string, SentimentSource>
  keyFactors?: string[]
  recommendation?: string
}

export interface SentimentSource {
  sentiment: number
  confidence: number
  count?: number
  engagement?: number
}

export interface WebSocketMessage {
  type: string
  message: string
  data?: AnalysisData
  nlu_result?: NLUResult
  timestamp: string
}

export interface StockInfo {
  ticker: string
  companyName: string
  isKorean: boolean
}