import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import type { Bookmark, SessionDetail } from "../api/schemas";
import { addBookmark, deleteBookmark, sessionKeys } from "../api/sessionApi";

type BookmarkTarget = {
  targetType: Bookmark["targetType"];
  targetId: number;
  sectionIndex: number;
};

/**
 * 북마크 여부 판별 함수와 추가·해제 함수를 반환한다. 추가·해제 결과는 강의 상세 캐시의 북마크 목록에 반영한다.
 *
 * @param lectureId 강의 ID
 * @param bookmarks 현재 북마크 목록
 * @returns `isBookmarked`(대상이 북마크됐는지)와 `toggle`(대상의 북마크 여부를 바꿈)
 */
export function useBookmarks(lectureId: number, bookmarks: Bookmark[]) {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  const updateBookmarks = (update: (current: Bookmark[]) => Bookmark[]) =>
    queryClient.setQueryData<SessionDetail>(sessionKeys.detail(lectureId), (detail) =>
      detail ? { ...detail, bookmarks: update(detail.bookmarks) } : detail,
    );

  const mutation = useMutation({
    mutationFn: async (target: BookmarkTarget) => {
      const existing = bookmarks.find(
        (b) => b.targetType === target.targetType && b.targetId === target.targetId,
      );
      if (existing) {
        await deleteBookmark(existing.id);
        updateBookmarks((current) => current.filter((b) => b.id !== existing.id));
        return "removed" as const;
      }
      const created = await addBookmark({ lectureId, ...target });
      updateBookmarks((current) => [...current, created]);
      return "added" as const;
    },
    onSuccess: (result) =>
      toast.success(t(result === "added" ? "session.bookmarkAdded" : "session.bookmarkRemoved")),
    onError: () => toast.error(t("session.bookmarkFailed")),
  });

  return {
    isBookmarked: (targetType: Bookmark["targetType"], targetId: number) =>
      bookmarks.some((b) => b.targetType === targetType && b.targetId === targetId),
    toggle: (target: BookmarkTarget) => mutation.mutate(target),
  };
}
