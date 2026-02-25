import { VersionProvider, useVersion } from "@/contexts/VersionContext";
import { UpgradeRequiredScreen } from "@/components/UpgradeRequiredScreen";

function VersionGateInner({ children }: { children: React.ReactNode }) {
  const { shouldBlock, data } = useVersion();

  if (shouldBlock && data) {
    return (
      <UpgradeRequiredScreen
        minClientVersion={data.minClientVersion}
        downloadUrl={data.downloadUrl}
        onClose={() => window.electronAPI?.close?.()}
      />
    );
  }

  return <>{children}</>;
}

export function VersionGate({ children }: { children: React.ReactNode }) {
  return (
    <VersionProvider>
      <VersionGateInner>{children}</VersionGateInner>
    </VersionProvider>
  );
}
