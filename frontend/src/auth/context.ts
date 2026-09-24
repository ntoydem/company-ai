import { createContext } from "react";

import type { CurrentUser } from "../api/types";

export interface AuthContextValue {
  user: CurrentUser | null;
  isLoading: boolean;
  setUser: (user: CurrentUser | null) => void;
  signOut: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
