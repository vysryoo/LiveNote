import { useOutletContext } from "react-router";
import type { Lecture } from "./services/ports";

export type LegacyAppContext = {
  lectures: Lecture[];
  lecturesLoading: boolean;
  openNewLectureModal: () => void;
  handleDeleteSession: (sessionId: number) => void;
  handleRenameSession: (sessionId: number, newName: string) => Promise<void>;
  handleEndSession: (lectureId: number, sessionName: string) => Promise<void>;
};

export function useLegacyApp(): LegacyAppContext {
  return useOutletContext<LegacyAppContext>();
}
