import { useOutletContext } from "react-router";
import type { Lecture, UserView } from "./services/ports";

export type LegacyAppContext = {
  user: UserView | null;
  initializing: boolean;
  lectures: Lecture[];
  lecturesLoading: boolean;
  openLoginModal: () => void;
  openNewLectureModal: () => void;
  handleSignup: (data: {
    loginId: string;
    email: string;
    password: string;
    name: string;
  }) => Promise<void>;
  handleLogout: () => Promise<void>;
  handleDeleteSession: (sessionId: number) => void;
  handleRenameSession: (sessionId: number, newName: string) => Promise<void>;
  handleEndSession: (lectureId: number, sessionName: string) => Promise<void>;
  handleSettings: (data: {
    language: string;
    currentPassword?: string;
    newPassword?: string;
  }) => Promise<void>;
};

export function useLegacyApp(): LegacyAppContext {
  return useOutletContext<LegacyAppContext>();
}
