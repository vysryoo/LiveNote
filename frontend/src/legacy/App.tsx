import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Outlet, useNavigate } from "react-router";
import { NewLectureModal } from "./components/NewLectureModal";
import { DeleteSessionModal } from "./components/DeleteSessionModal";
import { Toaster } from "@/shared/ui/sonner";
import { toast } from "sonner";
import { useBackend } from "./services/BackendContext";
import type { Lecture } from "./services/ports";
import { useMe } from "@/features/auth/hooks/useMe";
import type { LegacyAppContext } from "./appContext";

export default function App() {
  const backend = useBackend();
  const navigate = useNavigate();
  const { data: user } = useMe();
  const [newLectureModalOpen, setNewLectureModalOpen] = useState(false);
  const [deleteSessionModalOpen, setDeleteSessionModalOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<number | null>(null);
  const [lectures, setLectures] = useState<Lecture[]>([]);
  const [lecturesLoading, setLecturesLoading] = useState(false);

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

  // 로그인한 사용자가 바뀌면 강의 목록을 다시 받고, 로그아웃하면 비움
  useEffect(() => {
    if (user) {
      void fetchLectures();
    } else {
      setLectures([]);
    }
  }, [user?.id, fetchLectures]);

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
        setNewLectureModalOpen(false);
        navigate(`/lectures/${lecture.id}`);
        toast.success("새 강의가 시작되었습니다");
      } catch (error) {
        console.error(error);
        toast.error(error instanceof Error ? error.message : "새 강의를 시작하지 못했습니다");
        throw error;
      }
    },
    [backend, fetchLectures, navigate],
  );

  const handleEndSession = useCallback(
    async (lectureId: number, sessionName: string) => {
      try {
        await backend.lecture.endLecture(lectureId, { title: sessionName });
        await fetchLectures();
        navigate("/lectures");
        toast.success("강의가 저장되었습니다");
      } catch (error) {
        console.error(error);
        toast.error(error instanceof Error ? error.message : "강의 종료 처리에 실패했습니다");
        throw error;
      }
    },
    [backend, fetchLectures, navigate],
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

  const sessionForDeletion = useMemo(
    () => lectures.find((lecture) => lecture.id === sessionToDelete),
    [lectures, sessionToDelete],
  );

  const outletContext: LegacyAppContext = {
    lectures: filteredLectures,
    lecturesLoading,
    openNewLectureModal: () => setNewLectureModalOpen(true),
    handleDeleteSession,
    handleRenameSession,
    handleEndSession,
  };

  return (
    <>
      <Outlet context={outletContext} />

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
