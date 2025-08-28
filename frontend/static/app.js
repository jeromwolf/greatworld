/**
 * StockAI 채팅 애플리케이션
 * WebSocket을 통한 실시간 통신
 */

class StockAIChat {
    constructor() {
        this.ws = null;
        this.clientId = this.generateClientId();
        this.messageContainer = document.getElementById('chatMessages');
        this.inputField = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendButton');
        
        this.init();
    }
    
    generateClientId() {
        return 'client_' + Math.random().toString(36).substr(2, 9);
    }
    
    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.setupExampleClicks();
    }
    
    connectWebSocket() {
        const wsUrl = `ws://localhost:8200/ws/${this.clientId}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket 연결 성공');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket 연결 종료');
            this.addSystemMessage('서버와의 연결이 끊어졌습니다. 페이지를 새로고침해주세요.');
            
            // 재연결 시도
            setTimeout(() => {
                this.connectWebSocket();
            }, 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket 오류:', error);
            this.addSystemMessage('연결 오류가 발생했습니다.');
        };
    }
    
    setupEventListeners() {
        // 전송 버튼 클릭
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // 엔터 키 처리
        this.inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }
    
    setupExampleClicks() {
        const examples = document.querySelectorAll('.examples li');
        examples.forEach(example => {
            example.addEventListener('click', () => {
                this.inputField.value = example.textContent.replace(/^"|"$/g, '');
                this.inputField.focus();
            });
        });
    }
    
    sendMessage() {
        const message = this.inputField.value.trim();
        
        if (!message) return;
        
        if (this.ws.readyState !== WebSocket.OPEN) {
            this.addSystemMessage('서버와 연결되지 않았습니다. 잠시 후 다시 시도해주세요.');
            return;
        }
        
        // 사용자 메시지 표시
        this.addUserMessage(message);
        
        // 서버로 메시지 전송
        this.ws.send(JSON.stringify({
            message: message,
            timestamp: new Date().toISOString()
        }));
        
        // 입력 필드 초기화
        this.inputField.value = '';
        
        // 타이핑 인디케이터 표시
        this.showTypingIndicator();
    }
    
    handleMessage(data) {
        // 타이핑 인디케이터 제거
        this.hideTypingIndicator();
        
        switch (data.type) {
            case 'system':
                this.addSystemMessage(data.message);
                break;
            case 'bot':
                this.addBotMessage(data.message, data.data || data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    addUserMessage(message) {
        const messageDiv = this.createMessageElement(message, 'user');
        this.messageContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addBotMessage(message, data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot';
        
        // 마크다운 형식 지원
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = this.parseMarkdown(message);
        messageDiv.appendChild(contentDiv);
        
        // 감성 점수가 있으면 시각화
        if (data && data.sentiment !== undefined) {
            const sentimentDiv = document.createElement('div');
            sentimentDiv.className = 'sentiment-indicator';
            const sentimentScore = data.sentiment;
            const sentimentColor = this.getSentimentColor(sentimentScore);
            
            sentimentDiv.innerHTML = `
                <div class="sentiment-bar">
                    <div class="sentiment-fill" style="background: ${sentimentColor}; width: ${(sentimentScore + 1) * 50}%"></div>
                </div>
                <span class="sentiment-label">${this.getSentimentLabel(sentimentScore)}</span>
            `;
            messageDiv.appendChild(sentimentDiv);
        }
        
        // NLU 결과가 있으면 디버그 모드에서만 표시
        if (data && data.nlu_result && window.DEBUG_MODE) {
            const nluDiv = document.createElement('div');
            nluDiv.className = 'nlu-result';
            nluDiv.innerHTML = `
                <details>
                    <summary>분석 상세</summary>
                    <pre>${JSON.stringify(data.nlu_result, null, 2)}</pre>
                </details>
            `;
            messageDiv.appendChild(nluDiv);
        }
        
        // 시간 추가
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        messageDiv.appendChild(timeDiv);
        
        this.messageContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    parseMarkdown(text) {
        // 간단한 마크다운 파싱
        return text
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/• /g, '&bull; ')
            .replace(/📊/g, '<span class="emoji">📊</span>')
            .replace(/🔍/g, '<span class="emoji">🔍</span>');
    }
    
    getSentimentColor(score) {
        if (score >= 0.6) return '#4CAF50';  // 강한 긍정 - 녹색
        if (score >= 0.2) return '#8BC34A';  // 긍정 - 연녹색
        if (score >= -0.2) return '#FFC107'; // 중립 - 노란색
        if (score >= -0.6) return '#FF9800'; // 부정 - 주황색
        return '#F44336';  // 강한 부정 - 빨간색
    }
    
    getSentimentLabel(score) {
        if (score >= 0.6) return '매우 긍정적';
        if (score >= 0.2) return '긍정적';
        if (score >= -0.2) return '중립적';
        if (score >= -0.6) return '부정적';
        return '매우 부정적';
    }
    
    addSystemMessage(message) {
        const messageDiv = this.createMessageElement(message, 'system');
        this.messageContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    createMessageElement(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        
        // 시간 표시 추가
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        messageDiv.appendChild(timeDiv);
        
        return messageDiv;
    }
    
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        this.messageContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    scrollToBottom() {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }
}

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    new StockAIChat();
});