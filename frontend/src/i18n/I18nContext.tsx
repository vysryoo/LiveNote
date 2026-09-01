import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

export type SupportedLanguage = "한국어" | "English" | "日本語" | "汉语";
export type LanguageCode = "ko" | "en" | "ja" | "zh";

type Dictionary = Record<string, string>;

// 언어 표시명과 DB 코드 간 변환 함수
export function languageToCode(lang: SupportedLanguage): LanguageCode {
  const map: Record<SupportedLanguage, LanguageCode> = {
    한국어: "ko",
    English: "en",
    日本語: "ja",
    汉语: "zh",
  };
  return map[lang] || "ko";
}

export function codeToLanguage(code: string): SupportedLanguage {
  const map: Record<string, SupportedLanguage> = {
    ko: "한국어",
    en: "English",
    ja: "日本語",
    zh: "汉语",
  };
  return map[code] || "한국어";
}

const dictionaries: Record<SupportedLanguage, Dictionary> = {
  한국어: {
    "common.settings": "설정",
    "common.logout": "로그아웃",
    "common.edit": "수정",
    "common.delete": "삭제",
    "common.cancel": "취소",
    "common.save": "저장",
    "common.saveAndEnd": "저장하고 종료",
    "common.language": "언어",
    "main.myLectures": "내 강의",
    "main.startNewLecture": "새 강의 시작하기",
    "main.noLecturesTitle": "아직 강의가 없습니다",
    "main.noLecturesDesc": "새 강의를 시작하여 LiveNote를 경험해보세요",
    "login.title": "로그인",
    "login.desc": "아이디와 비밀번호를 입력하여 로그인하세요.",
    "login.username": "아이디",
    "login.password": "비밀번호",
    "login.login": "로그인",
    "login.signupLink": "회원 가입",
    "signup.title": "회원가입",
    "signup.username": "아이디",
    "signup.password": "비밀번호",
    "signup.passwordConfirm": "비밀번호 확인",
    "signup.name": "이름",
    "signup.email": "이메일",
    "signup.submit": "가입 완료",
    "settings.title": "설정",
    "settings.changePassword": "비밀번호 변경",
    "settings.currentPassword": "현재 비밀번호",
    "settings.newPassword": "새 비밀번호",
    "settings.confirmPassword": "비밀번호 확인",
    "settings.currentPasswordPH": "현재 비밀번호를 입력하세요",
    "settings.newPasswordPH": "새 비밀번호를 입력하세요",
    "settings.confirmPasswordPH": "비밀번호를 다시 입력하세요",
    "settings.save": "수정",
    "settings.back": "돌아가기",
    "session.header.record": "강의 기록",
    "session.header.summary": "실시간 요약",
    "session.resources": "자료 탐색",
    "session.ai": "AI 질문",
    "session.fetchError": "강의 정보를 불러오지 못했습니다",
    "session.loading": "강의 데이터를 불러오는 중입니다...",
    "session.noSummaries": "아직 요약 데이터가 없습니다.",
    "session.noTranscript": "전사 데이터가 없습니다.",
    "session.noSummaryText": "요약 데이터가 없습니다.",
    "session.bookmarkAdded": "북마크가 추가되었습니다",
    "session.bookmarkRemoved": "북마크가 제거되었습니다",
    "session.bookmarkFailed": "북마크 처리에 실패했습니다",
    "session.wsError": "녹음 연결 중 오류가 발생했습니다",
    "session.recordingError": "녹음을 시작할 수 없습니다",
    "session.micPermissionDenied": "마이크 권한이 필요합니다",
    "endSession.title": "강의 세션 종료",
    "endSession.desc": "강의를 저장하고 종료합니다. 강의 이름을 입력하세요.",
    "endSession.inputLabel": "저장할 강의 이름",
    "newLecture.title": "새 강의 설정",
    "newLecture.desc": "새로운 강의를 시작하기 위한 정보를 입력하세요.",
    "newLecture.category": "분류",
    "newLecture.categoryPH": "분류를 선택하세요",
    "newLecture.subject": "과목명",
    "newLecture.subjectPH": "과목명을 입력하세요",
    "newLecture.filesOptional": "참고 자료 (선택)",
    "newLecture.clickToAddFiles": "클릭하여 파일 추가",
    "newLecture.supportedTypes": "PDF, DOC, TXT, PPT 지원",
    "newLecture.addedFiles": "추가된 파일",
  },
  English: {
    "common.settings": "Settings",
    "common.logout": "Log out",
    "common.edit": "Edit",
    "common.delete": "Delete",
    "common.cancel": "Cancel",
    "common.save": "Save",
    "common.saveAndEnd": "Save and End",
    "common.language": "Language",
    "main.myLectures": "My Lectures",
    "main.startNewLecture": "Start New Lecture",
    "main.noLecturesTitle": "No lectures yet",
    "main.noLecturesDesc": "Start a new lecture to experience LiveNote",
    "login.title": "Login",
    "login.desc": "Enter your ID and password to sign in.",
    "login.username": "ID",
    "login.password": "Password",
    "login.login": "Login",
    "login.signupLink": "Sign up",
    "signup.title": "Sign Up",
    "signup.username": "ID",
    "signup.password": "Password",
    "signup.passwordConfirm": "Confirm Password",
    "signup.name": "Name",
    "signup.email": "Email",
    "signup.submit": "Create account",
    "settings.title": "Settings",
    "settings.changePassword": "Change Password",
    "settings.currentPassword": "Current Password",
    "settings.newPassword": "New Password",
    "settings.confirmPassword": "Confirm Password",
    "settings.currentPasswordPH": "Enter current password",
    "settings.newPasswordPH": "Enter new password",
    "settings.confirmPasswordPH": "Re-enter password",
    "settings.save": "Save",
    "settings.back": "Back",
    "session.header.record": "Lecture Record",
    "session.header.summary": "Live Summary",
    "session.resources": "Resources",
    "session.ai": "AI Q&A",
    "session.fetchError": "Failed to load lecture information",
    "session.loading": "Loading lecture data...",
    "session.noSummaries": "No summary data yet.",
    "session.noTranscript": "No transcript available.",
    "session.noSummaryText": "No summary available.",
    "session.bookmarkAdded": "Bookmark added",
    "session.bookmarkRemoved": "Bookmark removed",
    "session.bookmarkFailed": "Failed to process bookmark",
    "session.wsError": "An error occurred while connecting for recording",
    "session.recordingError": "Failed to start recording",
    "session.micPermissionDenied": "Microphone permission is required",
    "endSession.title": "End Session",
    "endSession.desc": "Save and end the lecture. Enter a name.",
    "endSession.inputLabel": "Lecture name to save",
    "newLecture.title": "New Lecture Settings",
    "newLecture.desc": "Enter details to start a new lecture.",
    "newLecture.category": "Category",
    "newLecture.categoryPH": "Select a category",
    "newLecture.subject": "Subject",
    "newLecture.subjectPH": "Enter subject name",
    "newLecture.filesOptional": "Reference files (optional)",
    "newLecture.clickToAddFiles": "Click to add files",
    "newLecture.supportedTypes": "Supports PDF, DOC, TXT, PPT",
    "newLecture.addedFiles": "Added files",
  },
  日本語: {
    "common.settings": "設定",
    "common.logout": "ログアウト",
    "common.edit": "編集",
    "common.delete": "削除",
    "common.cancel": "キャンセル",
    "common.save": "保存",
    "common.saveAndEnd": "保存して終了",
    "common.language": "言語",
    "main.myLectures": "マイ講義",
    "main.startNewLecture": "新しい講義を開始",
    "main.noLecturesTitle": "講義はまだありません",
    "main.noLecturesDesc": "新しい講義を開始して LiveNote を体験しましょう",
    "login.title": "ログイン",
    "login.desc": "ID とパスワードを入力してください。",
    "login.username": "ID",
    "login.password": "パスワード",
    "login.login": "ログイン",
    "login.signupLink": "新規登録",
    "signup.title": "新規登録",
    "signup.username": "ID",
    "signup.password": "パスワード",
    "signup.passwordConfirm": "パスワード確認",
    "signup.name": "名前",
    "signup.email": "メール",
    "signup.submit": "登録",
    "settings.title": "設定",
    "settings.changePassword": "パスワード変更",
    "settings.currentPassword": "現在のパスワード",
    "settings.newPassword": "新しいパスワード",
    "settings.confirmPassword": "確認用パスワード",
    "settings.currentPasswordPH": "現在のパスワードを入力してください",
    "settings.newPasswordPH": "新しいパスワードを入力してください",
    "settings.confirmPasswordPH": "もう一度パスワードを入力してください",
    "settings.save": "保存",
    "settings.back": "戻る",
    "session.header.record": "講義記録",
    "session.header.summary": "ライブ要約",
    "session.resources": "資料",
    "session.ai": "AI 質問",
    "session.fetchError": "講義情報の読み込みに失敗しました",
    "session.loading": "講義データを読み込んでいます...",
    "session.noSummaries": "要約データはまだありません。",
    "session.noTranscript": "書き起こしデータがありません。",
    "session.noSummaryText": "要約はありません。",
    "session.bookmarkAdded": "ブックマークを追加しました",
    "session.bookmarkRemoved": "ブックマークを削除しました",
    "session.bookmarkFailed": "ブックマーク処理に失敗しました",
    "session.wsError": "録音用の接続でエラーが発生しました",
    "session.recordingError": "録音を開始できませんでした",
    "session.micPermissionDenied": "マイクの権限が必要です",
    "endSession.title": "セッション終了",
    "endSession.desc": "保存して終了します。名前を入力してください。",
    "endSession.inputLabel": "保存する講義名",
    "newLecture.title": "新しい講義の設定",
    "newLecture.desc": "新しい講義を開始するための情報を入力してください。",
    "newLecture.category": "分類",
    "newLecture.categoryPH": "分類を選択してください",
    "newLecture.subject": "科目名",
    "newLecture.subjectPH": "科目名を入力してください",
    "newLecture.filesOptional": "参考資料（任意）",
    "newLecture.clickToAddFiles": "クリックしてファイルを追加",
    "newLecture.supportedTypes": "PDF、DOC、TXT、PPT 対応",
    "newLecture.addedFiles": "追加されたファイル",
  },
  汉语: {
    "common.settings": "设置",
    "common.logout": "登出",
    "common.edit": "编辑",
    "common.delete": "删除",
    "common.cancel": "取消",
    "common.save": "保存",
    "common.saveAndEnd": "保存并结束",
    "common.language": "语言",
    "main.myLectures": "我的课程",
    "main.startNewLecture": "开始新课程",
    "main.noLecturesTitle": "暂无课程",
    "main.noLecturesDesc": "开始新课程体验 LiveNote",
    "login.title": "登录",
    "login.desc": "请输入账号和密码登录。",
    "login.username": "账号",
    "login.password": "密码",
    "login.login": "登录",
    "login.signupLink": "注册",
    "signup.title": "注册",
    "signup.username": "账号",
    "signup.password": "密码",
    "signup.passwordConfirm": "确认密码",
    "signup.name": "姓名",
    "signup.email": "邮箱",
    "signup.submit": "完成注册",
    "settings.title": "设置",
    "settings.changePassword": "修改密码",
    "settings.currentPassword": "当前密码",
    "settings.newPassword": "新密码",
    "settings.confirmPassword": "确认密码",
    "settings.currentPasswordPH": "请输入当前密码",
    "settings.newPasswordPH": "请输入新密码",
    "settings.confirmPasswordPH": "请再次输入密码",
    "settings.save": "保存",
    "settings.back": "返回",
    "session.header.record": "课程记录",
    "session.header.summary": "实时摘要",
    "session.resources": "资料检索",
    "session.ai": "AI 提问",
    "session.fetchError": "无法加载课程信息",
    "session.loading": "正在加载课程数据...",
    "session.noSummaries": "暂时没有摘要数据。",
    "session.noTranscript": "暂无转写数据。",
    "session.noSummaryText": "暂无摘要。",
    "session.bookmarkAdded": "已添加书签",
    "session.bookmarkRemoved": "已移除书签",
    "session.bookmarkFailed": "书签处理失败",
    "session.wsError": "录音连接时发生错误",
    "session.recordingError": "无法开始录音",
    "session.micPermissionDenied": "需要麦克风权限",
    "endSession.title": "结束会话",
    "endSession.desc": "保存并结束课程。请输入名称。",
    "endSession.inputLabel": "保存的课程名称",
    "newLecture.title": "新课程设置",
    "newLecture.desc": "请输入信息以开始新课程。",
    "newLecture.category": "分类",
    "newLecture.categoryPH": "请选择分类",
    "newLecture.subject": "科目名",
    "newLecture.subjectPH": "请输入科目名称",
    "newLecture.filesOptional": "参考资料（可选）",
    "newLecture.clickToAddFiles": "点击添加文件",
    "newLecture.supportedTypes": "支持 PDF、DOC、TXT、PPT",
    "newLecture.addedFiles": "已添加文件",
  },
};

type I18nContextValue = {
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  t: (key: string) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({
  children,
  initialLanguage,
}: {
  children: any;
  initialLanguage?: SupportedLanguage;
}) {
  const [language, setLanguageState] = useState<SupportedLanguage>(initialLanguage ?? "한국어");

  useEffect(() => {
    if (initialLanguage) setLanguageState(initialLanguage);
  }, [initialLanguage]);

  const setLanguage = useCallback((lang: SupportedLanguage) => {
    setLanguageState(lang);
    try {
      localStorage.setItem("uiLanguage", lang);
    } catch {
      // 프라이빗 모드 등 localStorage 접근 불가 환경 무시
    }
  }, []);

  const t = useCallback(
    (key: string) => {
      const dict = dictionaries[language] || dictionaries["한국어"];
      return dict[key] ?? key;
    },
    [language],
  );

  const value = useMemo(() => ({ language, setLanguage, t }), [language, setLanguage, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
