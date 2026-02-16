import { useEffect, useState } from 'react';
import { apiFetch } from '../api/client';

interface HelloResponse {
  message: string;
}

export default function HelloWorld() {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function fetchHello() {
      const result = await apiFetch<HelloResponse>('/api/v1/hello');
      if (cancelled) return;

      if (result.ok) {
        setMessage(result.data.message);
      } else {
        setError(result.error);
      }
      setLoading(false);
    }

    fetchHello();
    return () => { cancelled = true; };
  }, []);

  if (loading) return <p className="status">Loading...</p>;
  if (error) return <p className="status error">Error: {error}</p>;

  return <h1 className="hello-message">{message}</h1>;
}
