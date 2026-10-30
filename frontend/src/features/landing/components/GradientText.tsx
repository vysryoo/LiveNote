import type { ReactNode } from "react";
import "./GradientText.css";

type GradientTextProps = {
  children: ReactNode;
  colors: string[];
  animationSpeed: number;
};

export function GradientText({ children, colors, animationSpeed }: GradientTextProps) {
  return (
    <div className="animated-gradient-text">
      <div
        className="text-content"
        style={{
          backgroundImage: `linear-gradient(to right, ${colors.join(", ")})`,
          animationDuration: `${animationSpeed}s`,
        }}
      >
        {children}
      </div>
    </div>
  );
}
