import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Badge } from "@/shared/ui/badge";
import { cn } from "@/shared/ui/utils";
import type { QnA, Resource } from "../api/schemas";
import { useTypewriter } from "../hooks/useTypewriter";
import { toDisplayReason } from "../lib/resourceReason";
import type { StreamingCard } from "../lib/sessionReducer";

const CARD_CLASS =
  "border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px]";
const BRAND_GRADIENT =
  "linear-gradient(90deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)";

type ResourceCategory = "paper" | "wiki" | "video" | "blog";

const RESOURCE_GRADIENTS: Record<ResourceCategory, string> = {
  paper: "linear-gradient(90deg, #0c4997, #1e5fa8, #3b72dd, #4d82e0)",
  wiki: "linear-gradient(90deg, #0c966b, #10b981, #34d399, #6ee7b7)",
  video: "linear-gradient(90deg, #960c0c, #dc2626, #ef4444, #f87171)",
  blog: "linear-gradient(90deg, #3f0c96, #6366f1, #8b5cf6, #a78bfa)",
};

// 백엔드 자료 유형(PAPER, WIKI, VIDEO, YOUTUBE, GOOGLE, BLOG)을 화면 분류 네 가지로 묶음
function toResourceCategory(type: string): ResourceCategory {
  if (type === "paper" || type === "wiki") return type;
  if (type === "video" || type === "youtube") return "video";
  return "blog";
}

const QNA_TYPE_KEYS = {
  concept: "session.qnaTypes.concept",
  application: "session.qnaTypes.application",
  advanced: "session.qnaTypes.advanced",
  comparison: "session.qnaTypes.comparison",
} as const;

function BookmarkToggle({
  id,
  checked,
  onToggle,
  className,
}: {
  id: string;
  checked: boolean;
  onToggle: () => void;
  className?: string;
}) {
  return (
    <label className="ml-2 flex-shrink-0">
      <input type="checkbox" id={id} checked={checked} onChange={onToggle} />
      <label htmlFor={id} className={`bookmark scale-[0.6] ${className ?? ""}`}>
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
  );
}

export function ResourceCard({
  resource,
  bookmarked,
  animate,
  onToggleBookmark,
}: {
  resource: Resource;
  bookmarked: boolean;
  animate: boolean;
  onToggleBookmark: () => void;
}) {
  const { t } = useTranslation();
  const category = toResourceCategory(resource.type);
  const description = useTypewriter(resource.text, animate);
  const reason = toDisplayReason(resource.reason);
  return (
    <CardFrame
      badge={t(`session.resourceTypes.${category}`)}
      badgeBackground={RESOURCE_GRADIENTS[category]}
      centerBadge
      bookmark={
        <BookmarkToggle
          id={`checkboxInput-resource-${resource.id}`}
          checked={bookmarked}
          onToggle={onToggleBookmark}
          className="text-[rgb(163,172,183)]"
        />
      }
      title={resource.title || t("lectures.untitled")}
      body={resource.text ? description : t("session.noDescription")}
      keepLineBreaks={false}
    >
      {reason && (
        <div className="pt-3 flex-shrink-0 text-xs text-muted-foreground">
          <span className="font-medium">{t("session.recommendationReason")}</span>
          <p className="mt-1 line-clamp-2" title={reason}>
            {reason}
          </p>
        </div>
      )}
      {resource.url && (
        <div className="pt-3 text-right text-xs text-muted-foreground">
          <a href={resource.url} target="_blank" rel="noreferrer" className="underline">
            {t("session.viewDetails")}
          </a>
        </div>
      )}
    </CardFrame>
  );
}

export function QnaCard({
  qna,
  bookmarked,
  onToggleBookmark,
}: {
  qna: QnA;
  bookmarked: boolean;
  onToggleBookmark: () => void;
}) {
  const { t } = useTranslation();
  const typeKey = QNA_TYPE_KEYS[qna.type as keyof typeof QNA_TYPE_KEYS] ?? QNA_TYPE_KEYS.comparison;
  return (
    <CardFrame
      badge={t(typeKey)}
      badgeBackground={BRAND_GRADIENT}
      bookmark={
        <BookmarkToggle
          id={`checkboxInput-ai-${qna.id}`}
          checked={bookmarked}
          onToggle={onToggleBookmark}
        />
      }
      title={qna.question}
      body={qna.answer}
    />
  );
}

export function StreamingCardView({ card }: { card: StreamingCard }) {
  const { t } = useTranslation();
  const generating = t("session.generating");
  const background =
    card.kind === "resource" && card.resourceType
      ? RESOURCE_GRADIENTS[toResourceCategory(card.resourceType)]
      : BRAND_GRADIENT;
  return (
    <CardFrame
      badge={generating}
      badgeBackground={background}
      title={card.title || generating}
      body={card.content || generating}
    />
  );
}

// 카드 3종의 공통 틀: 배지와 북마크 줄, 제목, 스크롤되는 본문, 추가 내용
function CardFrame({
  badge,
  badgeBackground,
  centerBadge = false,
  bookmark,
  title,
  body,
  keepLineBreaks = true,
  children,
}: {
  badge: string;
  badgeBackground: string;
  centerBadge?: boolean;
  bookmark?: ReactNode;
  title: string;
  body: string;
  keepLineBreaks?: boolean;
  children?: ReactNode;
}) {
  return (
    <div className={CARD_CLASS}>
      <div className="flex items-start justify-between mb-3 flex-shrink-0">
        <Badge
          className={cn(
            "text-xs text-[rgb(255,255,255)] flex-shrink-0",
            centerBadge && "self-center",
          )}
          style={{ background: badgeBackground }}
        >
          {badge}
        </Badge>
        {bookmark}
      </div>
      <div className="mb-3 flex-shrink-0">
        <p className="font-medium">{title}</p>
      </div>
      <div className="flex-1 overflow-y-auto">
        <p className={cn("text-sm text-muted-foreground", keepLineBreaks && "whitespace-pre-line")}>
          {body}
        </p>
      </div>
      {children}
    </div>
  );
}
