// 원과 네 꼭짓점 별 모양을 번갈아 오가며 회전함
const CIRCLE_PATH =
  "M0,-30 C16.5,-30 30,-16.5 30,0 C30,16.5 16.5,30 0,30 C-16.5,30 -30,16.5 -30,0 C-30,-16.5 -16.5,-30 0,-30 Z";
const STAR_PATH =
  "M0,-45 C5,-45 45,-5 45,0 C45,5 5,45 0,45 C-5,45 -45,5 -45,0 C-45,-5 -5,-45 0,-45 Z";
const MORPH_VALUES = [CIRCLE_PATH, STAR_PATH, CIRCLE_PATH, STAR_PATH, CIRCLE_PATH].join(";");

/**
 * 생성 중임을 알리는 그라데이션 로딩 아이콘을 표시한다.
 *
 * @param props.id SVG 그라데이션 ID. 한 화면에 여러 개를 그릴 때 서로 겹치지 않아야 함
 */
export function AnimatedLoaderIcon({ id }: { id: string }) {
  return (
    <svg viewBox="0 0 120 120" width="20" height="20" xmlns="http://www.w3.org/2000/svg">
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
          <animate attributeName="d" dur="6s" repeatCount="indefinite" values={MORPH_VALUES} />
        </path>
      </g>
    </svg>
  );
}
