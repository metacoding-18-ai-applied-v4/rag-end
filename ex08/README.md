# ex08 — 검색 품질 튜닝 실험

> **Chapter 08 "엉뚱한 문서를 가져온다"** 의 실습 코드입니다.
>
> RAG 파이프라인에서 **검색 품질**을 높이는 세 가지 축을 실험합니다.
> 모든 실험은 터미널에서 바로 실행할 수 있고, 파라미터를 바꿔가며 결과를 비교해 볼 수 있습니다.

## 사전 준비

```bash
cd projects/사내AI비서_v2/code/ex08
pip install -r requirements.txt    # rich, langchain, sentence-transformers 등
```

---

## 실험 목록 한눈에 보기

| 실험 | 주제 | 핵심 질문 |
|------|------|----------|
| **1-1** | 청크 크기 비교 | 300자 vs 500자 vs 1000자, 어떤 크기가 좋을까? |
| **1-2** | 오버랩 비율 비교 | 10% vs 20% vs 30%, 얼마나 겹쳐야 문맥이 살까? |
| **1-3** | 청킹 전략 비교 (긴 문서) | Fixed vs Recursive vs Semantic, 긴 규정 문서에서 누가 이길까? |
| **1-4** | 청킹 전략 비교 (짧은 문서) | 짧은 문서에서도 Semantic이 최선일까? |
| **1-5** | Retriever 파라미터 튜닝 | k값, threshold, metadata 필터를 바꾸면 검색 결과가 어떻게 달라질까? |
| **2-1** | Reranker 전후 비교 | Cross-Encoder가 순위를 얼마나 바꿀까? |
| **2-2** | initial_k × top_k 조합 | 넓게 검색 → 좁게 정제 vs 좁게 검색 → 좁게 정제? |
| **3-1** | 하이브리드 검색 alpha 비교 | BM25와 Vector의 가중치 비율을 바꾸면? |
| **3-2** | 하이브리드 검색 데모 | 실제 질문으로 하이브리드 검색 결과를 확인 |

---

## Step 1: 청킹 전략 실험

### 실험 1-1: 청크 크기 비교

```bash
python -m tuning.step1_chunk_experiment --step 1-1
```

300자, 500자, 1000자로 잘랐을 때 청크 수·평균 크기·최소/최대를 비교합니다.
**결론: 500자가 정밀도와 문맥의 균형점.**

### 실험 1-2: 오버랩 비율 비교

```bash
python -m tuning.step1_chunk_experiment --step 1-2
```

오버랩 10%, 20%, 30%가 청크 크기에 미치는 영향을 확인합니다.
**결론: 20% 오버랩(100자)이 실용적 기본값.**

### 실험 1-3: 청킹 전략 비교 — 긴 문서

```bash
# 기본 (percentile=70)
python -m tuning.step1_chunk_experiment --step 1-3

# percentile을 바꿔서 비교
python -m tuning.step1_chunk_experiment --step 1-3 --percentile 50
python -m tuning.step1_chunk_experiment --step 1-3 --percentile 95
```

10개 규정이 담긴 긴 문서(4,500자)에서 Fixed-size, Recursive, Semantic 전략을 비교합니다.
벡터 검색까지 수행하여 "재택근무 외출 절차" 질문에 각 전략이 정답을 찾는지 확인합니다.

- `--percentile 50`: 더 예민하게 자름 → 청크가 작고 많아짐
- `--percentile 95`: 둔감하게 자름 → 청크가 크고 적어짐

**결론: 긴 문서 + 적절한 임계값 = Semantic 청킹이 최고 유사도.**

### 실험 1-4: 청킹 전략 비교 — 짧은 문서

```bash
python -m tuning.step1_chunk_experiment --step 1-4
```

1,100자 정도의 짧은 문서에서 세 가지 전략을 비교합니다.
Semantic 청킹이 만능은 아닙니다 — 짧은 문서에서는 오히려 불리할 수 있습니다.

**결론: 짧은 문서에서는 Recursive가 최선.** 문단·문장 경계를 자연스럽게 존중하면서도 실행 속도가 빠릅니다.

### 실험 1-5: Retriever 파라미터 튜닝

```bash
# 전체 비교 실험 (1-5a: k값, 1-5b: threshold, 1-5c: metadata)
python -m tuning.step1_chunk_experiment --step 1-5

# k값만 바꿔서 직접 실험
python -m tuning.step1_chunk_experiment --step 1-5 --k 3
python -m tuning.step1_chunk_experiment --step 1-5 --k 10

# threshold만 바꿔서 실험
python -m tuning.step1_chunk_experiment --step 1-5 --threshold 0.3

# 부서별 metadata 필터 적용
python -m tuning.step1_chunk_experiment --step 1-5 --department HR
python -m tuning.step1_chunk_experiment --step 1-5 --department FINANCE

# 조합
python -m tuning.step1_chunk_experiment --step 1-5 --k 3 --threshold 0.3 --department HR
```

세 가지 파라미터를 실험합니다:

| 파라미터 | 의미 | 예시 |
|---------|------|------|
| `--k` | 검색 결과 반환 수 | 3, 5, 10 |
| `--threshold` | 유사도 임계값 (이하 제거) | 0.0, 0.2, 0.5 |
| `--department` | 메타데이터 부서 필터 | HR, FINANCE, IT |

**결론: k=5, threshold=0.2, 부서별 metadata 필터를 조합하면 노이즈를 효과적으로 줄일 수 있습니다.**

---

## Step 2: Reranker 실험

### 실험 2-1: 리랭킹 전후 비교

```bash
# 기본 (initial_k=10, top_k=5, 기본 쿼리)
python -m tuning.step2_reranker --step 2-1

# 직접 질문 입력
python -m tuning.step2_reranker --step 2-1 --query "성과 평가 기준이 뭔가요"
python -m tuning.step2_reranker --step 2-1 --query "USB 반입 규정"
python -m tuning.step2_reranker --step 2-1 --query "육아휴직 신청 방법"

# 검색 범위 조절
python -m tuning.step2_reranker --step 2-1 --initial_k 20 --top_k 3
python -m tuning.step2_reranker --step 2-1 --query "출장비 정산" --initial_k 5 --top_k 3
```

Vector Search 순위(유사도 기반)와 Cross-Encoder 순위(정밀 매칭)를 나란히 비교합니다.
`--query`로 아무 질문이나 넣어서 리랭킹이 순위를 어떻게 뒤집는지 직접 확인해보세요.

| 파라미터 | 의미 | 기본값 |
|---------|------|--------|
| `--query` | 직접 질문 입력 | "연차 신청 절차는 어떻게 됩니까" |
| `--initial_k` | 초기 검색 결과 수 (넓게) | 10 |
| `--top_k` | 리랭킹 후 최종 결과 수 (좁게) | 5 |

### 실험 2-2: initial_k × top_k 조합 비교

```bash
python -m tuning.step2_reranker --step 2-2
```

4가지 조합 `(5,3)`, `(10,5)`, `(20,5)`, `(20,10)`을 한 번에 비교합니다.
**결론: initial_k=10~20, top_k=5가 비용 대비 효과적.**

---

## Step 3: 하이브리드 검색 실험

### 실험 3-1: alpha 파라미터 비교

```bash
# 기본 (alpha 0.0~1.0 전체 비교)
python -m tuning.step3_hybrid_search --step 3-1

# 특정 alpha만 테스트
python -m tuning.step3_hybrid_search --step 3-1 --alpha 0.7
```

`alpha`는 BM25와 Vector의 가중치 비율입니다:

| alpha | BM25 | Vector | 특성 |
|-------|------|--------|------|
| 0.0 | 100% | 0% | 키워드 정확 매칭만 |
| 0.5 | 50% | 50% | 균형 (권장) |
| 0.7 | 30% | 70% | 의미 검색 중심 |
| 1.0 | 0% | 100% | 벡터 유사도만 |

### 실험 3-2: 하이브리드 검색 데모

```bash
# 기본 (alpha=0.5)
python -m tuning.step3_hybrid_search --step 3-2

# alpha를 바꿔서 실험
python -m tuning.step3_hybrid_search --step 3-2 --alpha 0.7
```

3개 질문에 대해 BM25 결과, Vector 결과, 하이브리드 결과를 나란히 보여줍니다.

---

## 전체 실험 한 번에 실행

```bash
# Step 1 전체 (1-1, 1-2, 1-3)
python -m tuning.step1_chunk_experiment

# Step 2 전체 (2-1, 2-2)
python -m tuning.step2_reranker

# Step 3 전체 (3-1, 3-2)
python -m tuning.step3_hybrid_search
```

> **Tip:** 실험을 돌리면서 파라미터를 하나씩 바꿔보세요.
> 숫자가 바뀌는 것을 직접 눈으로 확인하는 것이 가장 빠른 이해 방법입니다.
