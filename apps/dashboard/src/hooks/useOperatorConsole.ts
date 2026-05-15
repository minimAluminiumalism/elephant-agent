import { useCallback, useEffect, useRef, useState } from "react";

import { DashboardLoadAbortedError, loadDashboardSnapshot } from "../lib/dashboardApi";
import type { DashboardSection, InternalDashboardSnapshot } from "../types/dashboard";

const DASHBOARD_CACHE_TTL_MS = 15_000;
const DASHBOARD_STORAGE_TTL_MS = 5 * 60_000;
const DASHBOARD_STORAGE_KEY_PREFIX = "elephant.internalDashboardSnapshot";

type CachedDashboardSnapshot = {
  snapshot: InternalDashboardSnapshot;
  cachedAt: number;
};

const cachedDashboardSnapshots = new Map<DashboardSection, CachedDashboardSnapshot>();
const pendingDashboardLoads = new Map<DashboardSection, Promise<InternalDashboardSnapshot>>();

type DashboardRefreshOptions = {
  silent?: boolean;
};

type DashboardSnapshotState = {
  dashboard: InternalDashboardSnapshot | null;
  loading: boolean;
  error: string | null;
  refresh: (options?: DashboardRefreshOptions) => Promise<void>;
};

function storageKey(section: DashboardSection): string {
  return `${DASHBOARD_STORAGE_KEY_PREFIX}.${section}.v1`;
}

function hydrateDashboardFromSession(section: DashboardSection): CachedDashboardSnapshot | null {
  const cached = cachedDashboardSnapshots.get(section);
  if (cached || typeof window === "undefined") {
    return cached ?? null;
  }
  try {
    const raw = window.sessionStorage.getItem(storageKey(section));
    if (!raw) {
      return null;
    }
    const stored = JSON.parse(raw) as { cachedAt?: unknown; snapshot?: unknown };
    if (typeof stored.cachedAt !== "number" || Date.now() - stored.cachedAt > DASHBOARD_STORAGE_TTL_MS) {
      window.sessionStorage.removeItem(storageKey(section));
      return null;
    }
    if (stored.snapshot && typeof stored.snapshot === "object") {
      const nextCached = {
        cachedAt: stored.cachedAt,
        snapshot: stored.snapshot as InternalDashboardSnapshot,
      };
      cachedDashboardSnapshots.set(section, nextCached);
      return nextCached;
    }
  } catch {
    try {
      window.sessionStorage.removeItem(storageKey(section));
    } catch {
      // Ignore storage cleanup failures; the live request path still works.
    }
  }
  return null;
}

function rememberDashboardSnapshot(section: DashboardSection, nextSnapshot: InternalDashboardSnapshot): InternalDashboardSnapshot {
  const cachedAt = Date.now();
  cachedDashboardSnapshots.set(section, { cachedAt, snapshot: nextSnapshot });
  if (typeof window !== "undefined") {
    try {
      window.sessionStorage.setItem(storageKey(section), JSON.stringify({ cachedAt, snapshot: nextSnapshot }));
    } catch {
      try {
        window.sessionStorage.removeItem(storageKey(section));
      } catch {
        // Ignore storage cleanup failures; the in-memory cache still works.
      }
    }
  }
  return nextSnapshot;
}

function getCachedDashboard(section: DashboardSection): CachedDashboardSnapshot | null {
  return hydrateDashboardFromSession(section);
}

function hasFreshCachedDashboard(section: DashboardSection): boolean {
  const cached = getCachedDashboard(section);
  return Boolean(cached) && Date.now() - (cached?.cachedAt ?? 0) < DASHBOARD_CACHE_TTL_MS;
}

function loadSharedDashboard(section: DashboardSection, force = false): Promise<InternalDashboardSnapshot> {
  const cached = getCachedDashboard(section);
  if (!force && cached && hasFreshCachedDashboard(section)) {
    return Promise.resolve(cached.snapshot);
  }
  const pending = pendingDashboardLoads.get(section);
  if (!force && pending) {
    return pending;
  }

  const nextLoad = loadDashboardSnapshot(section)
    .then((nextSnapshot) => rememberDashboardSnapshot(section, nextSnapshot))
    .finally(() => {
      pendingDashboardLoads.delete(section);
    });
  pendingDashboardLoads.set(section, nextLoad);
  return nextLoad;
}

export function useDashboardSnapshot(section: DashboardSection): DashboardSnapshotState {
  const initialCached = getCachedDashboard(section);
  const [dashboardSnapshot, setDashboardSnapshot] = useState<InternalDashboardSnapshot | null>(initialCached?.snapshot ?? null);
  const [loading, setLoading] = useState(!initialCached);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const runLoad = useCallback((force = false, options: DashboardRefreshOptions = {}) => {
    let active = true;
    const cached = getCachedDashboard(section);
    if (!options.silent) {
      setLoading(!cached);
      setError(null);
      setDashboardSnapshot(cached?.snapshot ?? null);
    }
    const promise = loadSharedDashboard(section, force)
      .then((nextSnapshot) => {
        if (active && mountedRef.current) {
          setDashboardSnapshot(nextSnapshot);
          if (!options.silent) {
            setError(null);
          }
        }
      })
      .catch((nextError) => {
        if (!active || !mountedRef.current || options.silent) {
          return;
        }
        if (nextError instanceof DashboardLoadAbortedError) {
          return;
        }
        setError(nextError instanceof Error ? nextError.message : `Dashboard ${section} data unavailable.`);
      })
      .finally(() => {
        if (active && mountedRef.current && !options.silent) {
          setLoading(false);
        }
      });

    return {
      cancel: () => {
        active = false;
      },
      promise: promise.then(() => undefined),
    };
  }, [section]);

  useEffect(() => {
    mountedRef.current = true;
    const load = runLoad(false);
    return () => {
      mountedRef.current = false;
      load.cancel();
    };
  }, [runLoad]);

  return {
    dashboard: dashboardSnapshot,
    loading,
    error,
    refresh: (options?: DashboardRefreshOptions) => runLoad(true, options).promise,
  };
}
