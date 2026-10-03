import React, { memo } from "react";
import { Badge } from "@/shared/ui/badge";
import type { Resource } from "../services/ports";
import type { StreamingCard } from "./StreamingCardTypes";

// 스트리밍 Resource 카드 컴포넌트 (메모이제이션으로 리렌더링 최소화)
const StreamingResourceCard = memo(({ card }: { card: StreamingCard }) => {
  if (card.error) {
    return (
      <div className="border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px] border-red-300">
        <div className="flex items-start justify-between mb-3 flex-shrink-0">
          <Badge className="text-xs bg-red-500 text-white flex-shrink-0">생성 실패</Badge>
        </div>
        <div className="mb-3 flex-shrink-0">
          <p className="font-medium text-red-600">생성 실패</p>
        </div>
        <div className="flex-1 overflow-y-auto">
          <p className="text-sm text-red-500">{card.error}</p>
        </div>
      </div>
    );
  }

  // 타입별 색상 결정
  // 1. card.resourceType이 있으면 사용
  // 2. 없으면 기본 색상 사용
  const resourceType: "paper" | "wiki" | "video" | "blog" | null = card.resourceType || null;

  // 타입별 배지 색상
  const badgeStyle = resourceType
    ? resourceType === "paper"
      ? { background: "linear-gradient(90deg, #0c4997, #1e5fa8, #3b72dd, #4d82e0)" }
      : resourceType === "wiki"
        ? { background: "linear-gradient(90deg, #0c966b, #10b981, #34d399, #6ee7b7)" }
        : resourceType === "video"
          ? { background: "linear-gradient(90deg, #960c0c, #dc2626, #ef4444, #f87171)" }
          : { background: "linear-gradient(90deg, #3f0c96, #6366f1, #8b5cf6, #a78bfa)" }
    : {
        background: "linear-gradient(90deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
      };

  // 제목 추출 우선순위:
  // 1. 완료된 데이터 (card.data.title)가 있으면 사용
  // 2. card.title이 있으면 사용
  // 3. 없으면 "생성 중..." 표시
  const getTitle = () => {
    if (card.data && "title" in card.data) {
      const resource = card.data as Resource;
      const title = resource.title;
      if (title) {
        return Array.isArray(title) ? title.join(" ") : title;
      }
    }
    if (card.title) {
      return card.title;
    }
    return "생성 중...";
  };

  const title = getTitle();

  return (
    <div className="border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px]">
      <div className="flex items-start justify-between mb-3 flex-shrink-0">
        <Badge className="text-xs text-[rgb(255,255,255)] flex-shrink-0" style={badgeStyle}>
          생성 중...
        </Badge>
      </div>
      <div className="mb-3 flex-shrink-0">
        <p className="font-medium">{title}</p>
      </div>
      <div className="flex-1 overflow-y-auto">
        <p className="text-sm text-muted-foreground">{card.content || "생성 중..."}</p>
      </div>
    </div>
  );
});

StreamingResourceCard.displayName = "StreamingResourceCard";

export default StreamingResourceCard;
