// 전문적인 투자 리포트 UI JavaScript

let ws = null;
let clientId = Math.random().toString(36).substr(2, 9);

// WebSocket 연결
function connectWebSocket() {
    ws = new WebSocket(`ws://localhost:8200/ws/client_${clientId}`);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        console.log('Received message:', event.data);
        const data = JSON.parse(event.data);
        
        if (data.type === 'system') {
            console.log('System message:', data.message);
        } else if (data.type === 'bot' && data.data) {
            displayResults(data);
            document.getElementById('loading').classList.add('hidden');
            document.getElementById('results').classList.remove('hidden');
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        document.getElementById('loading').classList.add('hidden');
        alert('서버 연결에 실패했습니다. 다시 시도해주세요.');
    };
    
    ws.onclose = () => {
        console.log('WebSocket closed');
        // 5초 후 재연결 시도
        setTimeout(connectWebSocket, 5000);
    };
}

// 주식 분석 시작
function analyzeStock() {
    const stockInput = document.getElementById('stockInput');
    const query = stockInput.value.trim();
    
    if (!query) {
        alert('종목명을 입력해주세요.');
        return;
    }
    
    // UI 초기화 - 이전 데이터 완전히 삭제
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    
    // 이전 결과 초기화
    clearPreviousResults();
    
    // WebSocket으로 메시지 전송
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = {
            message: query + ' 주가 분석해줘'
        };
        console.log('Sending message:', message);
        ws.send(JSON.stringify(message));
    } else {
        console.log('WebSocket not ready. State:', ws ? ws.readyState : 'null');
        alert('서버에 연결 중입니다. 잠시 후 다시 시도해주세요.');
        document.getElementById('loading').classList.add('hidden');
    }
}

// 이전 결과 초기화
function clearPreviousResults() {
    document.getElementById('companyName').textContent = '-';
    document.getElementById('analysisDate').textContent = '-';
    document.getElementById('dataReliability').textContent = '-';
    document.getElementById('sentimentEmoji').textContent = '-';
    document.getElementById('sentimentScore').textContent = '0.00';
    document.getElementById('sentimentLabel').textContent = '-';
    document.getElementById('confidenceStars').textContent = '-';
    document.getElementById('confidencePercent').textContent = '0%';
    document.getElementById('keyFactors').innerHTML = '';
    document.getElementById('sentimentCharts').innerHTML = '';
    document.getElementById('newsList').innerHTML = '';
    document.getElementById('financialData').innerHTML = '';
    document.getElementById('disclosureList').innerHTML = '';
    document.getElementById('aiRecommendation').innerHTML = '';
}

// 결과 표시
function displayResults(data) {
    // 데이터에서 정보 추출
    const sentiment = data.data.sentiment || 0;
    const sources = data.data.sources || {};
    const reliability = data.data.reliability || 'unknown';
    
    // 메시지 파싱 (간단한 정규식으로 주요 정보 추출)
    const message = data.message || '';
    
    // 회사명 추출
    const companyMatch = message.match(/([가-힣]+|[A-Z]+(?:\s+[A-Z]+)*)\s+투자\s+분석\s+리포트/);
    const companyName = companyMatch ? companyMatch[1] : '분석 결과';
    document.getElementById('companyName').textContent = companyName;
    
    // 날짜 설정
    document.getElementById('analysisDate').textContent = new Date().toLocaleString('ko-KR');
    
    // 신뢰도 표시
    const reliabilityElement = document.getElementById('dataReliability');
    reliabilityElement.textContent = {
        'high': '✓ 실제 데이터',
        'mixed': '⚠️ 혼합 데이터',
        'low': '⚠️ 모의 데이터',
        'unknown': '데이터 확인 중'
    }[reliability];
    reliabilityElement.className = 'data-source ' + reliability;
    
    // 감성 점수 표시
    displaySentiment(sentiment, sources);
    
    // 메시지 내용 파싱해서 각 섹션에 표시
    parseAndDisplayContent(message, sources);
}

// 감성 점수 표시
function displaySentiment(overall, sources) {
    // 전체 감성
    const emoji = overall > 0.1 ? '📈' : overall < -0.1 ? '📉' : '➖';
    const label = overall > 0.1 ? '긍정적' : overall < -0.1 ? '부정적' : '중립적';
    
    document.getElementById('sentimentEmoji').textContent = emoji;
    document.getElementById('sentimentScore').textContent = overall.toFixed(2);
    document.getElementById('sentimentLabel').textContent = label;
    
    // 신뢰도 (sources 개수 기반 추정)
    const confidence = Math.min(1.0, Object.keys(sources).length * 0.33);
    const stars = '⭐'.repeat(Math.max(1, Math.floor(confidence * 5)));
    document.getElementById('confidenceStars').textContent = stars;
    document.getElementById('confidencePercent').textContent = Math.floor(confidence * 100) + '%';
    
    // 데이터 소스별 차트
    displaySentimentCharts(sources);
}

// 감성 차트 표시
function displaySentimentCharts(sources) {
    const container = document.getElementById('sentimentCharts');
    container.innerHTML = '';
    
    Object.entries(sources).forEach(([source, data]) => {
        const sentiment = data.sentiment || 0;
        const count = data.count || 0;
        
        const chartItem = document.createElement('div');
        chartItem.className = 'sentiment-chart-item';
        
        const sentimentClass = sentiment > 0 ? 'positive' : sentiment < 0 ? 'negative' : 'neutral';
        const percentage = Math.abs(sentiment) * 100;
        
        chartItem.innerHTML = `
            <div class="sentiment-header">
                <h4>${source.toUpperCase()} (${count}건)</h4>
                <span class="sentiment-value ${sentimentClass}">${sentiment > 0 ? '+' : ''}${sentiment.toFixed(2)}</span>
            </div>
            <div class="sentiment-bar">
                <div class="sentiment-bar-fill ${sentimentClass}" style="width: ${percentage}%"></div>
            </div>
        `;
        
        container.appendChild(chartItem);
    });
}

// 메시지 내용 파싱 및 표시
function parseAndDisplayContent(message, sources) {
    console.log('Parsing message:', message);
    
    // 핵심 인사이트 추출
    const insightsMatch = message.match(/핵심 인사이트\s*\n([\s\S]*?)(?=\n-{3,}|\n={3,}|$)/);
    if (insightsMatch) {
        const insights = insightsMatch[1].split('\n')
            .filter(line => line.trim().startsWith('•') || line.trim().startsWith('-'))
            .map(line => line.replace(/^[•\-]\s*/, '').trim())
            .filter(line => line.length > 0);
        
        const factorsList = document.getElementById('keyFactors');
        factorsList.innerHTML = insights.map(insight => `<li>${insight}</li>`).join('');
    }
    
    // 뉴스 추출 - 새로운 카테고리 포맷 처리
    const newsMatch = message.match(/최근 뉴스 분석.*?\n-{3,}\n([\s\S]*?)(?=\n-{3,}|$)/);
    
    if (newsMatch) {
        const newsSection = newsMatch[1];
        const newsList = document.getElementById('newsList');
        let newsHTML = '';
        
        // 카테고리별로 처리
        const criticalMatch = newsSection.match(/🚨 \*\*즉시 확인 필요\*\*\n([\s\S]*?)(?=\n\n|$)/);
        const importantMatch = newsSection.match(/💡 \*\*주요 뉴스\*\*\n([\s\S]*?)(?=\n\n|$)/);
        const generalMatch = newsSection.match(/📌 \*\*일반 뉴스\*\*\n([\s\S]*?)(?=\n\n|$)/);
        
        if (criticalMatch) {
            newsHTML += '<div class="news-category critical"><h5>🚨 즉시 확인 필요</h5><ul>';
            const criticalNews = criticalMatch[1].split('\n').filter(line => line.includes('▸'));
            criticalNews.forEach(news => {
                const title = news.replace(/^\s*▸\s*/, '').trim();
                const keyInfo = news.match(/\[(.*?)\]/);
                newsHTML += `<li>${title}${keyInfo ? ` <span class="key-info">${keyInfo[1]}</span>` : ''}</li>`;
            });
            newsHTML += '</ul></div>';
        }
        
        if (importantMatch) {
            newsHTML += '<div class="news-category important"><h5>💡 주요 뉴스</h5><ul>';
            const importantNews = importantMatch[1].split('\n').filter(line => line.includes('▸'));
            importantNews.forEach(news => {
                const title = news.replace(/^\s*▸\s*/, '').trim();
                const keyInfo = news.match(/\[(.*?)\]/);
                newsHTML += `<li>${title}${keyInfo ? ` <span class="key-info">${keyInfo[1]}</span>` : ''}</li>`;
            });
            newsHTML += '</ul></div>';
        }
        
        if (generalMatch) {
            newsHTML += '<div class="news-category general"><h5>📌 일반 뉴스</h5><ul>';
            const generalNews = generalMatch[1].split('\n').filter(line => line.includes('▸'));
            generalNews.forEach(news => {
                const title = news.replace(/^\s*▸\s*/, '').trim();
                newsHTML += `<li>${title}</li>`;
            });
            newsHTML += '</ul></div>';
        }
        
        // 구형 포맷 대비
        if (!newsHTML) {
            const newsItems = newsSection.split('\n')
                .filter(line => line.match(/^\d+\./))
                .map(line => line.replace(/^\d+\.\s*/, '').trim())
                .filter(line => line.length > 0);
            
            if (newsItems.length > 0) {
                newsHTML = newsItems.slice(0, 10).map(news => `<li>${news}</li>`).join('');
            }
        }
        
        newsList.innerHTML = newsHTML || '<li>뉴스 데이터가 없습니다.</li>';
    }
    
    // 공시 및 재무 데이터 추출 - 더 유연한 패턴
    const disclosureMatch = message.match(/주요 공시.*?\n-{3,}\n([\s\S]*?)(?=\n-{3,}|\n={3,}|$)/);
    if (!disclosureMatch) {
        // 백업 패턴 시도
        const backupMatch = message.match(/핵심 공시.*?\n([\s\S]*?)(?=\n## |$)/);
        if (backupMatch) {
            parseDisclosureContent(backupMatch[1]);
        }
    } else {
        parseDisclosureContent(disclosureMatch[1]);
    }
    
    function parseDisclosureContent(content) {
        // 재무 데이터 추출
        const financialLines = content.split('\n')
            .filter(line => {
                const lower = line.toLowerCase();
                return (line.includes('매출액') || line.includes('영업이익') || line.includes('당기순이익') ||
                        lower.includes('revenue') || lower.includes('profit')) && 
                       line.trim().length > 0;
            });
        
        if (financialLines.length > 0) {
            const financialData = document.getElementById('financialData');
            financialData.innerHTML = '<h4 style="margin-bottom: 10px; color: #3B82F6;">💼 실제 재무 데이터</h4>' + 
                                     financialLines.map(line => {
                                         const cleanLine = line.replace(/^[▫•\-]\s*/, '').trim();
                                         return `<p>${cleanLine}</p>`;
                                     }).join('');
        }
        
        // 공시 목록 추출
        const disclosureLines = content.split('\n')
            .filter(line => {
                return (line.includes('보고서') || line.includes('공시') || 
                       line.match(/^\d{8}/) || // 날짜로 시작
                       line.startsWith('▫') || line.startsWith('-')) &&
                       !line.includes('매출액') && !line.includes('영업이익') && 
                       !line.includes('당기순이익') && line.trim().length > 5;
            })
            .map(line => line.replace(/^[▫•\-]\s*/, '').trim());
        
        if (disclosureLines.length > 0) {
            const disclosureList = document.getElementById('disclosureList');
            disclosureList.innerHTML = disclosureLines.slice(0, 5).map(disclosure => `<li>${disclosure}</li>`).join('');
        }
    }
    
    // AI 의견 추출
    const aiMatch = message.match(/AI 투자 의견\s*\n-{3,}\n([\s\S]*?)(?=\n={3,}|$)/);
    if (aiMatch) {
        const aiText = aiMatch[1].trim();
        const aiElement = document.getElementById('aiRecommendation');
        
        // \n을 실제 줄바꿈으로 변환
        aiElement.innerHTML = aiText
            .replace(/\\n/g, '<br>')
            .replace(/\n/g, '<br>')
            .replace(/•/g, '▫️');
    }
}

// Enter 키로 검색
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
    
    const stockInput = document.getElementById('stockInput');
    stockInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            analyzeStock();
        }
    });
    
    // 포커스
    stockInput.focus();
});