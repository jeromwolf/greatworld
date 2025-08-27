import re
from typing import List, Dict
from knowledge_graph_example import HealthKnowledgeGraph

class SeniorHealthChatbot:
    def __init__(self, kg: HealthKnowledgeGraph):
        self.kg = kg
        self.symptom_keywords = {
            "소변": ["S001", "잦은 소변"],
            "갈증": ["S002", "심한 갈증"],
            "두통": ["S003", "두통"],
            "어지럼": ["S004", "어지러움"],
            "가슴": ["S005", "가슴 통증"],
            "숨": ["S006", "호흡곤란"],
            "관절": ["S007", "관절통"],
            "피로": ["S008", "피로감"]
        }
        self.current_symptoms = []
    
    def understand_symptom(self, user_input: str) -> List[str]:
        """사용자의 자연어 입력에서 증상을 추출"""
        found_symptoms = []
        
        # 간단한 키워드 매칭 (실제로는 NLP 모델 사용)
        for keyword, symptom_info in self.symptom_keywords.items():
            if keyword in user_input:
                found_symptoms.append({
                    "id": symptom_info[0],
                    "name": symptom_info[1]
                })
        
        return found_symptoms
    
    def generate_response(self, user_input: str) -> str:
        """사용자 입력에 대한 응답 생성"""
        
        # 증상 언급 확인
        symptoms = self.understand_symptom(user_input)
        
        if symptoms:
            self.current_symptoms.extend([s["id"] for s in symptoms])
            symptom_names = [s["name"] for s in symptoms]
            
            response = f"아, {', '.join(symptom_names)} 증상이 있으시군요.\n"
            
            # 충분한 증상이 모이면 질병 추론
            if len(self.current_symptoms) >= 2:
                possible_diseases = self.kg.find_disease_by_symptoms(
                    list(set(self.current_symptoms))
                )
                
                if possible_diseases:
                    response += "\n제가 확인해본 결과:\n"
                    for disease in possible_diseases[:3]:
                        response += f"• {disease['disease']} 가능성이 있습니다.\n"
                    
                    response += "\n💊 권장사항:\n"
                    response += "• 가까운 병원을 방문하여 정확한 진단을 받으세요\n"
                    response += "• 혈당/혈압을 정기적으로 체크하세요\n"
                    response += "• 충분한 수분을 섭취하세요\n"
                else:
                    response += "다른 증상이 더 있으신가요?"
            else:
                response += "다른 증상도 있으신지 알려주세요."
        
        # 약물 관련 질문
        elif "약" in user_input or "복용" in user_input:
            response = self.handle_medication_query(user_input)
        
        # 일반 건강 조언
        elif "운동" in user_input:
            response = "시니어분들께 좋은 운동:\n"
            response += "• 걷기: 하루 30분, 천천히\n"
            response += "• 스트레칭: 아침에 10분\n"
            response += "• 수중운동: 관절에 무리가 적어요"
        
        else:
            response = "무엇을 도와드릴까요? 증상이나 복용 중인 약물을 알려주세요."
        
        return response
    
    def handle_medication_query(self, user_input: str) -> str:
        """약물 관련 질문 처리"""
        # 실제로는 약물명을 추출하는 로직 필요
        response = "복용 중인 약물을 모두 알려주시면 상호작용을 확인해드릴게요.\n"
        response += "예: 혈압약, 당뇨약, 진통제 등"
        return response


# 간단한 대화형 인터페이스
def run_chatbot():
    # 실제로는 Neo4j 연결
    # kg = HealthKnowledgeGraph("bolt://localhost:7687", "neo4j", "password")
    # chatbot = SeniorHealthChatbot(kg)
    
    print("🏥 시니어 건강 도우미")
    print("=" * 40)
    print("안녕하세요! 건강에 대해 궁금한 점을 편하게 물어보세요.")
    print("예: '요즘 자주 화장실에 가요', '두통이 있어요'")
    print("종료하려면 '끝'을 입력하세요.\n")
    
    while True:
        user_input = input("👤 어르신: ")
        
        if user_input.lower() in ['끝', '종료', 'quit']:
            print("🏥 도우미: 건강하세요! 필요하시면 언제든 불러주세요.")
            break
        
        # 여기서 실제 챗봇 응답 생성
        # response = chatbot.generate_response(user_input)
        
        # 데모를 위한 간단한 응답
        if "소변" in user_input or "화장실" in user_input:
            response = """아, 잦은 소변 증상이 있으시군요.
다른 증상도 있으신지 알려주세요.
예를 들어 갈증, 피로감, 체중 변화 등이 있나요?"""
        elif "갈증" in user_input or "목" in user_input:
            response = """심한 갈증도 있으시군요.
잦은 소변과 함께 나타나면 당뇨병 가능성이 있습니다.

💊 권장사항:
• 가까운 내과를 방문하여 혈당 검사를 받으세요
• 단 음료 대신 물을 자주 드세요
• 가족력이 있다면 꼭 의사에게 말씀하세요"""
        else:
            response = "증상을 좀 더 자세히 말씀해주세요."
        
        print(f"🏥 도우미: {response}\n")


if __name__ == "__main__":
    run_chatbot()