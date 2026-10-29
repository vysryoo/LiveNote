import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createLecture,
  deleteLecture,
  endLecture,
  lectureKeys,
  updateLectureTitle,
} from "../api/lecturesApi";

/**
 * 강의 생성 mutation을 반환한다. 성공 시 목록을 무효화한다.
 *
 * @returns TanStack Query mutation
 */
export function useCreateLecture() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createLecture,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: lectureKeys.list }),
  });
}

/**
 * 강의 제목 변경 mutation을 반환한다. 성공 시 목록과 해당 강의 상세를 무효화한다.
 *
 * @returns TanStack Query mutation
 */
export function useRenameLecture() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ lectureId, title }: { lectureId: number; title: string }) =>
      updateLectureTitle(lectureId, title),
    onSuccess: (_lecture, { lectureId }) =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: lectureKeys.list }),
        queryClient.invalidateQueries({ queryKey: lectureKeys.detail(lectureId) }),
      ]),
  });
}

/**
 * 강의 삭제 mutation을 반환한다. 성공 시 목록을 무효화한다.
 *
 * @returns TanStack Query mutation
 */
export function useDeleteLecture() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteLecture,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: lectureKeys.list }),
  });
}

/**
 * 강의 종료 mutation을 반환한다. 성공 시 목록과 해당 강의 상세를 무효화한다.
 *
 * @returns TanStack Query mutation
 */
export function useEndLecture() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ lectureId, title }: { lectureId: number; title: string }) =>
      endLecture(lectureId, title),
    onSuccess: (_lecture, { lectureId }) =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: lectureKeys.list }),
        queryClient.invalidateQueries({ queryKey: lectureKeys.detail(lectureId) }),
      ]),
  });
}
