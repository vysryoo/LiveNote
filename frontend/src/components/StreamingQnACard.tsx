import React, { memo } from "react";
import { Badge } from "./ui/badge";
import type { StreamingCard } from "./StreamingCardTypes";

// 스트리밍 QnA 카드 컴포넌트 (메모이제이션으로 리렌더링 최소화)
const StreamingQnACard = memo(({ card }: { card: StreamingCard }) => {
  if (card.error) {
    return (
      <div
        className="border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px] border-red-300"
      >
        <div className="flex items-start justify-between mb-3 flex-shrink-0">
          <Badge className="text-xs bg-red-500 text-white flex-shrink-0">
            생성 실패
          </Badge>
        </div>
        <div className="mb-3 flex-shrink-0">
          <p className="font-medium text-red-600">생성 실패</p>
        </div>
        <div className="flex-1 overflow-y-auto">
          <p className="text-sm text-red-500 whitespace-pre-line">
            {card.error}
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div
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
          생성 중...
        </Badge>
      </div>
      <div className="mb-3 flex-shrink-0">
        <p className="font-medium">생성 중...</p>
      </div>
      <div className="flex-1 overflow-y-auto">
        <p className="text-sm text-muted-foreground whitespace-pre-line">
          {card.content || "생성 중..."}
        </p>
      </div>
    </div>
  );
});

StreamingQnACard.displayName = "StreamingQnACard";

export default StreamingQnACard;


