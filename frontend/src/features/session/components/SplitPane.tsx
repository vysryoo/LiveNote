import { useLayoutEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { ScrollArea } from "@/shared/ui/scroll-area";
import type { Bookmark, QnA, Resource } from "../api/schemas";
import type { StreamingCard } from "../state/sessionReducer";
import { AnimatedLoaderIcon } from "./AnimatedLoaderIcon";
import { QnaCard, ResourceCard, StreamingCardView } from "./SessionCards";

type SplitPaneProps = {
  resources: Resource[];
  qna: QnA[];
  streamingResources: StreamingCard[];
  streamingQna: StreamingCard[];
  isGenerating: boolean;
  showBookmarkedOnly: boolean;
  autoMode: boolean;
  isBookmarked: (targetType: Bookmark["targetType"], targetId: number) => boolean;
  onToggleBookmark: (target: {
    targetType: Bookmark["targetType"];
    targetId: number;
    sectionIndex: number;
  }) => void;
  onClose: () => void;
  onToggleBookmarkedOnly: () => void;
  onToggleAutoMode: () => void;
};

// 새 스트리밍 카드가 생기면 목록 맨 아래를 보여 줌
function useScrollToBottomOnGrow(count: number) {
  const contentRef = useRef<HTMLDivElement>(null);
  const previousCountRef = useRef(count);
  useLayoutEffect(() => {
    if (count > previousCountRef.current) {
      const viewport = contentRef.current?.closest<HTMLElement>(
        '[data-slot="scroll-area-viewport"]',
      );
      if (viewport) viewport.scrollTop = viewport.scrollHeight;
    }
    previousCountRef.current = count;
  }, [count]);
  return contentRef;
}

function LoadingHint({ id, text }: { id: string; text: string }) {
  return (
    <div className="flex items-center justify-start gap-2 mt-1">
      <AnimatedLoaderIcon id={id} />
      <span className="text-[rgb(125,128,136)] text-xs text-[14px]">{text}</span>
    </div>
  );
}

export function SplitPane({
  resources,
  qna,
  streamingResources,
  streamingQna,
  isGenerating,
  showBookmarkedOnly,
  autoMode,
  isBookmarked,
  onToggleBookmark,
  onClose,
  onToggleBookmarkedOnly,
  onToggleAutoMode,
}: SplitPaneProps) {
  const { t } = useTranslation();
  const resourceListRef = useScrollToBottomOnGrow(streamingResources.length);
  const qnaListRef = useScrollToBottomOnGrow(streamingQna.length);

  const visibleResources = showBookmarkedOnly
    ? resources.filter((r) => isBookmarked("resource", r.id))
    : resources;
  const visibleQna = showBookmarkedOnly ? qna.filter((q) => isBookmarked("qna", q.id)) : qna;
  const showResourceHint =
    !showBookmarkedOnly &&
    (resources.length === 0 || (isGenerating && streamingResources.length === 0));
  const showQnaHint =
    !showBookmarkedOnly && (qna.length === 0 || (isGenerating && streamingQna.length === 0));

  return (
    <div className="flex-1 p-2 flex items-center justify-center">
      <div className="w-full h-full rounded-xl overflow-hidden shadow-2xl flex flex-col">
        <div
          className="flex items-center justify-between px-4 py-2 bg-[#333333]"
          style={{ height: "29px" }}
        >
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="w-3 h-3 rounded-full bg-[#FF605C] hover:bg-[#FF3B30] transition-colors cursor-pointer"
              title={t("session.closeSplit")}
            />
            <button
              type="button"
              onClick={onToggleBookmarkedOnly}
              className="w-3 h-3 rounded-full transition-colors cursor-pointer bg-[#FFBD44] hover:bg-[#FFB000]"
              title={t("session.bookmarkFilter")}
            />
            <button
              type="button"
              onClick={onToggleAutoMode}
              className={`w-3 h-3 rounded-full transition-colors cursor-pointer border border-white/20 ${
                autoMode
                  ? "bg-[#66FFAA] hover:bg-[#88FFCC] shadow-[0_0_4px_rgba(102,255,170,0.6)]"
                  : "bg-[#55EE99] hover:bg-[#66FFAA]"
              }`}
              title={t(autoMode ? "session.autoModeOff" : "session.autoModeOn")}
            />
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden bg-white">
          <div className="w-1/2 border-r p-[12px] flex flex-col bg-[#f9fafb]">
            <h3 className="mb-2 text-[16px]">&nbsp;{t("session.resources")}</h3>
            <ScrollArea className="flex-1 h-0">
              <div ref={resourceListRef} className="flex flex-col gap-3 p-[0px]">
                {visibleResources.map((resource) => (
                  <ResourceCard
                    key={resource.id}
                    resource={resource}
                    bookmarked={isBookmarked("resource", resource.id)}
                    onToggleBookmark={() =>
                      onToggleBookmark({
                        targetType: "resource",
                        targetId: resource.id,
                        sectionIndex: resource.sectionIndex,
                      })
                    }
                  />
                ))}
                {streamingResources.map((card) => (
                  <StreamingCardView key={card.cardId} card={card} />
                ))}
                {showResourceHint && (
                  <LoadingHint id="grad-resources" text={t("session.findingResources")} />
                )}
              </div>
            </ScrollArea>
          </div>

          <div className="w-1/2 p-[12px] flex flex-col bg-[#f9fafb]">
            <h3 className="mb-2 text-[16px]">&nbsp;{t("session.ai")}</h3>
            <ScrollArea className="flex-1 h-0">
              <div ref={qnaListRef} className="flex flex-col gap-3 p-[0px]">
                {visibleQna.map((item) => (
                  <QnaCard
                    key={item.id}
                    qna={item}
                    bookmarked={isBookmarked("qna", item.id)}
                    onToggleBookmark={() =>
                      onToggleBookmark({
                        targetType: "qna",
                        targetId: item.id,
                        sectionIndex: item.sectionIndex,
                      })
                    }
                  />
                ))}
                {streamingQna.map((card) => (
                  <StreamingCardView key={card.cardId} card={card} />
                ))}
                {showQnaHint && (
                  <LoadingHint id="grad-ai" text={t("session.generatingQuestions")} />
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>
    </div>
  );
}
