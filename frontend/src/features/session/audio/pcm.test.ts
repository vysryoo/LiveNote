import { describe, expect, it } from "vitest";
import { resampleLinear, toPcm16 } from "./pcm";

describe("resampleLinear", () => {
  it("샘플레이트가 같으면 원본을 그대로 반환", () => {
    const samples = new Float32Array([0.1, 0.2]);
    expect(resampleLinear(samples, 24000, 24000)).toBe(samples);
  });

  it("48kHz를 24kHz로 줄이면 길이가 절반", () => {
    expect(resampleLinear(new Float32Array(4800), 48000, 24000)).toHaveLength(2400);
  });

  it("늘릴 때 사이 값을 선형 보간", () => {
    expect(Array.from(resampleLinear(new Float32Array([0, 1]), 1, 2))).toEqual([0, 0.5, 1, 1]);
  });
});

describe("toPcm16", () => {
  it("양수는 32767, 음수는 32768 기준으로 변환하고 범위 밖 값은 잘라냄", () => {
    expect(Array.from(toPcm16(new Float32Array([0, 1, -1, 2, -2])))).toEqual([
      0, 32767, -32768, 32767, -32768,
    ]);
  });
});
