/**
 * 오디오 샘플을 선형 보간으로 다른 샘플레이트로 변환한다.
 *
 * @param samples 원본 샘플 (-1 ~ 1)
 * @param fromRate 원본 샘플레이트(Hz)
 * @param toRate 목표 샘플레이트(Hz)
 * @returns 변환된 샘플. 두 샘플레이트가 같으면 원본을 그대로 반환
 */
export function resampleLinear(
  samples: Float32Array,
  fromRate: number,
  toRate: number,
): Float32Array {
  if (fromRate === toRate || samples.length === 0) return samples;
  const ratio = toRate / fromRate;
  const output = new Float32Array(Math.round(samples.length * ratio));
  for (let i = 0; i < output.length; i++) {
    const position = i / ratio;
    const lower = Math.floor(position);
    const upper = Math.min(lower + 1, samples.length - 1);
    const fraction = position - lower;
    output[i] = samples[lower] * (1 - fraction) + samples[upper] * fraction;
  }
  return output;
}

/**
 * 부동소수 샘플을 16비트 정수 PCM으로 변환한다. 범위를 넘는 값은 잘라낸다.
 *
 * @param samples 샘플 (-1 ~ 1)
 * @returns 16비트 PCM 샘플
 */
export function toPcm16(samples: Float32Array): Int16Array {
  const pcm = new Int16Array(samples.length);
  for (let i = 0; i < samples.length; i++) {
    const sample = Math.max(-1, Math.min(1, samples[i]));
    pcm[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return pcm;
}
