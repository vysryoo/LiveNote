import type { ParseKeys } from "i18next";
import { BookOpen, Check, Chrome, GraduationCap, Youtube, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Trans, useTranslation } from "react-i18next";
import { cn } from "@/shared/ui/utils";

const RESOURCE_TILES: {
  icon: LucideIcon;
  background: string;
  typeKey: ParseKeys;
  descKey: ParseKeys;
}[] = [
  {
    icon: GraduationCap,
    background: "var(--brand-gradient)",
    typeKey: "session.resourceTypes.paper",
    descKey: "landing.resources.paperDesc",
  },
  {
    icon: BookOpen,
    background: "linear-gradient(135deg, #63EE86, #5BA26D, #83F19E, #63FF8A, #3BDD64, #4DE072)",
    typeKey: "session.resourceTypes.wiki",
    descKey: "landing.resources.wikiDesc",
  },
  {
    icon: Youtube,
    background: "linear-gradient(135deg, #EE6363, #A25B5B, #F18383, #FF6363, #DD3B3B, #E04D4D)",
    typeKey: "session.resourceTypes.video",
    descKey: "landing.resources.videoDesc",
  },
  {
    icon: Chrome,
    background: "linear-gradient(135deg, #A863EE, #7E5BA2, #BA83F1, #B163FF, #8C3BDD, #964DE0)",
    typeKey: "session.resourceTypes.blog",
    descKey: "landing.resources.blogDesc",
  },
];

/**
 * 실시간 요약 기능 소개. 세션 화면의 기록·요약 카드를 흉내 낸 예시와 설명을 나란히 표시한다.
 */
export function SummaryFeature() {
  const { t } = useTranslation();
  return (
    <FeatureRow align="items-center">
      <div className="relative">
        <MockSessionWindow spaciousHeader>
          <div className="space-y-6 pb-6">
            <div className="rounded-lg p-6 bg-white">
              <h4 className="mb-4">{t("session.header.record")}</h4>
              <p className="text-sm text-muted-foreground">{t("landing.mock.transcript")}</p>
            </div>
            <div className="rounded-lg p-6 bg-white hover:bg-muted cursor-pointer transition-all border-brand-gradient">
              <h4 className="mb-4">{t("session.header.summary")}</h4>
              <p className="text-sm text-muted-foreground">{t("landing.mock.summary")}</p>
            </div>
          </div>
        </MockSessionWindow>
      </div>

      <FeatureDescription
        title={t("session.header.summary")}
        description={t("landing.summary.desc")}
      >
        <CheckList
          itemKeys={["landing.summary.point1", "landing.summary.point2", "landing.summary.point3"]}
        />
      </FeatureDescription>
    </FeatureRow>
  );
}

/**
 * 자료 추천 기능 소개. 자료 종류 타일 4개와 자료 카드 예시를 나란히 표시한다.
 */
export function ResourcesFeature() {
  // Trans에 t를 넘겨야 언어가 바뀔 때 다시 그려짐. 넘기지 않으면 React Compiler가 이전 언어의 Trans를 재사용함
  const { t } = useTranslation();
  return (
    <FeatureRow align="items-stretch">
      <FeatureDescription
        title={t("landing.resources.title")}
        description={<Trans t={t} i18nKey="landing.resources.desc" />}
      >
        <div className="grid grid-cols-2 gap-4 mb-6">
          {RESOURCE_TILES.map(({ icon: Icon, background, typeKey, descKey }) => (
            <div key={typeKey} className="rounded-xl p-5" style={{ background }}>
              <div className="flex items-center mb-3">
                <Icon className="w-8 h-8 text-white" />
              </div>
              <div className="font-semibold text-white mb-1">{t(typeKey)}</div>
              <div className="text-sm text-white/90">{t(descKey)}</div>
            </div>
          ))}
        </div>
      </FeatureDescription>

      <div>
        <MockSessionWindow fullHeight>
          <div className="flex flex-col gap-3">
            <MockCard
              badge={t("session.resourceTypes.paper")}
              badgeColor="bg-[rgb(12,73,151)]"
              title="Attention Is All You Need"
              text="We present the Transformer, a model based entirely on self-attention without recurrence or convolution..."
            />
            <MockCard
              badge={t("session.resourceTypes.video")}
              badgeColor="bg-[#960c0c]"
              title="Transformers, the tech behind LLMs | Deep Learning Chapter 5"
              text="This video visually explains how Large Language Models (LLMs) work, focusing on Transformers..."
              animationDelay="0.2s"
            />
          </div>
        </MockSessionWindow>
      </div>
    </FeatureRow>
  );
}

/**
 * AI 질문 생성 기능 소개. QnA 카드 예시와 설명을 나란히 표시한다.
 */
export function QnaFeature() {
  // Trans에 t를 넘겨야 언어가 바뀔 때 다시 그려짐. 넘기지 않으면 React Compiler가 이전 언어의 Trans를 재사용함
  const { t } = useTranslation();
  return (
    <FeatureRow align="items-center">
      <div className="space-y-4">
        <MockSessionWindow>
          <div className="flex flex-col gap-3">
            <MockCard
              badge={t("session.qnaTypes.concept")}
              badgeColor="bg-[#6b7280]"
              title={t("landing.qna.sampleQ1")}
              text={t("landing.qna.sampleA1")}
            />
            <MockCard
              badge={t("session.qnaTypes.application")}
              badgeColor="bg-[#6b7280]"
              title={t("landing.qna.sampleQ2")}
              text={t("landing.qna.sampleA2")}
              animationDelay="0.1s"
            />
          </div>
        </MockSessionWindow>
      </div>

      <FeatureDescription
        title={t("landing.qna.title")}
        description={<Trans t={t} i18nKey="landing.qna.desc" />}
      >
        <CheckList itemKeys={["landing.qna.point1", "landing.qna.point2", "landing.qna.point3"]} />
      </FeatureDescription>
    </FeatureRow>
  );
}

function FeatureRow({
  align,
  children,
}: {
  align: "items-center" | "items-stretch";
  children: ReactNode;
}) {
  return (
    <div className="mb-32">
      <div className={`grid md:grid-cols-2 gap-16 ${align}`}>{children}</div>
    </div>
  );
}

function FeatureDescription({
  title,
  description,
  children,
}: {
  title: ReactNode;
  description: ReactNode;
  children: ReactNode;
}) {
  return (
    <div>
      <h3 className="text-[2.5rem] leading-[1.3] mb-6 text-[#1F2937]" style={{ fontWeight: 700 }}>
        {title}
      </h3>
      <p className="text-[1.125rem] leading-[1.8] text-[#6B7280] mb-8">{description}</p>
      {children}
    </div>
  );
}

function CheckList({ itemKeys }: { itemKeys: ParseKeys[] }) {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      {itemKeys.map((key) => (
        <div key={key} className="flex items-start gap-3">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
            <Check className="w-4 h-4 text-white" />
          </div>
          <span className="text-[1.125rem] text-[#4B5563]">{t(key)}</span>
        </div>
      ))}
    </div>
  );
}

// 세션 화면을 흉내 낸 회색 창. 요약 소개만 머리 여백이 더 넓음
function MockSessionWindow({
  fullHeight = false,
  spaciousHeader = false,
  children,
}: {
  fullHeight?: boolean;
  spaciousHeader?: boolean;
  children: ReactNode;
}) {
  return (
    <div className={cn("bg-[rgb(246,246,246)] rounded-2xl p-8 shadow-2xl", fullHeight && "h-full")}>
      <div
        className={
          spaciousHeader ? "flex items-center gap-2 mb-6" : "flex items-center justify-between mb-4"
        }
      >
        <span className="ml-auto text-[#9CA3AF] text-sm">LiveNote Session</span>
      </div>
      {children}
    </div>
  );
}

function MockCard({
  badge,
  badgeColor,
  title,
  text,
  animationDelay,
}: {
  badge: string;
  badgeColor: string;
  title: string;
  text: string;
  animationDelay?: string;
}) {
  return (
    <div
      className="border rounded-lg p-6 bg-white flex-1 opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col"
      style={animationDelay ? { animationDelay } : undefined}
    >
      <div className="flex items-start justify-between mb-3">
        <span
          className={`px-2 py-1 ${badgeColor} text-xs text-[rgb(255,255,255)] rounded flex-shrink-0`}
        >
          {badge}
        </span>
      </div>
      <div className="mb-3">
        <p className="font-medium text-[#1F2937]">{title}</p>
      </div>
      <div className="flex-1 overflow-hidden">
        <p className="text-sm text-muted-foreground line-clamp-2">{text}</p>
      </div>
    </div>
  );
}
