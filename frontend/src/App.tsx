import React, { useCallback, useEffect, useMemo, useState } from "react";
import { LandingPage } from "./components/LandingPage";
import { LoginModal } from "./components/LoginModal";
import { SignupPage } from "./components/SignupPage";
import { MainPage } from "./components/MainPage";
import { NewLectureModal } from "./components/NewLectureModal";
import { SessionPage } from "./components/SessionPage";
import { SettingsPage } from "./components/SettingsPage";
import { DeleteSessionModal } from "./components/DeleteSessionModal";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { useBackend } from "./services/BackendContext";
import type { Lecture, UserView } from "./services/ports";
import { useI18n, codeToLanguage } from "./i18n/I18nContext";

type Page = "landing" | "signup" | "main" | "session" | "settings";

export default function App() {
  const backend = useBackend();
  const { setLanguage } = useI18n();
  const [currentPage, setCurrentPage] = useState<Page>("landing");
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [newLectureModalOpen, setNewLectureModalOpen] = useState(false);
  const [deleteSessionModalOpen, setDeleteSessionModalOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<number | null>(null);
  const [user, setUser] = useState<UserView | null>(null);
  const [lectures, setLectures] = useState<Lecture[]>([]);
  const [lecturesLoading, setLecturesLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);

  const filteredLectures = useMemo(() => {
    if (!user) return [] as Lecture[];
    return lectures.filter((lecture) => lecture.userId === user.id);
  }, [lectures, user]);

  const fetchLectures = useCallback(async () => {
    setLecturesLoading(true);
    try {
      const data = await backend.lecture.getLectures();
      setLectures(data);
    } catch (error) {
      console.error(error);
      toast.error("강의 목록을 불러오지 못했습니다");
    } finally {
      setLecturesLoading(false);
    }
  }, [backend]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await backend.settings.getUser();
        if (cancelled) return;
        // DB에서 읽은 코드를 표시명으로 변환
        const displayLang = codeToLanguage(me.uiLanguage || "ko");
        const normalized = { ...me, uiLanguage: me.uiLanguage || "ko" };
        setUser(normalized);
        setLanguage(displayLang);
        // 로그인되어 있어도 랜딩 페이지 유지 (사용자가 직접 로그인해야 메인으로 이동)
        await fetchLectures();
      } catch (error) {
        console.info("User not authenticated", error);
        // 비로그인 상태: 한국어 고정
        if (!cancelled) {
          setLanguage("한국어");
        }
      } finally {
        if (!cancelled) setInitializing(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [backend, fetchLectures]);

  const handleLogin = useCallback(
    async (loginId: string, password: string) => {
      try {
        const authResp = await backend.auth.login({ loginId, password });
        const me = await backend.settings.getUser().catch(() => null);
        let effectiveUser: UserView = {
          id: authResp.user.id,
          loginId: authResp.user.loginId,
          name: authResp.user.name,
          email: authResp.user.email,
          uiLanguage: authResp.user.uiLanguage ?? "ko",
        };
        if (me) {
          effectiveUser = { ...me, uiLanguage: me.uiLanguage || effectiveUser.uiLanguage || "ko" };
        }
        // DB에서 읽은 코드를 표시명으로 변환
        const displayLang = codeToLanguage(effectiveUser.uiLanguage || "ko");
        setUser(effectiveUser);
        setLanguage(displayLang);
        setLoginModalOpen(false);
        setCurrentPage("main");
        await fetchLectures();
        toast.success("로그인되었습니다");
      } catch (error) {
        console.error(error);
        toast.error(error instanceof Error ? error.message : "로그인에 실패했습니다");
        throw error;
      }
    },
    [backend, fetchLectures],
  );

  const handleSignup = useCallback(
    async (data: { loginId: string; email: string; password: string; name: string }) => {
      try {
        await backend.auth.signup({
          loginId: data.loginId,
          password: data.password,
          email: data.email,
          name: data.name,
        });
        await handleLogin(data.loginId, data.password);
      } catch (error) {
        console.error(error);
        toast.error(error instanceof Error ? error.message : "회원가입에 실패했습니다");
        throw error;
      }
    },
    [backend, handleLogin],
  );

  const handleLogout = useCallback(async () => {
    try {
      await backend.auth.logout();
    } catch (error) {
      console.error(error);
    }
    setUser(null);
    setLectures([]);
    setCurrentSessionId(null);
    setCurrentPage("landing");
    // 로그아웃 시 UI 언어는 한국어로 고정
    setLanguage("한국어");
    toast.success("로그아웃되었습니다");
  }, [backend]);

  const handleNewLecture = useCallback(
    async (data: { language: string; category: string; subject: string; files: File[] }) => {
      try {
        const lecture = await backend.lecture.createLecture({
          title: data.subject,
          subject: data.category,
          sttLanguage: data.language,
          files: data.files,
        });
        await fetchLectures();
        setCurrentSessionId(lecture.id);
        setNewLectureModalOpen(false);
        setCurrentPage("session");
        toast.success("새 강의가 시작되었습니다");
      } catch (error) {
        console.error(error);
        toast.error(error instanceof Error ? error.message : "새 강의를 시작하지 못했습니다");
        throw error;
      }
    },
    [backend, fetchLectures],
  );

  const handleSessionClick = useCallback((sessionId: number) => {
    setCurrentSessionId(sessionId);
    setCurrentPage("session");
  }, []);

  const handleEndSession = useCallback(
    async (sessionName: string) => {
      if (!currentSessionId) return;
      try {
        await backend.lecture.endLecture(currentSessionId, { title: sessionName });
        await fetchLectures();
        setCurrentSessionId(null);
        setCurrentPage("main");
        toast.success("강의가 저장되었습니다");
      } catch (error) {
        console.error(error);
        toast.error(error instanceof Error ? error.message : "강의 종료 처리에 실패했습니다");
        throw error;
      }
    },
    [backend, currentSessionId, fetchLectures],
  );

  const handleDeleteSession = useCallback((sessionId: number) => {
    setSessionToDelete(sessionId);
    setDeleteSessionModalOpen(true);
  }, []);

  const confirmDeleteSession = useCallback(async () => {
    if (sessionToDelete == null) {
      return;
    }
    try {
      await backend.lecture.deleteLecture(sessionToDelete);
      await fetchLectures();
      toast.success("강의가 삭제되었습니다");
    } catch (error) {
      console.error(error);
      toast.error(error instanceof Error ? error.message : "강의를 삭제하지 못했습니다");
      throw error;
    } finally {
      setDeleteSessionModalOpen(false);
      setSessionToDelete(null);
    }
  }, [backend, fetchLectures, sessionToDelete]);

  const handleRenameSession = useCallback(
    async (sessionId: number, newName: string) => {
      try {
        await backend.lecture.updateLectureTitle(sessionId, { title: newName });
        await fetchLectures();
        toast.success("강의 이름이 변경되었습니다");
      } catch (error) {
        console.error(error);
        toast.error(error instanceof Error ? error.message : "강의 이름 변경에 실패했습니다");
        throw error;
      }
    },
    [backend, fetchLectures],
  );

  const handleSettings = useCallback(
    async (data: { language: string; currentPassword?: string; newPassword?: string }) => {
      try {
        // data.language는 이미 코드로 변환되어 전달됨
        const updated = await backend.settings.setLanguage({ language: data.language || "ko" });
        const normalized = { ...updated, uiLanguage: updated.uiLanguage || "ko" };
        // DB에서 읽은 코드를 표시명으로 변환
        const displayLang = codeToLanguage(normalized.uiLanguage || "ko");
        setUser(normalized);
        setLanguage(displayLang);
        if (data.newPassword && data.currentPassword) {
          await backend.settings.setPassword({
            currentPassword: data.currentPassword,
            newPassword: data.newPassword,
          });
          toast.success("비밀번호가 변경되었습니다");
        }
        setCurrentPage("main");
        toast.success("설정이 저장되었습니다");
      } catch (error) {
        console.error(error);
        toast.error(error instanceof Error ? error.message : "설정을 저장하지 못했습니다");
        throw error;
      }
    },
    [backend],
  );

  const sessionForDeletion = useMemo(
    () => lectures.find((lecture) => lecture.id === sessionToDelete),
    [lectures, sessionToDelete],
  );

  if (initializing) {
    return (
      <>
        <div className="min-h-screen flex items-center justify-center text-muted-foreground">
          초기화 중입니다...
        </div>
        <Toaster />
      </>
    );
  }

  return (
    <>
      {currentPage === "landing" && (
        <LandingPage
          onLoginClick={() => setLoginModalOpen(true)}
          onSignupClick={() => setCurrentPage("signup")}
        />
      )}

      {currentPage === "signup" && (
        <SignupPage onSignup={handleSignup} onBack={() => setCurrentPage("landing")} />
      )}

      {currentPage === "main" && (
        <MainPage
          onNewLecture={() => setNewLectureModalOpen(true)}
          onSessionClick={handleSessionClick}
          onSettings={() => setCurrentPage("settings")}
          onLogout={handleLogout}
          onDeleteSession={handleDeleteSession}
          onRenameSession={handleRenameSession}
          lectures={filteredLectures}
          loading={lecturesLoading}
        />
      )}

      {currentPage === "session" && currentSessionId != null && (
        <SessionPage
          lectureId={currentSessionId}
          onLogoClick={() => setCurrentPage("main")}
          onSettings={() => setCurrentPage("settings")}
          onLogout={handleLogout}
          onSaveAndEnd={handleEndSession}
        />
      )}

      {currentPage === "settings" && user && (
        <SettingsPage
          onBack={() => setCurrentPage("main")}
          onSave={handleSettings}
          currentLanguage={user.uiLanguage || "ko"}
        />
      )}

      <LoginModal
        open={loginModalOpen}
        onClose={() => setLoginModalOpen(false)}
        onLogin={handleLogin}
        onSignupClick={() => {
          setLoginModalOpen(false);
          setCurrentPage("signup");
        }}
      />

      <NewLectureModal
        open={newLectureModalOpen}
        onClose={() => setNewLectureModalOpen(false)}
        onStart={handleNewLecture}
      />

      <DeleteSessionModal
        open={deleteSessionModalOpen}
        sessionName={sessionForDeletion?.title ?? ""}
        onClose={() => {
          setDeleteSessionModalOpen(false);
          setSessionToDelete(null);
        }}
        onConfirm={confirmDeleteSession}
      />

      <Toaster />
    </>
  );
}
