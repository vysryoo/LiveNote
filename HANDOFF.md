# 작업 인수인계

이 문서는 이전 세션에서 진행한 내용을 다음 에이전트가 이어받기 위한 것이다. 대화 맥락 없이 이 문서만으로 작업을 재개할 수 있도록 작성했다.

작업 시작 전 `AGENTS.md`를 읽는다. 코드를 한 줄이라도 수정한다면 `.agent/coding.md`를 먼저 읽는다.

---

## 1. 현재 상태 요약

| 항목 | 상태 |
| --- | --- |
| 저장소 재구성 | 완료 |
| 프론트엔드 현황 조사 | 완료 |
| 재작성 설계 결정 | 완료 (사용자와 문답으로 확정) |
| 구현 | **착수 전** |

구현은 한 줄도 시작하지 않았다. 설계만 확정된 상태다.

상세 계획 파일은 `C:\Users\vysry\.claude\plans\validated-inventing-sutherland.md`에 있다. 이 문서와 내용이 겹치나, 계획 파일이 마일스톤 원본이다.

---

## 2. 저장소 상태

### 2-1. 완료된 작업

`vysryoo/LiveNote`의 포크 관계가 끊겨 있던 것을 재구성함. 경위는 다음과 같다.

- 기존 저장소는 GitHub API상 `fork:false`, `parent:null`이었으나 `origin/feat/back_merge01`의 SHA가 `Team-GongGong-s/LiveNote_frontend`와 완전히 동일해 원본이 확인됨
- private 전환 과정에서 fork network를 떠나 관계가 끊긴 것으로 추정됨
- 포크 배지와 private은 동시에 유지 불가하므로, 사용자가 public 수용을 선택함
- 기존 저장소를 `LiveNote-old`로 rename → `LiveNote_frontend`를 `LiveNote`라는 이름으로 포크 → 모노레포 `main` 푸시 → 기본 브랜치를 `main`으로 변경 → 모든 ref 포함 확인 후 `LiveNote-old` 삭제

현재 상태.

```
repo    : vysryoo/LiveNote
fork    : true
parent  : Team-GongGong-s/LiveNote_frontend
private : false
default : main
```

로컬 remote는 `origin`(본인 저장소)과 `upstream`(원본 팀 저장소) 두 개다.

`main`(`cad395f`)이 유일한 브랜치다. `master`와 `feat/back_merge01`은 아래 보안 사유로 삭제했다.

### 2-2. 커밋되지 않은 파일

`AGENTS.md`와 `CLAUDE.md`가 untracked 상태다. 커밋할지 사용자에게 확인이 필요하다. 이 `HANDOFF.md`도 마찬가지다.

### 2-3. 미해결 보안 사항

**배포용 SSH private key가 원본 팀 저장소 히스토리에 공개된 상태다.**

이 문서는 공개 저장소에 있으므로 파일 경로, 키 지문, 대상 호스트, 커밋 해시 등 식별자를 여기에 적지 않는다. 구체적인 값은 사용자에게 문의한다.

`vysryoo/LiveNote`에서는 해당 키를 담은 브랜치 두 개(`master`, `feat/back_merge01`)를 삭제했다. 다만 원본 `Team-GongGong-s/LiveNote_frontend`가 public이고 거기에 그대로 남아 있으며, 포크 네트워크는 git 객체를 공유하므로 커밋 해시 직접 URL로도 접근 가능하다. 즉 저장소 측 정리는 노출 차단이 아니라 확산 축소 수준이다.

실제 폐기는 인프라 소유자만 가능하며 **아직 수행되지 않았다.** 필요한 조치는 다음과 같다.

1. 대상 서버의 `~/.ssh/authorized_keys`에서 해당 공개키 제거
2. EC2 콘솔에서 key pair 삭제 및 재발급
3. `/var/log/auth.log`로 비인가 접속 흔적 확인

인스턴스가 이미 종료됐다면 위 조치는 불필요하다. 원본 저장소도 2025-12-12 이후 활동이 없어 그럴 가능성이 있으나 **확인되지 않았다.** 인스턴스 상태 확인이 순서상 먼저다.

과거 커밋에 하드코딩된 DB 비밀번호와 JWT secret도 남아 있다. 둘 다 개발용 기본값으로 보이나 운영 환경에서 재사용했는지는 확인이 필요하다. 현재 `backend/src/main/resources/application.yml`은 전부 환경변수 참조로 정리돼 있다.

---

## 3. 프론트엔드 현황 (측정값)

모든 수치는 `cad395f` 시점에 실제 실행해 얻은 것이다.

| 검증 | 결과 |
| --- | --- |
| `npm run typecheck` | 통과 |
| `npm run build` | 성공 (6.71s) |
| `npm run lint` | **에러 0, 경고 171** |

번들은 단일 청크 590 kB (gzip 180 kB)이고 `ctaBackground.png`가 1.25 MB 무압축이다.

### 린트 경고 내역

```
88  no-console                              (SessionPage 64, useRecording 13, App 10, MainPage 1)
26  @typescript-eslint/no-explicit-any      (서비스 계층이 19건으로 73%)
15  @typescript-eslint/no-unused-vars
15  react-hooks/set-state-in-effect
12  react-hooks/exhaustive-deps
 9  react-hooks/memo-dependencies
 4  react-refresh/only-export-components
 1  react-hooks/no-deriving-state-in-effects
```

`src/components/ui/**`는 `eslint.config.mjs:34`에서 제외돼 있어 전부 앱 코드에서 나온다.

### 주요 파일 크기

```
1713  src/components/SessionPage.tsx      (useState 23개, useEffect 18개)
 688  src/components/ui/sidebar.tsx
 593  src/components/LandingPage.tsx      (i18n 미사용, 전부 한국어 하드코딩)
 383  src/hooks/useRecording.ts
 346  src/services/adapters/spring.ts
 345  src/App.tsx
 338  src/i18n/I18nContext.tsx            (262줄이 사전 데이터)
 299  src/services/adapters/supabase.ts   (@ts-nocheck, 죽은 어댑터)
 293  src/services/ports.ts
```

### 이전 단계에서 완료된 작업

모노레포 통합(`2c59867`, 2026-08-30) 이후 11커밋으로 빌드 기반을 정비함. Figma Make 스캐폴딩 잔재 정리, TypeScript strict 도입, ESLint 9 + Prettier 도입, Tailwind v4 빌드 파이프라인 복구(`index.css` 3496줄 → `styles/globals.css` 345줄), React 19 업그레이드, React Compiler 도입.

`eslint.config.mjs:9`와 `supabase.ts:1`에 "Phase 3", "Phase 4"라는 언급이 있으나 전체 정의 문서는 존재하지 않는다. 위 11커밋이 그에 해당한다고 **추정**할 뿐이다.

---

## 4. 조사로 확인된 문제

이 항목들은 코드를 읽어 확인한 것이다. 재작성에서 반드시 해소돼야 한다.

### 4-1. 버그 3개

1. **STOMP 클로저 고정** — `SessionPage.tsx:592`의 구독 이펙트 deps가 `[lectureId]`뿐이라 `handleStreamingMessage`가 마운트 시점 클로저로 고정됨. 그때 `selectedSectionIndex`는 `null`이므로 `:511`/`:524`의 폴백 `selectedSectionIndex || 0`이 **항상 0**이 됨.
2. **순수하지 않은 상태 갱신** — `setStreamingCards` updater 내부(`:449-580`)에서 `appendQnAForSection`(`:513`), `appendResourcesForSection`(`:526`), `setTimeout`(`:487`)을 호출함. StrictMode 이중 호출 시 중복 append 발생 구조.
3. **도달 불가 코드** — `:531-541`의 resource 제목 표시 로직이 `:546`의 무조건 `newMap.delete(cardId)` 때문에 실행되지 않음.

셋 다 수동 조작으로는 발견하기 어렵다. 1번은 2번째 이후 섹션에서만, 2번은 개발 모드에서만 나타나고, 3번은 애초에 실행되지 않는다.

### 4-2. 구조적 문제

- **섹션 인덱스의 주인이 셋** — STOMP `/section` → `SessionPage` 상태 → props → `useRecording`에서 `floor(elapsed/30)`과 `Math.min` 비교 → 반환 → 이펙트 `:1189`가 보정. 왕복 구조.
- **전사 텍스트가 세 벌** — `transcription`(현재 섹션), `liveSectionTranscripts`(실시간 누적), `transcripts`(DB 저장본). 이펙트 3개(`:1119`, `:1154`, `:1189`)가 서로 동기화.
- **분리된 컴포넌트가 미연결** — `LecturePane.tsx`와 `SplitPane.tsx`(327줄)가 import만 되고 JSX에서 미사용. 동일 UI가 `SessionPage.tsx:1368-1413`, `:1416-1684`에 인라인 중복(약 315줄).
- **전체 재조회** — `App.tsx`에서 변경마다 `fetchLectures()` 호출이 5곳(`:99, 153, 177, 201, 217`). 리렌더를 막으려 `SessionPage.tsx:255-319`에 수동 깊은 비교 65줄.
- **이중 에러 표시** — App 핸들러가 `toast.error` 후 재-throw하고, 모달이 그것을 잡아 인라인 에러 박스에도 렌더. 로그인 실패 시 토스트와 빨간 박스가 동시에 뜸.
- **i18n 커버리지** — 63키만 번역됨. `LandingPage.tsx` 593줄, 폼 검증 메시지 5개 파일, 토스트 10곳이 한국어 하드코딩. 보간 API가 없어 `MainPage.tsx:134-148`이 `switch (language)`로 우회.
- **`supabase.ts` 299줄** — `@ts-nocheck`로 타입 검사가 꺼진 죽은 어댑터. `VITE_BACKEND_TYPE=supabase`일 때만 쓰이나 사용처 없음.

### 4-3. 기타

- **폰트 파일 전부 누락** — `globals.css:308-330`이 `/fonts/Paperlogy-*.woff2`를 참조하나 `public/`에는 `favicon.png`, `preview.jpg`뿐. `public/fonts/` 폴더 자체가 없음. **현재 화면은 대체 폰트로 렌더되는 중이다.**
- **`frontend/README.md` 낡음** — `542b8e3`에서 삭제된 `index.css`를 파일 구조에 기재.

### 4-4. 언어 필드 구분 (중요)

언어가 두 종류이며 **혼동하면 안 된다.**

| 필드 | 위치 | 용도 |
| --- | --- | --- |
| `uiLanguage` | `User`, `UserView` (`ports.ts:7,15`) | 화면 표시 언어 |
| `sttLanguage` | `Lecture`, `CreateLectureRequest` (`ports.ts:57,68`) | 강의별 음성 인식 언어. 백엔드와 AI 서버가 사용 |

`NewLectureModal.tsx:23`이 강의 `sttLanguage`의 기본값을 UI 언어에서 가져온다. 이 동작 유지 여부는 M4에서 판단한다.

---

## 5. 확정된 설계 결정

사용자와 문답으로 하나씩 확정한 것이다. 재론하지 말고 전제로 삼는다.

| 항목 | 결정 | 근거 |
| --- | --- | --- |
| 이행 방식 | 완전 재작성 | 기존 구조를 물려받지 않고 설계부터 다시 세움 |
| 재사용 자산 | shadcn/ui 48개, Tailwind v4 + `globals.css`, 빌드·린트 설정 일체, 화면 디자인·UX | 직전 11커밋으로 정비된 자산 |
| 라우팅 | React Router | URL이 화면을 반영하지 않아 뒤로가기·새로고침·링크 공유 불가 |
| 서버 상태 | TanStack Query | 전체 재조회 5곳, 수동 깊은 비교 65줄, 로딩/에러 쌍 9곳 대체 |
| 폼 | react-hook-form + zod | 폼 5개가 동일 구조 복붙. rhf는 이미 설치됨 |
| 전역 상태 라이브러리 | **도입하지 않음** | prop drilling 최대 3단계, 전역 상태로 보이는 것이 모두 서버 상태 |
| 디렉터리 구조 | 기능 중심 | 관련 파일이 세 폴더에 흩어지는 문제 해결 |
| 세션 데이터 주인 | Query + reducer 분리 | 기준: **새로고침하면 서버에서 다시 받을 수 있는가** |
| API 계층 | 기능별 API 모듈 | 포트 추상화 비용만 치르고 이득 없음. zod로 응답 런타임 검증 |
| 테스트 | Vitest, reducer·유틸 단위만 | 컴포넌트 테스트와 E2E는 하지 않음 |
| i18n | i18next + react-i18next, **UI 전체 번역** | 보간·복수형·지연 로딩 내장 |
| 진행 순서 | 앱 셸 → 인증 → 강의 목록 → 세션 | 작은 화면에서 라이브러리를 익히고 세션을 마지막에 |
| 폰트 | Paperlogy 파일 확보해 `public/fonts/`에 추가 | 미확보 시 대체안으로 전환 (아래 미결 사항 참조) |

### 목표 디렉터리 구조

```
src/
├─ app/                    # 진입점, 라우터, 프로바이더
├─ features/
│  ├─ auth/                # 로그인·회원가입·설정
│  │  ├─ api/  components/  hooks/
│  ├─ lectures/            # 강의 목록·생성·삭제
│  │  ├─ api/  components/  hooks/
│  └─ session/             # 실시간 세션
│     ├─ api/  components/  hooks/
│     ├─ realtime/         # STOMP + 오디오 소켓
│     └─ state/            # 세션 reducer
├─ shared/
│  ├─ ui/                  # shadcn/ui 48개 (기존 components/ui 이동)
│  ├─ lib/
│  └─ i18n/
└─ main.tsx
```

### 실시간 데이터 경계

판별 기준은 한 문장이다 — **새로고침하면 서버에서 다시 받을 수 있는가.**

| 경로 | 저장소 |
| --- | --- |
| HTTP 초기 로드 (강의, 요약, 전사, 북마크, 자료, QnA) | Query 캐시 |
| STOMP `/summary` `/qna` `/resources` `/transcripts` | Query 캐시 (`setQueryData`) |
| STOMP `/section` | Query 캐시 — "현재 섹션"의 **유일한 쓰기 지점** |
| STOMP `/stream` (토큰 스트리밍) | 세션 reducer |
| 오디오 WebSocket `transcript` | 세션 reducer |
| 스트리밍 카드 완성 시 | reducer에서 제거 → Query 캐시로 이동 (명시적 단계) |

---

## 6. 구현 설계

### 6-1. 재작성 중 구 코드를 두는 곳

완전 재작성이지만 저장소는 매 커밋 빌드 가능한 상태로 유지한다. 진행 순서가 "쉬운 화면부터"라 각 단계에서 앱을 띄워 확인해야 하기 때문이다.

구 코드를 **한 번에 `src/legacy/`로 옮긴다.** 새 구조는 `src/app`, `src/features`, `src/shared`에 짓고, 기능 하나를 재작성할 때마다 대응하는 `legacy/` 파일을 삭제한다. `legacy/`에 남은 것이 곧 남은 작업량이다.

`legacy/`는 `eslint.config.mjs`의 `ignores`에 추가해 새 코드만 규칙을 적용한다. 마지막 단계에서 폴더가 비면 제거한다.

### 6-2. 세션 reducer

reducer는 **전송 중이라 서버에 완성본이 없는 것만** 담는다.

```ts
type StreamingCard = {
  cardId: string;
  kind: "qna" | "resource";
  sectionIndex: number;        // 메시지가 직접 알려준 값만 사용
  content: string;
  title?: string;
  resourceType?: string;
  status: "streaming" | "failed";
  errorMessage?: string;
};

type SessionState = {
  streamingCards: Record<string, StreamingCard>;
  liveTranscripts: Record<number, string>;   // sectionIndex → 녹음 중 누적 텍스트
};
```

액션 목록.

| 액션 | 발생원 |
| --- | --- |
| `LIVE_TRANSCRIPT_RECEIVED { sectionIndex, content, isFinal }` | 오디오 WebSocket |
| `STREAM_TOKEN { cardId, token, title?, resourceType? }` | STOMP `/stream` |
| `STREAM_COMPLETED { cardId }` | STOMP `/stream` — 카드 제거만 수행 |
| `STREAM_FAILED { cardId, error }` | STOMP `/stream` |
| `STREAM_ERROR_DISMISSED { cardId }` | 화면의 타이머 |
| `SECTION_TRANSCRIPT_PERSISTED { sectionIndex }` | 해당 섹션 전사가 DB에 저장됨 |
| `SESSION_RESET` | `lectureId` 변경 |

**기존 문제가 해소되는 방식.**

섹션 인덱스는 reducer에 두지 않는다. Query 캐시의 `["lectures","detail",id,"currentSection"]` 하나에만 존재하고 쓰기 지점은 STOMP `/section` 핸들러 단 하나다. 녹음 훅은 읽기만 하고 `floor(elapsed/30)`로 계산하지 않는다.

전사는 셋 중 둘만 상태로 남긴다.

| 기존 | 새 위치 |
| --- | --- |
| `transcripts` (DB 저장본) | Query 캐시 |
| `liveSectionTranscripts` (녹음 중 누적) | reducer |
| `transcription` (현재 섹션 표시용) | **상태 아님. 렌더 시 파생** |

`transcription`은 `liveTranscripts[current] ?? dbTranscripts[current]`로 계산한다. 이것만으로 `set-state-in-effect` 경고가 나던 이펙트 3개가 사라진다.

`STREAM_COMPLETED`는 reducer에서 카드를 지우기만 한다. Query 캐시로 옮기는 일은 호출부가 reducer 바깥에서 수행한다. reducer 안에서 `setTimeout`이나 다른 상태 갱신 함수를 부르지 않는다.

### 6-3. STOMP 구독 계층

```
features/session/realtime/
├─ messages.ts         # 토픽별 zod 스키마 6종
├─ handlers.ts         # 순수 핸들러 — (queryClient, dispatch, lectureId)만 인자로 받음
├─ stompClient.ts      # 연결 생성·해제
└─ useSessionStream.ts # 구독 수명주기 훅
```

**클로저 고정 문제를 deps 수정이 아니라 구조로 막는다.** 원인은 핸들러가 변하는 UI 상태를 클로저로 잡은 것이다. deps에 넣으면 메시지마다 재구독이 일어나고, 안 넣으면 값이 굳는다. 두 가지를 지킨다.

1. 핸들러는 `queryClient`와 `dispatch`만 쓴다. 둘 다 참조가 안정적이라 deps `[lectureId]`로 충분하고 stale이 생기지 않는다.
2. 메시지의 `sectionIndex`를 zod 스키마에서 **필수 필드로 강제**한다. 현재처럼 `cardId` 문자열을 파싱하거나 UI 상태로 폴백하지 않는다.

핸들러를 모듈 최상위 순수 함수로 두면 컴포넌트 생명주기와 무관해져 단위 테스트도 가능하다.

기존 STOMP 구독은 `SessionPage.tsx:592-816`에 225줄로 있고 6개 토픽을 구독한다. `brokerURL`은 `${VITE_WS_URL||ws://localhost:8080}/ws`다.

### 6-4. Query 키 설계

목록과 상세를 분리한다. `["lectures", id]` 형태면 `["lectures"]` 무효화 시 열려 있는 세션의 상세까지 날아간다.

```
["auth", "me"]
["lectures", "list"]
["lectures", "detail", lectureId]
["lectures", "detail", lectureId, "summaries"]
["lectures", "detail", lectureId, "transcripts"]
["lectures", "detail", lectureId, "resources"]
["lectures", "detail", lectureId, "qna"]
["lectures", "detail", lectureId, "bookmarks"]
["lectures", "detail", lectureId, "currentSection"]
```

| 작업 | 무효화 범위 |
| --- | --- |
| 강의 생성·삭제 | `["lectures","list"]` |
| 강의 제목 변경 | `["lectures","list"]` + `["lectures","detail",id]` |
| 세션 종료 | `["lectures","list"]` + `["lectures","detail",id]` |
| 로그아웃 | 캐시 전체 `clear()` |

STOMP로 들어오는 갱신은 무효화가 아니라 `setQueryData`로 캐시에 직접 쓴다. 재조회를 유발하지 않는다.

### 6-5. 오디오 녹음 훅 경계

```ts
useAudioRecording({ lectureId, onTranscript })
  → { isRecording, isAudioActive, start, stop }
```

**훅 안**: AudioContext(24kHz), 리샘플링, Float32→PCM16 변환, `getUserMedia`, WebSocket 연결·재연결·정리, 무음 감지.

**훅 밖**: 전사 텍스트 병합. 현재 `SessionPage.tsx:105-131`에 있는 "isFinal이면 줄 추가, 아니면 마지막 줄 교체" 알고리즘을 reducer의 `LIVE_TRANSCRIPT_RECEIVED`로 옮긴다. 순수 함수가 되어 테스트 대상이 된다.

**제거 대상.**

| 대상 | 이유 |
| --- | --- |
| `mediaRecorderRef` (`useRecording.ts:45`) | 대입되는 곳이 없는 죽은 코드 |
| `wsRef` (`SessionPage.tsx:55`) | 선언만 되고 미사용 |
| `elapsedTimeRef`, `currentSectionIndexRef` 복제 | 훅과 컴포넌트 양쪽에 존재하며 각자 이펙트로 동기화 |
| `hasRecordingStarted` 이중 관리 | 훅 반환값이 쓰이지 않고 콜백으로 별도 관리 중 |
| `RecordingTabControl`의 자체 1초 타이머 (`:20-33`) | 훅 타이머와 이중이며 무음 시 멈추지 않음 |

`isAudioActive`는 반환해서 화면이 무음 상태를 표시할 수 있게 한다. 현재는 내부에서 타이머만 멈추고 사용자는 알 수 없다.

경과 시간과 현재 섹션은 훅이 계산하지 않는다. 서버가 STOMP로 보낸 값을 Query에서 읽는다.

### 6-6. 라우트와 코드 스플리팅

```
/                  LandingPage     eager  — 첫 화면
/signup            SignupPage      lazy
/lectures          MainPage        lazy   — 인증 필요
/lectures/:id      SessionPage     lazy   — 인증 필요, 가장 큼
/settings          SettingsPage    lazy   — 인증 필요
```

인증 가드는 `["auth","me"]` 쿼리로 판정하는 래퍼 라우트로 둔다. 현재 `App.tsx:261-270`의 `initializing` 게이트를 대체한다.

`SessionPage`가 `@stomp/stompjs`와 오디오 파이프라인을 끌고 오므로 lazy 분리 효과가 가장 크다.

---

## 7. 구현 마일스톤

각 마일스톤은 커밋 하나 크기다.

### M1 · 기반 정비

- 의존성 추가: `react-router`, `@tanstack/react-query`, `zod`, `i18next`, `react-i18next`, `vitest`
- `vite.config.ts`에 Vitest 설정, `package.json`에 `test` 스크립트
- 구 코드를 `src/legacy/`로 이동, `eslint.config.mjs`의 `ignores`에 추가
- `components/ui` 48개를 `src/shared/ui`로 이동
- `public/fonts/`에 Paperlogy 파일 추가
- **완료 기준**: 앱이 이전과 동일하게 동작하고 폰트가 제대로 로드됨

### M2 · 앱 셸

- `src/app/`에 라우터, `QueryClientProvider`, i18next 프로바이더 구성
- 라우트 5개 정의, 인증 가드 래퍼, lazy 경계
- `shared/lib/http.ts` — 공용 fetch 래퍼 (현재 `spring.ts:39-97`의 4가지 응답 분기를 정리)
- `shared/i18n/` — i18next 설정과 `locales/{ko,en,ja,zh}.json` (기존 63키 이관, 코드 기반 키로 전환)
- **완료 기준**: URL이 화면을 반영하고 뒤로가기·새로고침이 동작. 화면 내용은 아직 `legacy/` 컴포넌트

### M3 · 인증

- `features/auth/` — `api/`(zod 스키마 + 호출), `hooks/useMe`, `components/`
- rhf + zod로 폼 3개 재작성, 검증 메시지를 번역 키로
- 이중 에러 표시 제거 — 토스트와 인라인 중 하나로 통일
- `legacy/`에서 대응 파일 삭제
- **완료 기준**: 로그인·회원가입·설정이 새 구조로 동작

### M4 · 강의 목록

- `features/lectures/` — Query 키 계층 적용, mutation과 invalidate
- 전체 재조회 5곳 제거, 클라이언트 `userId` 필터 재검토
- rhf + zod로 신규 강의 모달 재작성 (`sttLanguage` 기본값 결정)
- **완료 기준**: 목록 화면이 새 구조로 동작하고 변경 시 목록만 갱신

### M5 · 세션 reducer와 실시간 계층

- `features/session/state/` — reducer, 액션, 단위 테스트
- `features/session/realtime/` — zod 메시지 스키마 6종, 순수 핸들러, `useSessionStream`
- `features/session/hooks/useAudioRecording` — 경계 정리
- 이 시점에 화면은 붙이지 않는다
- **완료 기준**: reducer 테스트 통과, 구독 계층이 독립적으로 존재

### M6 · 세션 화면

- `features/session/components/` — `LecturePane`, `SplitPane`, `SectionCard`, 스트리밍 카드를 실제로 연결 (인라인 중복 315줄 제거)
- 요약 선택·분할 패널·오토모드·북마크를 기능별 훅으로
- `legacy/SessionPage.tsx` 삭제
- **완료 기준**: 세션 화면 전체가 새 구조로 동작

### M7 · 마무리

- `legacy/` 폴더 제거, `supabase.ts`·`ports.ts` 삭제
- UI 전체 번역 적용 (랜딩 593줄, 토스트, 남은 하드코딩)
- `eslint.config.mjs`의 React Compiler 규칙 18종을 `warn` → `error`로 승격
- `frontend/README.md` 갱신, `ctaBackground.png` 최적화
- **완료 기준**: 린트 경고 0에 근접, 번들이 화면별로 분할됨

---

## 8. 검증 방법

각 마일스톤 끝에서 다음을 통과해야 한다.

```bash
cd frontend
npm run typecheck     # tsc --noEmit (strict)
npm run lint          # eslint . — 에러 0 유지
npm run build         # vite build
npm test              # vitest run (M5 이후)
```

세션 단계는 자동 검증만으로 부족하다. Spring 백엔드와 AI 서버를 띄우고 `npm run dev`로 다음 흐름을 직접 확인한다.

로그인 → 강의 생성 → 녹음 시작 → 전사가 실시간으로 쌓이는지 → 섹션 전환 시 전사가 초기화되는지 → 요약 카드 도착 → 요약 클릭 시 분할 패널이 열리고 QnA·자료 스트리밍 카드가 채워지는지 → 북마크 토글 → 세션 종료.

**버그 1번(섹션 인덱스가 항상 0)은 2번째 이후 섹션에서 요약을 클릭해야 재현된다.** 최소 60초 이상 녹음해 섹션을 2개 이상 만든 뒤 확인한다.

실행 전 `frontend/.env`가 필요하다.

```
VITE_API_URL=http://localhost:8080
VITE_WS_URL=ws://localhost:8080
```

---

## 9. 위험 요소

| 위험 | 대응 |
| --- | --- |
| STOMP 메시지 실제 형태가 zod 스키마와 안 맞을 수 있음 | M5에서 처음엔 관대한 스키마로 시작해 실제 메시지를 로깅하고, 확인된 뒤 조인다 |
| 세션 단계 검증에 백엔드와 AI 서버 필요 | M5까지는 reducer 테스트로 대체 가능. M6부터 실제 서버 필요 |
| Paperlogy 폰트 파일 확보 여부 미확정 | 확보 불가 시 웹폰트 CDN 또는 시스템 폰트로 대체 |
| M6가 가장 크고 되돌리기 어려움 | `legacy/SessionPage.tsx` 삭제를 M6 마지막 커밋으로 분리해, 문제 시 라우트만 되돌려 구 화면으로 복귀 |
| 번역 키가 63개에서 크게 늘어남 | M7에 몰지 말고 M3·M4에서 해당 화면 키를 그때그때 추가 |

---

## 10. 미결 사항

작업 재개 시 사용자에게 먼저 확인할 것.

1. **Paperlogy 폰트 파일을 보유하고 있는가.** 원본 팀 저장소에도 `public/fonts/`가 없어 프로젝트 안에서는 구할 수 없다. 미보유 시 웹폰트 CDN(Pretendard 등) 또는 시스템 폰트로 계획을 바꿔야 한다.
2. **`AGENTS.md`, `CLAUDE.md`, `HANDOFF.md`를 커밋할 것인가.** 현재 untracked 상태다.
3. **노출된 배포 키 폐기 진행 여부.** 2-3절 참조. 인프라 소유자만 수행 가능하며 구체적 식별자는 사용자에게 문의한다.
4. **`NewLectureModal`의 `sttLanguage` 기본값을 UI 언어에서 가져오는 동작을 유지할 것인가.** M4에서 결정한다.

---

## 11. 사용자 응대 시 참고

사용자는 프론트엔드 라이브러리와 아키텍처 패턴에 대한 사전 지식이 거의 없다. 본인이 "아예 모름"이라고 밝혔고, 선택지를 제시할 때마다 설명을 요청했다.

따라서 새로운 라이브러리나 패턴을 선택지로 제시할 때는 이름과 한 줄 요약만 던지지 말고 **먼저 설명한 뒤에 고르게 한다.** 설명은 일반론이 아니라 이 저장소의 실제 코드를 근거로 한다. 지금 코드의 어느 파일 몇 번째 줄이 어떤 문제를 겪는지 인용하고, 적용하면 어떻게 바뀌는지 짧은 코드 예시로 보여주고, 학습 비용과 단점을 함께 적는다.

설계 문답은 한 번에 하나씩 진행했다. 사용자가 그렇게 요청했다.
