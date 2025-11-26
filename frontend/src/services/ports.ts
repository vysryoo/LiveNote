 


export interface User {
  id: number;
  loginId: string; 
  password: string;
  email: string;
  name: string;
  uiLanguage: string;
}

export interface UserView {
  id: number;
  loginId: string;
  email: string;
  name: string;
  uiLanguage: string;
}

export interface AuthResponse {
  token: string;
  user: {
    id: number;
    loginId: string;
    name: string;
    email: string;
    uiLanguage?: string;
  };
}

export interface LoginRequest {
  loginId: string;
  password: string;
}

export interface SignupRequest {
  loginId: string;
  password: string;
  email: string;
  name: string;
}


 

export interface AuthPort {
  /** 로그인 */
  login(data: LoginRequest): Promise<AuthResponse>;

  /** 회원가입 */
  signup(data: SignupRequest): Promise<AuthResponse>;

  /** 로그아웃 */
  logout(): Promise<void>;
}

 


export interface Lecture {
  id: number;
  userId: number;
  title: string;
  subject: string;
  sttLanguage: string;
  status: 'recording' | 'completed';
  createdAt: string;
  endAt: string | null;
  duration: number | null;
  files?: File[];
}

export interface CreateLectureRequest {
  title: string;
  subject: string;
  sttLanguage: string;
  files?: File[];
}

export interface UpdateLectureTitleRequest {
  title: string;
}

export interface SessionDetailResponse extends Lecture {
  transcripts?: Transcript[];
  summaries?: Summary[];
  resources?: Resource[];
  qna?: QnA[];
  bookmarks?: Bookmark[];
}

export interface Bookmark {
  id: number;
  userId: number;
  lectureId: number;
  sectionIndex: number;
  targetType: 'resource' | 'qna';
  targetId: number;
}

export interface BookmarkRequest {
  lectureId: number;
  sectionIndex: number;
  targetType: 'resource' | 'qna';
  targetId: number;
}


export interface Transcript {
  id: number;
  lectureId: number;
  sectionIndex: number;
  startSec: number;
  endSec: number;
  text: string | string[];
}

export interface Summary {
  id?: number;
  lectureId: number;
  sectionIndex: number;
  startSec: number;
  endSec: number;
  text: string | string[];
}

export interface Resource {
  id: number;
  lectureId: number;
  sectionIndex: number;
  type: 'paper' | 'wiki' | 'video' | 'blog';
  title: string | string[];
  text: string | string[];
  url: string;
  thumbnail: string;
  score: number | null;
}

export interface QnA {
  id: number;
  lectureId: number;
  sectionIndex: number;
  type: 'concept' | 'application' | 'advanced' | 'comparison';
  question: string | string[];
  answer: string | string[];
}
// 개념확인 | 응용확장 | 심화질의 | 비교분서 

export interface WebSocketMessage {
  type: 'transcript' | 'summary' | 'resource' | 'qna' | 'error';
  data: {
    heading?: string | string[];
    content?: string | string[];
    timestamp?: number;
    isFinal?: boolean;
    error?: string;
  };
}

export interface LecturePort {
  /** 강의 목록 조회 */
  getLectures(): Promise<Lecture[]>;

  /** 강의 상세 조회 */
  getLecture(id: number): Promise<SessionDetailResponse>;

  /** 강의 생성 */
  createLecture(data: CreateLectureRequest): Promise<Lecture>;

  /** 강의 제목 수정 */
  updateLectureTitle(id: number, data: UpdateLectureTitleRequest): Promise<Lecture>;

  /** 강의 삭제 */
  deleteLecture(id: number): Promise<void>;

  /** 강의 종료 */
  endLecture(id: number, data?: UpdateLectureTitleRequest): Promise<Lecture>;


  /** 북마크 추가 */
  addBookmark(data: BookmarkRequest): Promise<Bookmark>;

  /** 북마크 목록 조회 (둘 다 필수) */
  getBookmarks(lectureId: number, sectionIndex: number): Promise<Bookmark[]>;

  /** 북마크 삭제 */
  deleteBookmark(bookmarkId: number): Promise<void>;

  /** 전사 조회 (sinceSection 이후) */
  getTranscripts(lectureId: number, sinceSection?: number): Promise<Transcript[]>;

  /** 요약 조회 (sinceSection 이후) */
  getSummaries(lectureId: number, sinceSection?: number): Promise<Summary[]>;

  /** 추천 자료 조회 (섹션 기준) */
  getResources(
    lectureId: number,
    sectionIndex: number,
    type?: 'paper' | 'wiki' | 'video' | 'blog'
  ): Promise<Resource[]>;

  /** Q&A 조회 (섹션 기준) */
  getQnA(
    lectureId: number,
    sectionIndex: number,
    type?: 'concept' | 'application' | 'advanced' | 'comparison'
  ): Promise<QnA[]>;

  /** 외부 콜백 처리 */
  aiCallback(payload: any): Promise<{ message: string }>;

  /** AI 요약 생성 */
  generateSummary(
    lectureId: number,
    sectionIndex: number,
    phase?: 'partial' | 'final'
  ): Promise<{ success: boolean; summary?: Summary; sectionIndex: number; error?: string }>;

  /** AI 질문 생성 */
  generateQnA(lectureId: number, sectionIndex: number): Promise<{ success: boolean; qna?: any[]; sectionIndex: number; error?: string }>;

  /** AI 자료 추천 생성 */
  generateResources(lectureId: number, sectionIndex: number): Promise<{ success: boolean; resources?: any[]; sectionIndex: number; error?: string }>;

  /** 전사 WebSocket 연결 생성 */
  connectTranscription(sessionId: string | number): WebSocket;

  /** WebSocket으로 오디오 데이터 전송 */
  sendAudioData(ws: WebSocket, audioData: ArrayBuffer): void;

  /** 카드 상태 조회 */
  getCardsStatus(
    lectureId: number,
    sectionIndex: number
  ): Promise<{
    qnaCards: Array<{
      cardId: string;
      cardIndex: number;
      type: string;
      isComplete: boolean;
      needsStreaming?: boolean;
      data?: QnA | Resource;
    }>;
    resourceCards: Array<{
      cardId: string;
      cardIndex: number;
      type: string;
      isComplete: boolean;
      needsStreaming?: boolean;
      data?: QnA | Resource;
    }>;
  }>;

  /** QnA 스트리밍 시작 */
  startQnAStream(
    lectureId: number,
    sectionIndex: number,
    cardIndex: number,
    qnaType?: string
  ): Promise<{ success: boolean; cardId: string; type: string }>;

  /** Resource 스트리밍 시작 */
  startResourceStream(
    lectureId: number,
    sectionIndex: number,
    cardIndex: number,
    resourceType?: string
  ): Promise<{ success: boolean; cardId: string; type: string }>;
}

 


export interface SetLanguageRequest {
  language: string;
}

export interface SetPasswordRequest {
  currentPassword: string;
  newPassword: string;
}


export interface SettingsPort {

  /** 현재 사용자 조회 */
  getUser(): Promise<UserView>;

  /** UI 표시 언어 변경 */
  setLanguage(data: SetLanguageRequest): Promise<UserView>;

  /** 비밀번호 변경 */
  setPassword(data: SetPasswordRequest): Promise<UserView>;


 
}

 
export interface BackendPort {
  auth: AuthPort;
  lecture: LecturePort;
  settings: SettingsPort;
}

