import React from "react";

export function AppProviders({ children }: { children: React.ReactNode }): React.JSX.Element {
  return <React.StrictMode>{children}</React.StrictMode>;
}
