import { createContext, useContext, ReactNode } from "react";
import { useVersionCheck, type VersionCheckResult } from "@/hooks/useVersionCheck";

const VersionContext = createContext<VersionCheckResult | undefined>(undefined);

export function VersionProvider({ children }: { children: ReactNode }) {
  const result = useVersionCheck("win");
  return (
    <VersionContext.Provider value={result}>{children}</VersionContext.Provider>
  );
}

export function useVersion() {
  const ctx = useContext(VersionContext);
  if (ctx === undefined) {
    throw new Error("useVersion must be used within VersionProvider");
  }
  return ctx;
}
