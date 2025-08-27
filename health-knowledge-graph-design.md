# 시니어 건강관리 앱 - 건강 지식 그래프 설계

## 1. 핵심 엔티티 (Entities)

### 질병 (Disease)
```
- ID: 고유 식별자
- 이름: 한글명, 영문명
- ICD-10 코드
- 카테고리: 만성질환, 급성질환 등
- 심각도: 1-5 레벨
```

### 증상 (Symptom)
```
- ID: 고유 식별자
- 이름: 일반인 용어, 의학 용어
- 부위: 신체 부위
- 특성: 지속성, 강도
```

### 약물 (Medication)
```
- ID: 고유 식별자
- 성분명
- 제품명
- 용법/용량
- 부작용
```

### 검사 (Test)
```
- ID: 고유 식별자
- 검사명
- 정상 범위
- 주기
```

### 생활습관 (Lifestyle)
```
- ID: 고유 식별자
- 운동
- 식단
- 수면
```

## 2. 관계 정의 (Relationships)

### 질병-증상 관계
```cypher
(Disease)-[:HAS_SYMPTOM {frequency: "common|rare", severity: 1-5}]->(Symptom)
```

### 질병-약물 관계
```cypher
(Disease)-[:TREATED_BY]->(Medication)
(Medication)-[:CONTRAINDICATED_FOR]->(Disease)
```

### 약물 상호작용
```cypher
(Medication)-[:INTERACTS_WITH {severity: "major|moderate|minor"}]->(Medication)
```

### 질병-검사 관계
```cypher
(Disease)-[:REQUIRES_TEST {frequency: "monthly|quarterly|yearly"}]->(Test)
```

### 질병-생활습관 관계
```cypher
(Disease)-[:PREVENTED_BY]->(Lifestyle)
(Disease)-[:MANAGED_BY]->(Lifestyle)
```

## 3. 시니어 특화 온톨로지

### 연령별 리스크 모델
```
Age_Group (65-74, 75-84, 85+)
  └── Risk_Factor
      ├── Disease_Prevalence
      ├── Medication_Sensitivity
      └── Complication_Risk
```

### 복합 질환 패턴
```
Multi-Morbidity_Pattern
  ├── Primary_Disease
  ├── Secondary_Diseases[]
  ├── Drug_Interactions[]
  └── Management_Priority
```

## 4. 추론 규칙 예시

### 규칙 1: 증상 기반 질병 추론
```
IF 
  User HAS_SYMPTOM "잦은 소변" AND
  User HAS_SYMPTOM "갈증" AND
  User HAS_SYMPTOM "체중감소"
THEN
  SUGGEST Disease "당뇨병" WITH confidence 0.8
```

### 규칙 2: 약물 충돌 검사
```
IF
  User TAKES Medication_A AND
  User PRESCRIBED Medication_B AND
  Medication_A INTERACTS_WITH Medication_B WITH severity "major"
THEN
  ALERT "약물 상호작용 위험"
```

### 규칙 3: 검사 주기 알림
```
IF
  User HAS_DISEASE "당뇨병" AND
  Last_HbA1c_Test WAS_MORE_THAN "3 months ago"
THEN
  REMIND "당화혈색소 검사 시기"
```

## 5. 구현 기술 스택

### 그래프 데이터베이스
- **Neo4j**: 메인 그래프 DB
- **GraphQL**: API 레이어

### 온톨로지 관리
- **Protégé**: 온톨로지 편집
- **Apache Jena**: RDF 처리
- **OWLAPI**: 온톨로지 추론

### 자연어 처리
- **KoBERT**: 한국어 증상 이해
- **Med-BERT**: 의료 용어 매핑

## 6. MVP 구현 우선순위

1. **Phase 1 (1-2개월)**
   - 5대 만성질환 (당뇨, 고혈압, 관절염, 치매, 심장질환)
   - 주요 증상 50개
   - 상용 약물 100개

2. **Phase 2 (3-4개월)**
   - 약물 상호작용 체크
   - 증상 기반 질병 추론
   - 검사 주기 관리

3. **Phase 3 (5-6개월)**
   - 생활습관 연계
   - 복합질환 관리
   - AI 건강 상담

## 7. 데이터 수집 계획

- 건강보험공단 공공 데이터
- 의약품안전나라 API
- 대한의학회 가이드라인
- 시니어 사용자 피드백