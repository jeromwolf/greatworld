from neo4j import GraphDatabase
import json

class HealthKnowledgeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def create_disease(self, disease_data):
        with self.driver.session() as session:
            result = session.run("""
                CREATE (d:Disease {
                    id: $id,
                    name_ko: $name_ko,
                    name_en: $name_en,
                    icd10_code: $icd10_code,
                    category: $category,
                    severity_level: $severity_level
                })
                RETURN d
            """, **disease_data)
            return result.single()[0]
    
    def create_symptom(self, symptom_data):
        with self.driver.session() as session:
            result = session.run("""
                CREATE (s:Symptom {
                    id: $id,
                    name_common: $name_common,
                    name_medical: $name_medical,
                    body_part: $body_part,
                    duration: $duration
                })
                RETURN s
            """, **symptom_data)
            return result.single()[0]
    
    def link_disease_symptom(self, disease_id, symptom_id, frequency, severity):
        with self.driver.session() as session:
            session.run("""
                MATCH (d:Disease {id: $disease_id})
                MATCH (s:Symptom {id: $symptom_id})
                CREATE (d)-[:HAS_SYMPTOM {
                    frequency: $frequency,
                    severity: $severity
                }]->(s)
            """, disease_id=disease_id, symptom_id=symptom_id, 
                frequency=frequency, severity=severity)
    
    def find_disease_by_symptoms(self, symptom_ids):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Disease)-[r:HAS_SYMPTOM]->(s:Symptom)
                WHERE s.id IN $symptom_ids
                WITH d, COUNT(DISTINCT s) as symptom_count, 
                     AVG(r.severity) as avg_severity
                WHERE symptom_count >= 2
                RETURN d.name_ko as disease, 
                       symptom_count, 
                       avg_severity
                ORDER BY symptom_count DESC, avg_severity DESC
                LIMIT 5
            """, symptom_ids=symptom_ids)
            return [record.data() for record in result]
    
    def check_drug_interaction(self, drug_ids):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m1:Medication)-[r:INTERACTS_WITH]->(m2:Medication)
                WHERE m1.id IN $drug_ids AND m2.id IN $drug_ids
                AND m1.id < m2.id
                RETURN m1.name as drug1, 
                       m2.name as drug2, 
                       r.severity as severity,
                       r.description as description
                ORDER BY 
                    CASE r.severity 
                        WHEN 'major' THEN 1 
                        WHEN 'moderate' THEN 2 
                        ELSE 3 
                    END
            """, drug_ids=drug_ids)
            return [record.data() for record in result]


# 초기 데이터 설정 예시
def setup_initial_data():
    kg = HealthKnowledgeGraph("bolt://localhost:7687", "neo4j", "password")
    
    # 질병 생성
    diabetes = {
        "id": "D001",
        "name_ko": "당뇨병",
        "name_en": "Diabetes Mellitus",
        "icd10_code": "E11",
        "category": "만성질환",
        "severity_level": 4
    }
    kg.create_disease(diabetes)
    
    hypertension = {
        "id": "D002",
        "name_ko": "고혈압",
        "name_en": "Hypertension",
        "icd10_code": "I10",
        "category": "만성질환",
        "severity_level": 3
    }
    kg.create_disease(hypertension)
    
    # 증상 생성
    frequent_urination = {
        "id": "S001",
        "name_common": "잦은 소변",
        "name_medical": "다뇨",
        "body_part": "비뇨기계",
        "duration": "지속적"
    }
    kg.create_symptom(frequent_urination)
    
    thirst = {
        "id": "S002",
        "name_common": "심한 갈증",
        "name_medical": "다갈",
        "body_part": "전신",
        "duration": "지속적"
    }
    kg.create_symptom(thirst)
    
    headache = {
        "id": "S003",
        "name_common": "두통",
        "name_medical": "두통",
        "body_part": "머리",
        "duration": "간헐적"
    }
    kg.create_symptom(headache)
    
    # 관계 생성
    kg.link_disease_symptom("D001", "S001", "common", 4)
    kg.link_disease_symptom("D001", "S002", "common", 4)
    kg.link_disease_symptom("D002", "S003", "common", 3)
    
    kg.close()


# 사용 예시
if __name__ == "__main__":
    kg = HealthKnowledgeGraph("bolt://localhost:7687", "neo4j", "password")
    
    # 증상으로 질병 찾기
    symptoms = ["S001", "S002"]  # 잦은 소변, 심한 갈증
    possible_diseases = kg.find_disease_by_symptoms(symptoms)
    print("가능한 질병:")
    for disease in possible_diseases:
        print(f"- {disease['disease']} (일치 증상: {disease['symptom_count']}개)")
    
    # 약물 상호작용 체크
    medications = ["M001", "M002", "M003"]
    interactions = kg.check_drug_interaction(medications)
    if interactions:
        print("\n⚠️  약물 상호작용 경고:")
        for interaction in interactions:
            print(f"- {interaction['drug1']} ↔ {interaction['drug2']}")
            print(f"  위험도: {interaction['severity']}")
            print(f"  설명: {interaction['description']}")
    
    kg.close()