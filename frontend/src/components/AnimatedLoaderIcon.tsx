import React from "react";

interface AnimatedLoaderIconProps {
  id: string;
}

// 공통 SVG 로딩 아이콘 (회전 + morph 애니메이션)
export function AnimatedLoaderIcon({ id }: AnimatedLoaderIconProps) {
  return (
    <svg
      viewBox="0 0 120 120"
      width="20"
      height="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#63A4FF">
            <animate
              attributeName="stop-color"
              values="#63A4FF;#639BEE;#83EAF1;#3B72DD;#4D82E0;#63A4FF"
              dur="6s"
              repeatCount="indefinite"
            />
          </stop>
          <stop offset="100%" stopColor="#4D82E0">
            <animate
              attributeName="stop-color"
              values="#4D82E0;#3B72DD;#83EAF1;#639BEE;#63A4FF;#4D82E0"
              dur="6s"
              repeatCount="indefinite"
            />
          </stop>
        </linearGradient>
      </defs>
      <g transform="translate(60 60)">
        <animateTransform
          attributeName="transform"
          type="rotate"
          values="0;360;1080;1440;2160"
          keyTimes="0;0.25;0.5;0.75;1"
          dur="6s"
          repeatCount="indefinite"
          additive="sum"
        />
        <path fill={`url(#${id})`}>
          <animate
            attributeName="d"
            dur="6s"
            repeatCount="indefinite"
            values="
              M0,-30 
              C16.5,-30 30,-16.5 30,0 
              C30,16.5 16.5,30 0,30 
              C-16.5,30 -30,16.5 -30,0 
              C-30,-16.5 -16.5,-30 0,-30 
              Z;
          
              M0,-45 
              C5,-45 45,-5 45,0 
              C45,5 5,45 0,45 
              C-5,45 -45,5 -45,0 
              C-45,-5 -5,-45 0,-45 
              Z;
          
              M0,-30 
              C16.5,-30 30,-16.5 30,0 
              C30,16.5 16.5,30 0,30 
              C-16.5,30 -30,16.5 -30,0 
              C-30,-16.5 -16.5,-30 0,-30 
              Z;
          
              M0,-45 
              C5,-45 45,-5 45,0 
              C45,5 5,45 0,45 
              C-5,45 -45,5 -45,0 
              C-45,-5 -5,-45 0,-45 
              Z;
          
              M0,-30 
              C16.5,-30 30,-16.5 30,0 
              C30,16.5 16.5,30 0,30 
              C-16.5,30 -30,16.5 -30,0 
              C-30,-16.5 -16.5,-30 0,-30 
              Z
            "
          />
        </path>
      </g>
    </svg>
  );
}


