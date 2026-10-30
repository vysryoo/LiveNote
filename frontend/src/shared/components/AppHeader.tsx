import type { ReactNode } from "react";
import logoImage from "@/assets/logo.png";

type AppHeaderProps = {
  opaque?: boolean;
  children: ReactNode;
};

/**
 * 화면 상단 헤더 틀을 표시한다. 글자 크기는 화면 너비에 따라 14~18px 사이로 바뀐다.
 *
 * @param props.opaque 불투명 배경 여부. 기본은 반투명 흐림 배경
 * @param props.children 헤더 내용
 */
export function AppHeader({ opaque = false, children }: AppHeaderProps) {
  return (
    <header
      className={`border-b shadow-lg ${opaque ? "bg-white" : "bg-white/80 backdrop-blur-sm"}`}
    >
      <div className="px-[3%] py-[0.4%]" style={{ fontSize: "clamp(14px, 1.2vw, 18px)" }}>
        {children}
      </div>
    </header>
  );
}

/**
 * LiveNote 로고 이미지를 표시한다. 높이는 글자 크기의 3배다.
 */
export function AppLogo() {
  return <img src={logoImage} alt="LiveNote" style={{ height: "3em" }} />;
}
