import React from "react";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import { AnimatedLoaderIcon } from "./AnimatedLoaderIcon";
import type { Resource, QnA } from "../services/ports";
import StreamingResourceCard from "./StreamingResourceCard";
import StreamingQnACard from "./StreamingQnACard";
import type { StreamingCard } from "./StreamingCardTypes";

interface SplitPaneProps {
  splitMode: boolean;
  showBookmarkedOnly: boolean;
  autoMode: boolean;
  loading: boolean;
  isGeneratingExtended: boolean;
  resourcesForView: Resource[];
  qnaForView: QnA[];
  streamingResourcesForSection: StreamingCard[];
  streamingQnAsForSection: StreamingCard[];
  isBookmarked: (type: "resource" | "qna", id: number) => boolean;
  toggleBookmark: (type: "resource" | "qna", id: number, sectionIndex: number) => void;
  closeSplitMode: () => void;
  setShowBookmarkedOnly: (value: boolean) => void;
  setAutoMode: (value: boolean) => void;
  resourceScrollViewportRef: React.MutableRefObject<HTMLDivElement | null>;
  qnaScrollViewportRef: React.MutableRefObject<HTMLDivElement | null>;
  t: (key: string) => string;
}

export function SplitPane({
  splitMode,
  showBookmarkedOnly,
  autoMode,
  loading,
  isGeneratingExtended,
  resourcesForView,
  qnaForView,
  streamingResourcesForSection,
  streamingQnAsForSection,
  isBookmarked,
  toggleBookmark,
  closeSplitMode,
  setShowBookmarkedOnly,
  setAutoMode,
  resourceScrollViewportRef,
  qnaScrollViewportRef,
  t,
}: SplitPaneProps) {
  if (!splitMode) return null;

  return (
    <div className="flex-1 p-2 flex items-center justify-center">
      <div className="w-full h-full rounded-xl overflow-hidden shadow-2xl flex flex-col">
        {/* macOS Window Bar */}
        <div
          className="flex items-center justify-between px-4 py-2 bg-[#333333]"
          style={{ height: "29px" }}
        >
          <div className="flex items-center gap-2">
            <button
              onClick={closeSplitMode}
              className="w-3 h-3 rounded-full bg-[#FF605C] hover:bg-[#FF3B30] transition-colors cursor-pointer"
              title="창 닫기"
            />
            <button
              onClick={() => setShowBookmarkedOnly(!showBookmarkedOnly)}
              className={`w-3 h-3 rounded-full transition-colors cursor-pointer ${
                showBookmarkedOnly ? "bg-[#FFBD44]" : "bg-[#FFBD44] hover:bg-[#FFB000]"
              }`}
              title="북마크 필터"
            />
            <button
              onClick={() => setAutoMode(!autoMode)}
              className="w-3 h-3 rounded-full transition-colors cursor-pointer border border-white/20"
              style={
                autoMode
                  ? {
                      backgroundColor: "#66FFAA",
                      boxShadow: "0 0 4px rgba(102,255,170,0.6)",
                    }
                  : { backgroundColor: "#55EE99" }
              }
              onMouseEnter={(e) => {
                if (autoMode) {
                  e.currentTarget.style.backgroundColor = "#88FFCC";
                } else {
                  e.currentTarget.style.backgroundColor = "#66FFAA";
                }
              }}
              onMouseLeave={(e) => {
                if (autoMode) {
                  e.currentTarget.style.backgroundColor = "#66FFAA";
                } else {
                  e.currentTarget.style.backgroundColor = "#55EE99";
                }
              }}
              title={autoMode ? "오토모드 끄기" : "오토모드 켜기"}
            />
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden bg-white">
          {/* Resources Pane */}
          <div className="w-1/2 border-r p-[12px] flex flex-col bg-[#f9fafb]">
            <h3 className="mb-2 text-[16px]">&nbsp;{t("session.resources")}</h3>

            <ScrollArea className="flex-1 h-0">
              <div
                ref={(el) => {
                  if (el) {
                    const viewport = el
                      .closest('[data-slot="scroll-area"]')
                      ?.querySelector('[data-slot="scroll-area-viewport"]') as HTMLDivElement;
                    if (viewport) {
                      resourceScrollViewportRef.current = viewport;
                    }
                  }
                }}
                className="flex flex-col gap-3 p-[0px]"
              >
                {/* 완료된 Resource 카드 먼저 표시 */}
                {resourcesForView.map((resource) => {
                  const bookmarked = isBookmarked("resource", resource.id);
                  if (showBookmarkedOnly && !bookmarked) {
                    return null;
                  }
                  const resourceTitle =
                    (Array.isArray(resource.title) ? resource.title.join(" ") : resource.title) ||
                    "제목 없음";
                  const resourceDescription =
                    (Array.isArray(resource.text) ? resource.text.join(" ") : resource.text) ||
                    "설명이 없습니다.";
                  return (
                    <div
                      key={resource.id}
                      className="border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px]"
                    >
                      <div className="flex items-start justify-between mb-3 flex-shrink-0">
                        <Badge
                          className="text-xs text-[rgb(255,255,255)] flex-shrink-0 self-center"
                          style={{
                            background:
                              resource.type === "paper"
                                ? "linear-gradient(90deg, #0c4997, #1e5fa8, #3b72dd, #4d82e0)"
                                : resource.type === "wiki"
                                  ? "linear-gradient(90deg, #0c966b, #10b981, #34d399, #6ee7b7)"
                                  : resource.type === "video"
                                    ? "linear-gradient(90deg, #960c0c, #dc2626, #ef4444, #f87171)"
                                    : "linear-gradient(90deg, #3f0c96, #6366f1, #8b5cf6, #a78bfa)",
                          }}
                        >
                          {resource.type === "paper"
                            ? "학술자료"
                            : resource.type === "wiki"
                              ? "위키백과"
                              : resource.type === "video"
                                ? "유튜브"
                                : "웹/블로그"}
                        </Badge>
                        <label className="ml-2 flex-shrink-0">
                          <input
                            type="checkbox"
                            id={`checkboxInput-resource-${resource.id}`}
                            checked={bookmarked}
                            onChange={() =>
                              toggleBookmark("resource", resource.id, resource.sectionIndex)
                            }
                          />
                          <label
                            htmlFor={`checkboxInput-resource-${resource.id}`}
                            className="bookmark scale-[0.6] text-[rgb(163,172,183)]"
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              height="1em"
                              viewBox="0 0 384 512"
                              className="svgIcon"
                            >
                              <path d="M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z"></path>
                            </svg>
                          </label>
                        </label>
                      </div>
                      <div className="mb-3 flex-shrink-0">
                        <p className="font-medium">{resourceTitle}</p>
                      </div>
                      <div className="flex-1 overflow-y-auto">
                        <p className="text-sm text-muted-foreground">{resourceDescription}</p>
                      </div>
                      <div className="pt-3 text-right text-xs text-muted-foreground">
                        <a
                          href={resource.url}
                          target="_blank"
                          rel="noreferrer"
                          className="underline"
                        >
                          자세히 보기
                        </a>
                      </div>
                    </div>
                  );
                })}
                {/* 스트리밍 중인 Resource 카드 표시 (완료된 카드 아래에) */}
                {streamingResourcesForSection.map((streamingCard) => (
                  <StreamingResourceCard key={streamingCard.cardId} card={streamingCard} />
                ))}
                {!showBookmarkedOnly &&
                  !loading &&
                  (resourcesForView.length === 0 ||
                    (isGeneratingExtended && streamingResourcesForSection.length === 0)) && (
                    <div className="flex items-center justify-start gap-2 mt-[3px]">
                      <AnimatedLoaderIcon id="grad-resources" />
                      <span className="text-[rgb(125,128,136)] text-xs text-[14px]">
                        자료를 찾고 있습니다...
                      </span>
                    </div>
                  )}
              </div>
            </ScrollArea>
          </div>

          {/* AI Q&A Pane */}
          <div className="w-1/2 p-[12px] flex flex-col bg-[#f9fafb]">
            <h3 className="mb-2 text-[16px]">&nbsp;{t("session.ai")}</h3>

            <ScrollArea className="flex-1 h-0">
              <div
                ref={(el) => {
                  if (el) {
                    const viewport = el
                      .closest('[data-slot="scroll-area"]')
                      ?.querySelector('[data-slot="scroll-area-viewport"]') as HTMLDivElement;
                    if (viewport) {
                      qnaScrollViewportRef.current = viewport;
                    }
                  }
                }}
                className="flex flex-col gap-3 p-[0px]"
              >
                {/* 완료된 QnA 카드 먼저 표시 */}
                {qnaForView.map((qa) => {
                  const bookmarked = isBookmarked("qna", qa.id);
                  if (showBookmarkedOnly && !bookmarked) {
                    return null;
                  }
                  const typeLabel =
                    qa.type === "concept"
                      ? "개념확인"
                      : qa.type === "application"
                        ? "응용확장"
                        : qa.type === "advanced"
                          ? "심화질의"
                          : "비교분석";
                  return (
                    <div
                      key={qa.id}
                      className="border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px]"
                    >
                      <div className="flex items-start justify-between mb-3 flex-shrink-0">
                        <Badge
                          className="text-xs text-[rgb(255,255,255)] flex-shrink-0"
                          style={{
                            background:
                              "linear-gradient(90deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
                          }}
                        >
                          {typeLabel}
                        </Badge>
                        <label className="ml-2 flex-shrink-0">
                          <input
                            type="checkbox"
                            id={`checkboxInput-ai-${qa.id}`}
                            checked={bookmarked}
                            onChange={() => toggleBookmark("qna", qa.id, qa.sectionIndex)}
                          />
                          <label
                            htmlFor={`checkboxInput-ai-${qa.id}`}
                            className="bookmark scale-[0.6]"
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              height="1em"
                              viewBox="0 0 384 512"
                              className="svgIcon"
                            >
                              <path d="M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z"></path>
                            </svg>
                          </label>
                        </label>
                      </div>
                      <div className="mb-3 flex-shrink-0">
                        <p className="font-medium">
                          {Array.isArray(qa.question) ? qa.question.join("\n") : qa.question}
                        </p>
                      </div>
                      <div className="flex-1 overflow-y-auto">
                        <p className="text-sm text-muted-foreground whitespace-pre-line">
                          {Array.isArray(qa.answer) ? qa.answer.join("\n") : qa.answer}
                        </p>
                      </div>
                    </div>
                  );
                })}
                {/* 스트리밍 중인 QnA 카드 표시 (완료된 카드 아래에) */}
                {streamingQnAsForSection.map((streamingCard) => (
                  <StreamingQnACard key={streamingCard.cardId} card={streamingCard} />
                ))}
                {!showBookmarkedOnly &&
                  !loading &&
                  (qnaForView.length === 0 ||
                    (isGeneratingExtended && streamingQnAsForSection.length === 0)) && (
                    <div className="flex items-center justify-start gap-2 mt-1">
                      <AnimatedLoaderIcon id="grad-ai" />
                      <span className="text-[rgb(125,128,136)] text-xs text-[14px]">
                        AI가 질문을 생성하고 있습니다...
                      </span>
                    </div>
                  )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>
    </div>
  );
}
