import { useCallback, useEffect, useState } from "react";

/**
 * Load data with a stable loading/error/reload contract.
 *
 * `loader` receives no arguments and returns the resolved data. It should be
 * memoized (useCallback) when it depends on component state.
 */
export function useAsyncData(loader, { fallbackError = "Could not load data." } = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await loader());
    } catch {
      setError(fallbackError);
    } finally {
      setLoading(false);
    }
  }, [fallbackError, loader]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { data, loading, error, reload, setData };
}
