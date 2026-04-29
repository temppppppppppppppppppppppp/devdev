# 사례 1. 콘솔 로그로 읽는 글도비 제작 공정

Date: 2026-04-29
Document Type: human-facing case study / PDF-ready source
Source Log: `0_temp.txt`
Runtime Project: `projects/0_카나리아`
Genre: 투자 (Investment Fiction)
Scope: Stage 0 기준선 연결 -> Stage 2 Arc Tactical Design 완료 -> Stage 3 Blueprint 생성 시작
Out of Scope: Stage 4 최종 원고 생산, 최종 원고 품질 평가, 전체 코드 감사

## 대전제: LLM은 구조화된 언어를 더 안정적으로 다룬다

이 시스템을 이해하기 위한 첫 전제는 이것이다.

> LLM은 순수한 자유 산문보다 JSON, key/value, table, schema, verdict, route, anchor처럼 구조가 드러난 언어를 더 안정적으로 다룬다.

웹소설은 최종적으로 독자가 읽는 자연어 원고가 되어야 한다. 하지만 제작 과정 전체를 자연어 감각에만 맡기면, 장편에서 중요한 설정, 상태, 판단 근거, 수정 이력이 쉽게 흐려진다.

그래서 글도비는 작품을 한 번에 원고로 생성하지 않는다. 먼저 작품 정보를 `Bible`, `Roadmap`, `style_guide`, `arc_payload`, `stage_attempt`, `director_selection` 같은 구조화된 단위로 나누고, LLM이 판단하기 쉬운 형태로 다시 묶어 Director에게 넘긴다.

즉 DB와 JSON은 개발자 취향의 부속물이 아니다. LLM이 장편 제작을 더 안정적으로 다루게 하기 위한 제작 언어다.

## 0. 한 문장 요약

이 사례는 글도비가 AI에게 바로 원고를 쓰게 하는 도구가 아니라, 장르 선택, 작품 기준선 연결, 문체 분석, 아크 설계, Director 심사, 상태 동기화를 거쳐 장편 웹소설 제작을 관리하는 단계형 제작 공정임을 보여준다.

## 1. 이 사례가 보여주는 문제

장편 웹소설 제작에서 어려운 부분은 한 번 그럴듯한 문장을 생성하는 것이 아니다. 더 큰 문제는 긴 제작 과정에서 다음 요소가 무너지지 않게 관리하는 것이다.

- 작품 설정과 장기 설계의 일관성
- 장르별 제작 규칙
- 인물, 자산, 장소, 관계 같은 상태 연속성
- 문체 기준과 금지 패턴
- 생성 결과에 대한 품질 판단과 재심사
- 각 단계의 기록과 추적 가능성

이 로그는 위 문제를 풀기 위해 글도비가 `생성`, `판단`, `기록`, `상태 동기화`를 분리해 운영하는 장면을 보여준다.

## 2. 로그를 읽는 방법

이 문서는 콘솔 로그를 세 층으로 읽는다.

1. 콘솔 표면: 운영자가 실행 중 보는 화면이다.
2. DB/기록 표면: 실행이 끝난 뒤에도 남는 제작 장부다.
3. 설계 선택: 왜 이런 단계와 기록 장치를 둔 것인지에 대한 해석이다.

중요한 원칙은 이것이다.

> 콘솔 로그는 사건의 화면이고, DB는 사건의 기억이다.

따라서 이 사례의 핵심은 "화면에 뭔가 많이 출력된다"가 아니다. 핵심은 출력된 사건들이 프로젝트 DB와 내부 산출물에 연결되어 다음 단계의 근거가 된다는 점이다.

## 3. 증거 기준

### 3.1 원본 로그 기준

원본 로그는 `0_temp.txt`에 저장된 `python main_a.py` 실행 기록이다. 확인된 주요 흐름은 다음과 같다.

- V40 장르 선택 화면 진입
- 투자 장르 선택
- 프로젝트 `0_카나리아` 선택
- Vector DB, Director, Writer Guard, Quality Dashboard 등 초기화
- Stage 0에서 Bible/Roadmap 연결
- 주인공, 회귀 설정, POV, 외부 시점 정책 저장
- 스타일 레퍼런스 분석 실행
- 작품가드 메뉴 진입
- Stage 2 Arc Tactical Design 실행
- Arc 1~4 생성, 검증, Director 판정
- Arc 4 PASS_WITH_FIX 이후 patch 및 재심사 PASS
- Stage 2 완료 후 Stage 3 Blueprint 생성 시작

### 3.2 DB 기준

동일 프로젝트의 `projects/0_카나리아/project_data.db` 확인 결과, 사례 시점에서 다음 기록이 존재했다.

| Table | Count | 의미 |
| --- | ---: | --- |
| `anchors` | 14 | 작품 기준선과 장기 산출물 anchor |
| `director_selections` | 4 | Director 판단 기록 |
| `stage_attempts` | 4 | Stage 2 Arc 시도 기록 |
| `llm_calls` | 49 | 에이전트/모델 호출 기록 |
| `cost_log` | 4 | Arc별 호출 수, 토큰, 비용 기록 |
| `ui_events` | 484 | 콘솔/운영자 이벤트 기록 |
| `blueprints` | 0 | Stage 3는 시작됐지만 저장 완료 전 |
| `manuscripts` | 0 | Stage 4 원고 생산 전 |

확인된 주요 anchor는 다음과 같다.

```text
arc_payload_0001
arc_payload_0002
arc_payload_0003
arc_payload_0004
arc_summary_1
arc_summary_2
arc_summary_3
arc_summary_4
arcs
bible
financial_registry
genre_info
stage2_arcs_source_lineage
style_guide
```

이 DB 상태는 이 사례가 "원고 생성 사례"가 아니라 "장르/설정/문체/아크 설계를 런타임 기억으로 고정한 사례"임을 보여준다.

## 4. 단계별 해설

## 4.1 장르 선택: 범용 채팅이 아니라 장르별 제작 공정으로 시작한다

### 콘솔 로그 증거

```text
📚 [V40 Multi-Genre Factory] 장르를 선택하십시오:
3. 투자 (Investment Fiction)
✅ [투자 (Investment Fiction)] 전문 공정이 선택되었습니다.
📌 HUD 시스템: INVESTMENT
📦 프리셋 초기화: investment
```

### 사람 말 번역

사용자는 빈 채팅창에서 "소설 써줘"로 시작하지 않는다. 먼저 장르를 선택하고, 시스템은 그 장르에 맞는 HUD, 프리셋, Guard를 준비한다.

이 사례에서는 투자 장르가 선택되었기 때문에 자본, 투자, 기업, 시장 같은 장르 축이 이후 설계의 기본 환경이 된다.

### DB/기록 관점

프로젝트 선택 직후 로그에는 다음 기록이 나타난다.

```text
preset_registry DB에서 복원 완료
프로젝트 장르 정보 저장: 투자 (Investment Fiction)
```

DB anchor 기준으로는 `genre_info`가 존재한다. 즉 장르 선택은 단순 화면 선택이 아니라 이후 단계가 참조할 프로젝트 기억으로 저장된다.

### 설계 이유

장편 제작에서 장르는 장식이 아니라 판단 기준이다. 투자물에서 중요한 것은 전투력 수치가 아니라 자본 흐름, 거래 구조, 손익, 회수 전략, 신뢰 관계다. 그래서 장르를 먼저 고정해야 이후 생성과 검증이 같은 기준을 공유할 수 있다.

### 카드뉴스 문장

제목: "글도비는 빈 채팅창에서 시작하지 않는다"

본문: "장르를 먼저 고정하고, 그 장르에 맞는 제작 규칙과 검증 장치를 켠 뒤 작품을 시작한다."

## 4.2 시스템 초기화: 원고보다 먼저 판단자와 기록 장치를 켠다

### 콘솔 로그 증거

```text
Vector DB integrity check complete.
sqlite-vec 벡터 엔진 초기화 완료
Stage 2 고도화 모듈 초기화 (Ensemble + DraftValidator + ConstraintCompiler)
Stage 2 초기통과율 극대화 모듈 초기화 (FourPhase + Preflight + Critic + Consensus)
Director 장르 설정: investment
Director Guard 연결 완료
Writer Guard/Genre 연결 완료
Quality Dashboard 활성화
```

### 사람 말 번역

원고를 쓰기 전에 기억 장치, 검증기, Director, Writer Guard, 품질 대시보드가 먼저 켜진다. 이 구조는 "생성 후 나중에 대충 보기"가 아니라 "생성 전에 필요한 판단 환경을 먼저 세팅하기"에 가깝다.

### DB/기록 관점

이 단계에서 핵심은 DB 테이블 하나에 특정 문장이 저장된다는 것보다, 이후 모든 단계가 DB와 로그에 남을 준비를 끝낸다는 점이다. 실제 DB에는 `llm_calls`, `stage_attempts`, `director_selections`, `cost_log`, `ui_events` 같은 운영 기록 테이블이 존재한다.

### 설계 이유

LLM은 생성 자체는 할 수 있지만, 장편 제작에서는 "무엇을 기준으로 합격시킬 것인가"가 더 중요하다. 따라서 생성기보다 먼저 판단자와 기록 장치를 준비한다.

### 카드뉴스 문장

제목: "글을 쓰기 전에 제작실을 먼저 켠다"

본문: "기억, 검증, 판단, 비용 추적이 준비된 뒤에야 생성 단계가 시작된다."

## 4.3 Stage 0: 작품 기준선을 런타임에 연결한다

### 콘솔 로그 증거

```text
Stage 0 - 프로젝트 설정
Bible Selection
Roadmap Selection
로드맵 선택 완료
설계도(50개)와 원고 역사가 무결하게 통합되었습니다.
```

### 사람 말 번역

Stage 0은 작품의 기준 자료를 시스템에 연결하는 구간이다. 여기서 Bible은 세계관, 인물, 설정의 기준선이고, Roadmap/Treatment는 장기 전개 설계다.

즉 이 단계는 원고 작성이 아니라 "이 작품이 무엇을 기준으로 쓰여야 하는지"를 런타임에 장착하는 과정이다.

### DB/기록 관점

DB anchor에는 `bible`과 `arcs`가 존재한다. 이후 Stage 2 로그에도 다음 계약이 나타난다.

```text
runtime_handoff_owner=db_anchor:bible
stage2_surface=MasterBible.plot_roadmap
stage2_consumer_mode=db_anchor_first
plot_roadmap_authority=MasterBible.plot_roadmap
```

이 문장은 Stage 2가 파일명이나 운영자 기억이 아니라 DB anchor의 Bible/plot_roadmap을 우선 기준으로 삼는다는 뜻이다.

### 설계 이유

장편 제작은 앞부분의 설정이 뒤에서 계속 효력을 가져야 한다. 그래서 Stage 0은 "자료 업로드"가 아니라 "이후 단계가 참조할 권위 있는 기준선 확정"에 가깝다.

### 카드뉴스 문장

제목: "Stage 0은 원고 작성이 아니라 기준선 장착이다"

본문: "작품의 Bible과 Roadmap을 DB anchor에 연결해야 이후 설계와 판단이 같은 기준을 본다."

## 4.4 주인공과 서술 정책: 이야기의 허용 범위를 먼저 고정한다

### 콘솔 로그 증거

```text
주인공의 세계관 출신을 선택하세요
주인공의 유형을 선택하세요
서술 시점을 선택하세요
외부 시점 삽입 정책을 선택하세요
주인공 설정이 Bible에 저장됨
```

### 사람 말 번역

이 단계는 "주인공이 누구인가"만 정하는 것이 아니다. 회귀자 여부, 회귀 시점, 서술 시점, 외부 시점 허용 정도처럼 이후 모든 에피소드에 영향을 주는 서술 규칙을 정한다.

사례에서는 현대인, 회귀 관련 설정, 혼합 POV, 제한적 외부 시점 허용이 저장된다.

### DB/기록 관점

로그에는 "Bible에 저장됨"이 명시되어 있다. 이는 주인공 정책이 일회성 입력이 아니라 `bible` anchor의 일부로 들어가 이후 설계와 원고 생성의 기준이 된다는 의미다.

### 설계 이유

장편에서 POV와 회귀 정보는 작은 설정이 아니다. 이 규칙이 흔들리면 독자는 같은 작품을 읽고 있다고 느끼기 어렵다. 그래서 문체보다 먼저 서술 권한과 정보 공개 범위를 고정한다.

### 카드뉴스 문장

제목: "주인공 설정은 취향 입력이 아니라 서술 계약이다"

본문: "회귀, 시점, 외부 시점 허용 여부는 이후 모든 장면의 정보 공개 방식을 결정한다."

## 4.5 스타일 레퍼런스: 참조 원고를 모방이 아니라 제작 규칙으로 분해한다

### 콘솔 로그 증거

```text
스타일 레퍼런스 분석 - 참조 원고에서 문체 DNA 추출
문체 분석 시작: 1화, 4,247,609자
통계 분석
샘플 큐레이션
리듬 분석
LLM 심층 분석
Anti-AI 패턴 생성
StyleGuide DB 저장 완료 (anchor: style_guide)
```

### 사람 말 번역

이 단계는 참조 원고를 그대로 베끼는 과정이 아니다. 시스템은 대량의 참조 텍스트에서 문장 리듬, 모범 문단, 피해야 할 AI식 표현 패턴을 추출해 별도의 스타일 가이드로 만든다.

### DB/기록 관점

DB anchor에는 `style_guide`가 존재한다. 로그의 `StyleGuide DB 저장 완료`와 일치한다.

### 설계 이유

웹소설 제작에서 문체는 "예쁘게 쓰기" 문제가 아니라 독자가 기대하는 읽기 리듬의 문제다. 참조 문체를 매번 프롬프트에 감으로 설명하면 흔들리기 쉽기 때문에, 분석 결과를 스타일 기준선으로 저장한다.

### 카드뉴스 문장

제목: "문체는 감이 아니라 추적 가능한 기준선이 된다"

본문: "참조 원고를 리듬, 샘플, 금지 패턴으로 분해해 이후 생성의 스타일 기준으로 저장한다."

## 4.6 Work Guard: 작품별 금지선과 감각을 별도 계약으로 다룬다

### 콘솔 로그 증거

```text
작품가드 설정 (선택)
라이브러리에서 가져오기
기본 템플릿으로 초기화
현재 프로젝트 작품가드 미리보기
현재 프로젝트 작품가드 삭제
잘못된 선택입니다.
```

### 사람 말 번역

이 실행에서는 작품가드 가져오기가 성공하지 않았다. 그러나 메뉴 자체는 중요한 설계 방향을 보여준다. 글도비는 작품별 금지선과 유지해야 할 감각을 별도 artifact로 다룰 수 있게 되어 있다.

### DB/기록 관점

이 사례 로그만으로는 work_guard가 성공적으로 저장되었다고 말할 수 없다. 확인 가능한 것은 "작품가드 설정 경로가 존재했고, 이 실행에서는 잘못된 선택으로 완료되지 않았다"는 점이다.

### 설계 이유

작품마다 망가지면 안 되는 선이 다르다. 어떤 작품은 주인공 품위가 중요하고, 어떤 작품은 손익 계산의 현실감이 중요하다. 이런 규칙은 범용 검증기만으로 충분하지 않기 때문에 작품별 guard가 필요하다.

### 카드뉴스 문장

제목: "작품마다 망가지면 안 되는 선이 다르다"

본문: "글도비는 작품별 금지선과 유지해야 할 감각을 별도 Guard로 다루는 구조를 갖고 있다."

## 4.7 Stage 2 진입: 장기 설계를 Arc 단위 전술서로 바꾼다

### 콘솔 로그 증거

```text
Stage 2: Arc Tactical Design
Volume 전략 없이도 Arc 설계를 진행할 수 있습니다.
Stage 1을 건너뛰고 진행하시겠습니까?
Stage 2 0124 매니페스트 정합 엔진 및 멀티 공정 기동
현재 단계 완료: 0 / 60 아크
몇 번 아크까지 단계하시겠습니까? 현재 1 ~ 최대 60: 4
```

### 사람 말 번역

Stage 2는 장기 Treatment/Roadmap을 실제 제작 가능한 Arc 전술서로 바꾸는 단계다. 이 사례에서는 사용자가 4번 Arc까지 진행하도록 지정했고, 시스템은 Arc 1~4를 순차적으로 설계한다.

### DB/기록 관점

DB에는 `arc_payload_0001`부터 `arc_payload_0004`, `arc_summary_1`부터 `arc_summary_4`, 그리고 전체 `arcs` anchor가 존재한다.

### 설계 이유

장편 원고를 바로 쓰면 큰 흐름과 세부 장면이 서로 어긋나기 쉽다. 그래서 먼저 Arc 단위로 목표, 갈등, 상태 변화, 보상 구조를 전술화한다.

### 카드뉴스 문장

제목: "장편은 바로 원고로 가지 않는다"

본문: "먼저 장기 설계를 Arc 단위 전술서로 바꿔, 각 구간이 무엇을 해야 하는지 정한다."

## 4.8 Batch Enrich: 원본 블록을 제작 가능한 정보로 보강한다

### 콘솔 로그 증거

```text
Batch 1~4 range enrich start
Block 1 task start
Block 2 task start
Block 3 task start
Block 4 task start
Block 1 task done
Block 2 task done
Block 4 task done
Block 3 task done
Enrich Phase completed: 52.9s (4 items)
```

### 사람 말 번역

원본 Roadmap 블록은 그대로 원고가 되기에는 거칠다. Batch Enrich는 각 블록을 실제 Arc 설계에 필요한 정보로 보강하는 단계다.

### DB/기록 관점

최종적으로 보강된 Arc 산출물은 `arc_payload_0001`부터 `arc_payload_0004` anchor와 `arcs` anchor에 반영된다.

### 설계 이유

기획 문장은 원고 지시서가 아니다. 제작에 쓰려면 목표, 제약, 인과, 상태 변화, 장르 규칙이 더 명확해야 한다. Enrich 단계는 이 간극을 메운다.

### 카드뉴스 문장

제목: "기획 문장을 바로 원고로 쓰지 않는다"

본문: "원본 블록을 Arc 설계에 필요한 전술 정보로 보강한 뒤 다음 단계로 넘긴다."

## 4.9 인과율 용접: Arc 사이의 연결부를 먼저 고정한다

### 콘솔 로그 증거

```text
Arc 1-2 고유 명사 앵커링 완료
Arc 1-2 인과율 용접 완료
Arc 2-3 고유 명사 앵커링 완료
Arc 2-3 인과율 용접 완료
Arc 3-4 고유 명사 앵커링 완료
Arc 3-4 인과율 용접 완료
```

### 사람 말 번역

각 Arc는 독립된 아이디어가 아니라 이어지는 장편 구간이다. 그래서 시스템은 Arc 사이의 고유명사, 사건, 상태 연결이 끊기지 않도록 먼저 맞춘다.

### DB/기록 관점

DB에는 `arc_dependencies` 테이블과 Arc anchor들이 존재한다. 이 사례에서 `arc_dependencies`에는 2건이 확인되었고, Arc payload와 summary anchor들이 남아 있다.

### 설계 이유

장편에서 가장 흔한 문제는 "앞에서 만든 사건이 뒤에서 사라지는 것"이다. 인과율 용접은 Arc 사이의 접합부를 먼저 보는 장치다.

### 카드뉴스 문장

제목: "Arc는 따로 쓰는 조각이 아니라 이어 붙이는 구조물이다"

본문: "고유명사와 사건 연결을 먼저 맞춰야 뒤의 원고가 앞의 이야기를 배신하지 않는다."

## 4.10 Preflight와 FourPhase: 생성 전에 위험 조건을 먼저 모은다

### 콘솔 로그 증거

```text
Preflight 병렬 분석 시작 (arc_drive + preflight + constraint)
Preflight arc_drive 완료
Preflight preflight 완료
Preflight constraint 완료
Stage 2 Arc attempt 1/10
FourPhase-Director 대면 1/5
generation=four_phase
validation 진입
Pre-Director 검증 체인 시작
```

### 사람 말 번역

Arc를 생성하기 전에 시스템은 먼저 무엇을 지켜야 하는지, 어떤 위험이 있는지, 어떤 제약을 넣어야 하는지 모은다. 그 뒤 FourPhase 생성과 Pre-Director 검증을 거쳐 Director 심사로 보낸다.

### DB/기록 관점

DB의 `stage_attempts`에는 Arc 1~4가 모두 `generation_method=four_phase`로 기록되어 있다. 또한 `llm_calls`에는 `arc_ensemble_generator`, `preflight_checker`, `analyst`, `director`, `state_extractor` 등 에이전트별 호출 기록이 남아 있다.

### 설계 이유

LLM에게 한 번에 "좋은 Arc 만들어줘"라고 요청하면 실패 원인을 추적하기 어렵다. Preflight와 FourPhase는 생성 이전의 조건 수집, 생성, 검증, 심사를 분리해 실패를 추적 가능하게 만든다.

### 카드뉴스 문장

제목: "생성 전에 먼저 위험 조건을 모은다"

본문: "Preflight가 요구 조건과 제약을 정리하고, FourPhase 생성물이 Director 심사로 넘어간다."

## 4.11 Director 판정: 합격은 코드 조건문이 아니라 서사 판단으로 남는다

### 콘솔 로그 증거

```text
Director 전략적 무결성 검수 중
Director PASS (score=100)
Director PASS (score=95)
Director PASS_WITH_FIX (score=90)
PASS_WITH_FIX patch #1/3
Director 재심사 #1 호출 중
재심사 #1: PASS (score=100)
Arc 수정 완료 -> PASS 확정
```

### 사람 말 번역

Director는 생성물을 바로 통과시키지 않는다. Arc 1~3은 PASS를 받았고, Arc 4는 PASS_WITH_FIX를 받은 뒤 patch와 재심사를 거쳐 최종 PASS로 확정되었다.

이 장면은 글도비가 "LLM이 쓴 것을 그대로 저장하는 시스템"이 아니라, 생성 결과를 심사하고 필요한 경우 수정 루프를 태우는 시스템임을 보여준다.

### DB/기록 관점

DB 확인 결과 `director_selections`에는 4건, `stage_attempts`에는 4건이 남아 있다. `stage_attempts` 기준 Arc 1~4의 최종 기록은 다음과 같다.

| Arc | Attempt | Method | Verdict | Score | Duration |
| ---: | ---: | --- | --- | ---: | ---: |
| 1 | 1 | `four_phase` | PASS | 100 | 14,843 ms |
| 2 | 1 | `four_phase` | PASS | 95 | 35,422 ms |
| 3 | 1 | `four_phase` | PASS | 95 | 44,234 ms |
| 4 | 1 | `four_phase` | PASS | 100 | 35,577 ms |

Arc 4는 콘솔 로그에서 PASS_WITH_FIX와 재심사 과정을 거친 뒤 최종 DB에는 PASS score 100으로 남은 것으로 해석된다.

### 설계 이유

Python이 "이 이야기는 좋다/나쁘다"를 결정하면 서사 판단이 코드 조건문으로 굳어 버린다. 반대로 LLM 판단이 기록 없이 휘발되면 나중에 왜 통과됐는지 알 수 없다. 그래서 Director가 판단하고, 그 판단을 DB에 남긴다.

### 카드뉴스 문장

제목: "Director는 생성물을 그냥 믿지 않는다"

본문: "PASS, PASS_WITH_FIX, 재심사 기록을 남겨 생성 결과가 어떤 이유로 통과됐는지 추적한다."

## 4.12 상태 동기화: 다음 Arc가 이전 Arc의 결과를 이어받게 한다

### 콘솔 로그 증거

```text
ConstraintDB 업데이트 완료
StateExtractor context ready
Stage2 Carryover Authority
start=서울 성북동 본가 저택 한시우의 침실 -> end=SW인베스트먼트 대표실
assets=20억원
assets=23억원
Carryover Sync
total_assets, capital, portfolio_position
```

### 사람 말 번역

Arc가 통과된 뒤에는 상태를 다음 Arc로 넘긴다. 이 사례에서는 장소, 소지품, 자산, 포트폴리오 포지션 같은 상태가 추적된다.

장편에서 이런 정보가 이어지지 않으면, 주인공이 가진 돈이나 위치, 관계가 매번 흔들린다.

### DB/기록 관점

DB에는 `financial_registry`, `arc_payload_*`, `arc_summary_*`, `arcs`, `stage_attempts`가 남아 있다. Stage 4 원고 생산 전이므로 `manuscripts`, `state_logs`, `episode_meta`는 아직 0건이다.

### 설계 이유

투자 장르에서 자산과 포지션은 장식이 아니라 플롯의 핵심 상태다. 상태 동기화가 없으면 다음 Arc가 이전 Arc의 성과와 리스크를 잊어버릴 수 있다.

### 카드뉴스 문장

제목: "장편은 기억을 잃는 순간 무너진다"

본문: "장소, 자산, 포지션, 관계 상태를 다음 Arc로 넘겨 이야기가 같은 세계 안에서 이어지게 한다."

## 4.13 Stage 3 진입: Arc 설계가 Episode Blueprint로 넘어간다

### 콘솔 로그 증거

```text
Stage 2: Arc Tactical Design [완료]
Stage 3: Episode Blueprinting
Arc 설계: 4개 완료
Blueprint: ep 0까지 완료
원고: ep 0까지 완료
예상 총 에피소드: 17
Three Phase Blueprint Generator 시작
범위: 제1화 ~ 제15화
Entity Registry 추출: 47개 엔티티
제1화 Blueprint 생성 중
```

### 사람 말 번역

Stage 2가 끝나면 시스템은 Arc 전술서를 에피소드 단위 설계도로 풀기 시작한다. 이 사례에서는 4개 Arc가 완료된 뒤 총 17화까지 설계 가능하다고 판단하고, 1화부터 15화까지 Blueprint 생성을 시작한다.

### DB/기록 관점

사례 시점의 DB에서 `blueprints`는 0건이었다. 따라서 이 문서에서는 "Stage 3 생성이 시작되었다"까지만 말할 수 있고, Blueprint 저장 완료까지는 주장하지 않는다.

### 설계 이유

Arc는 큰 전개 단위이고, Episode Blueprint는 실제 회차 생산에 가까운 단위다. 글도비는 큰 설계를 바로 원고로 보내지 않고, 중간에 회차 설계도로 한 번 더 쪼갠다.

### 카드뉴스 문장

제목: "Arc가 끝나면 바로 원고가 아니라 회차 설계도로 간다"

본문: "장기 전술을 Episode Blueprint로 쪼개야 실제 회차 생산이 흔들리지 않는다."

## 5. 이 사례에서 가장 중요한 설계 선택 5가지

## 5.1 장르별 공정 선택

투자 장르는 자본, 시장, 법인, 거래, 회수 전략이 중요하다. 그래서 장르 선택은 UI 옵션이 아니라 이후 판단 기준을 정하는 시작점이다.

## 5.2 DB anchor 중심의 기준선

Stage 0에서 연결한 Bible/Roadmap은 이후 Stage 2의 권위 표면이 된다. `runtime_handoff_owner=db_anchor:bible`이라는 로그가 이 구조를 잘 보여준다.

## 5.3 생성과 판단의 분리

FourPhase가 생성하고, Pre-Director가 검증하고, Director가 최종 판단한다. 이 분리는 "좋은 서사인가"를 Python 조건문에 맡기지 않기 위한 구조다.

## 5.4 실패를 숨기지 않는 repair loop

Arc 4는 처음부터 완전 PASS가 아니었다. PASS_WITH_FIX 이후 patch와 재심사를 거쳤다. 이 장면은 글도비가 실패를 숨기지 않고 수정 가능한 단위로 만든다는 점을 보여준다.

## 5.5 상태 carryover

자산, 위치, 소지품, 포트폴리오 상태가 다음 Arc로 넘어간다. 장편 제작에서 상태 carryover는 원고 품질만큼 중요한 기반이다.

## 6. 이 사례를 카드뉴스로 바꾸는 구성안

1. 표지
   - 제목: 콘솔 로그로 읽는 AI 웹소설 제작 공정
   - 문장: 글도비는 원고 생성기가 아니라 장편 제작 파이프라인이다.

2. 문제 정의
   - 로그 증거: 장르 선택 전 초기 화면
   - 번역: 빈 채팅이 아니라 제작 공정으로 시작한다.
   - 설계 이유: 장편은 기준 없는 생성으로 유지되지 않는다.

3. 장르 선택
   - 로그 증거: 투자 장르 선택, HUD 시스템 INVESTMENT
   - 번역: 투자 장르의 판단 기준을 먼저 고정한다.
   - 설계 이유: 장르마다 실패 조건이 다르다.

4. 시스템 초기화
   - 로그 증거: Vector DB, Director Guard, Writer Guard, Quality Dashboard
   - 번역: 원고보다 먼저 기억과 판단 장치를 켠다.
   - 설계 이유: 생성 결과를 추적하고 심사하기 위해서다.

5. Stage 0
   - 로그 증거: Bible/Roadmap 선택
   - 번역: 작품 기준선을 런타임에 연결한다.
   - 설계 이유: 이후 단계가 같은 기준을 봐야 한다.

6. 주인공/POV 정책
   - 로그 증거: 회귀, POV, 외부 시점 정책 저장
   - 번역: 정보 공개 규칙을 먼저 정한다.
   - 설계 이유: 시점 규칙이 흔들리면 장편 몰입이 깨진다.

7. 스타일 분석
   - 로그 증거: 4,247,609자 분석, StyleGuide DB 저장
   - 번역: 참조 문체를 제작 규칙으로 분해한다.
   - 설계 이유: 문체를 감이 아니라 기준선으로 만든다.

8. Stage 2 진입
   - 로그 증거: Arc Tactical Design, 4개 Arc 지정
   - 번역: 장기 설계를 Arc 전술서로 바꾼다.
   - 설계 이유: 큰 설계와 실제 원고 사이에 중간 단위가 필요하다.

9. Batch Enrich
   - 로그 증거: Block 1~4 enrich 완료
   - 번역: 원본 블록을 제작 가능한 정보로 보강한다.
   - 설계 이유: 기획 문장은 바로 원고 지시서가 아니다.

10. 인과율 용접
    - 로그 증거: Arc 1-2, 2-3, 3-4 용접 완료
    - 번역: Arc 사이 연결부를 먼저 맞춘다.
    - 설계 이유: 장편은 앞뒤가 끊기면 무너진다.

11. Director 심사
    - 로그 증거: PASS, PASS_WITH_FIX, 재심사 PASS
    - 번역: 생성물은 심사와 수정 루프를 거쳐 통과된다.
    - 설계 이유: 품질 판단은 코드 조건문이 아니라 Director가 맡는다.

12. 상태 carryover
    - 로그 증거: assets, location, portfolio_position
    - 번역: 다음 Arc가 이전 Arc의 결과를 이어받는다.
    - 설계 이유: 특히 투자물은 자산 상태가 플롯 그 자체다.

13. Stage 3 전환
    - 로그 증거: Three Phase Blueprint Generator 시작
    - 번역: Arc 설계를 회차 설계도로 쪼갠다.
    - 설계 이유: 실제 원고 생산 전에 회차 단위 계획이 필요하다.

14. 마무리
    - 문장: 글도비는 AI가 한 번 글을 쓰는 시스템이 아니라, 장편 작품이 기억을 잃지 않게 운영하는 제작 인프라다.

## 7. GPT에게 콘솔 로그 해석을 맡길 때의 프롬프트

다음 프롬프트는 `0_temp.txt`를 외부 GPT에 붙여 넣을 때 사용할 수 있다.

```text
아래 자료는 장편 웹소설 제작 AI 파이프라인의 실제 콘솔 로그입니다.

당신의 역할은 "콘솔 로그 해설자"입니다.
개발자가 아닌 사람도 이해할 수 있게, 로그가 의미하는 제작 공정과 설계 이유를 설명해 주세요.

출력 형식:

1. 전체 요약
- 이 실행 로그가 보여주는 시스템의 목적
- 이 시스템이 단순 생성기가 아니라 제작 파이프라인인 이유

2. 단계별 해석
각 단계마다 아래 형식으로 정리하세요.

[콘솔에 보이는 것]
로그에서 중요한 문장 3~5개를 짧게 인용하거나 요약

[무슨 일이 일어난 건가]
비개발자가 이해할 수 있게 설명

[DB나 기록 관점에서 중요한 것]
이 단계에서 시스템이 기억하거나 저장하는 것으로 보이는 것

[설계 이유]
왜 이런 구조가 필요한지 설명

[카드뉴스 문장]
이 단계를 한 장의 카드뉴스로 만들 때 쓸 수 있는 제목과 본문

3. 중요한 설계 선택
- 장르 선택
- 프로젝트 선택
- Stage 0
- Bible / Treatment / Roadmap 연결
- Style Reference 분석
- Work Guard
- Stage 2 Arc 설계
- Preflight
- FourPhase generation
- Director 심사
- PASS / PASS_WITH_FIX 판정
- 상태 동기화
- 비용/토큰/호출 기록

4. 주의할 점
로그만 보고 확정할 수 없는 것은 "추정"이라고 표시하세요.
코드나 DB를 직접 본 것처럼 말하지 마세요.
콘솔 로그에 나타난 증거와 해석을 구분하세요.

5. 마지막으로
이 로그를 바탕으로 카드뉴스 10~15장짜리 구성안을 만들어 주세요.
각 카드는 "제목 / 로그 증거 / 사람 말 번역 / 설계 이유" 형식으로 작성하세요.

아래부터 콘솔 로그입니다.
```

## 8. PDF/카드뉴스용 톤 가이드

이 사례는 내용이 기술적이므로 시각 톤은 부드럽게 잡는 편이 좋다.

- 배경: 따뜻한 화이트 또는 연한 종이색
- 본문: 차콜
- 강조색: 청록, 코랄, 진한 잉크색
- 카드 구조: 큰 문장 1개 + 로그 조각 + 사람 말 번역
- 콘솔 로그는 전체를 크게 보여주지 말고, 증거 조각처럼 작게 사용
- DB는 테이블 원본보다 "무엇을 기억하는가" 중심으로 표현

## 9. 3-pass 문서 감리 메모

### Pass 1. 구조와 범위

- 문서 유형은 사례 해설 / PDF-ready 원고로 한정했다.
- 범위는 `0_temp.txt` 로그와 `projects/0_카나리아/project_data.db` 관찰에 한정했다.
- 맨앞에 "LLM은 구조화된 언어를 더 안정적으로 다룬다"는 대전제를 추가해 DB/JSON/anchor 구조의 설계 이유를 먼저 제시했다.
- Stage 4 원고 생산과 원고 품질 평가는 범위 밖으로 명시했다.
- Stage 3은 시작 로그까지만 다루고, Blueprint 저장 완료는 주장하지 않았다.

### Pass 2. 증거와 일관성

- 콘솔 로그에서 확인 가능한 사건과 DB readback에서 확인한 테이블/anchor/count를 분리했다.
- Work Guard는 이 실행에서 성공 저장된 것으로 쓰지 않고, 메뉴 노출 및 실패 선택으로 제한했다.
- Arc 4는 콘솔상 PASS_WITH_FIX 후 재심사 PASS, DB상 최종 PASS score 100으로 구분해 설명했다.
- `blueprints`, `manuscripts`, `episode_bibles`, `state_logs`, `episode_meta`, `episode_fts`는 0건임을 반영했다.

### Pass 3. 실행성과 가독성

- 각 단계마다 "콘솔 로그 증거 / 사람 말 번역 / DB 관점 / 설계 이유 / 카드뉴스 문장" 형식을 반복했다.
- 비개발자가 읽을 수 있도록 테이블명은 필요한 경우에만 노출하고, 의미를 함께 붙였다.
- 이후 작업은 이 문서를 카드뉴스 PDF 또는 기술 해설 PDF로 변환하는 것이다.

Estimated Confidence: 96%
