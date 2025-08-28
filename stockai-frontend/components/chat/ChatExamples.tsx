interface ChatExamplesProps {
  onExampleClick: (example: string) => void
}

const examples = [
  "삼성전자 최근 실적 어때?",
  "AAPL 주가 전망 알려줘",
  "테슬라와 리비안 비교해줘",
  "코스피 시장 분위기는?"
]

export function ChatExamples({ onExampleClick }: ChatExamplesProps) {
  return (
    <div className="p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-600">예시 질문</h3>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {examples.map((example, index) => (
          <button
            key={index}
            onClick={() => onExampleClick(example)}
            className="rounded-lg border border-gray-200 p-3 text-left text-sm text-gray-700 transition-colors hover:border-blue-300 hover:bg-blue-50"
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  )
}