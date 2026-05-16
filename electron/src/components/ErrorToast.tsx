import { useEffect } from 'react';
import { useAppStore } from '../store/appStore';

export function ErrorToast() {
  const { error, setError } = useAppStore();

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 8000);
      return () => clearTimeout(timer);
    }
  }, [error, setError]);

  if (!error) return null;

  return (
    <div className="error-toast">
      <div className="error-toast-icon">⚠️</div>
      <div className="error-toast-message">{error}</div>
      <button className="error-toast-close" onClick={() => setError(null)}>×</button>
    </div>
  );
}
