import { LANGUAGE_CODES, LANGUAGE_LABELS, type LanguageCode } from "@/shared/i18n";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";

type LanguageSelectProps = {
  value: LanguageCode;
  onChange: (language: LanguageCode) => void;
};

/**
 * 지원 언어 중 하나를 고르는 선택 상자를 표시한다. 각 언어는 자기 언어로 표기한다.
 *
 * @param props.value 선택된 언어
 * @param props.onChange 다른 언어를 고르면 호출
 */
export function LanguageSelect({ value, onChange }: LanguageSelectProps) {
  return (
    <Select value={value} onValueChange={(next) => onChange(next as LanguageCode)}>
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {LANGUAGE_CODES.map((code) => (
          <SelectItem key={code} value={code}>
            {LANGUAGE_LABELS[code]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
