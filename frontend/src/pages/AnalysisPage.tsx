import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiFetch, apiPost } from '../api/client';

interface Prompt {
  id: string;
  text: string;
  created_at: string;
}

interface Run {
  id: string;
  prompt_id: string;
  document_filename: string;
  model: string;
  output: string | null;
  status: string;
  error_message: string | null;
  duration_ms: number | null;
  created_at: string;
  prompt_text: string;
}

function displayName(filename: string): string {
  return filename.replace(/^\d{8}_\d{6}_/, '');
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

export default function AnalysisPage() {
  const { filename } = useParams<{ filename: string }>();
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [selectedPromptId, setSelectedPromptId] = useState<string>('');
  const [promptText, setPromptText] = useState('');
  const [runs, setRuns] = useState<Run[]>([]);
  const [activeRun, setActiveRun] = useState<Run | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPrompts();
    loadRuns();
  }, [filename]);

  async function loadPrompts() {
    const result = await apiFetch<{ prompts: Prompt[] }>('/api/v1/prompts');
    if (result.ok) {
      setPrompts(result.data.prompts);
      if (result.data.prompts.length > 0 && !selectedPromptId) {
        setSelectedPromptId(result.data.prompts[0].id);
        setPromptText(result.data.prompts[0].text);
      }
    }
  }

  async function loadRuns() {
    if (!filename) return;
    const result = await apiFetch<{ runs: Run[] }>(`/api/v1/runs?document_filename=${encodeURIComponent(filename)}`);
    if (result.ok) {
      setRuns(result.data.runs);
    }
  }

  function handlePromptSelect(promptId: string) {
    setSelectedPromptId(promptId);
    const prompt = prompts.find(p => p.id === promptId);
    if (prompt) setPromptText(prompt.text);
  }

  async function handleRun() {
    if (!filename) return;
    setRunning(true);
    setError(null);
    setActiveRun(null);

    // If the prompt text differs from the selected prompt, save as new
    let promptId = selectedPromptId;
    const selectedPrompt = prompts.find(p => p.id === selectedPromptId);
    if (!selectedPrompt || selectedPrompt.text !== promptText) {
      const createResult = await apiPost<Prompt>('/api/v1/prompts', { text: promptText });
      if (!createResult.ok) {
        setError(createResult.error);
        setRunning(false);
        return;
      }
      promptId = createResult.data.id;
      setSelectedPromptId(promptId);
      await loadPrompts();
    }

    const result = await apiPost<Run>('/api/v1/analyse', {
      prompt_id: promptId,
      document_filename: filename,
    });

    if (result.ok) {
      setActiveRun(result.data);
    } else {
      setError(result.error);
    }

    await loadRuns();
    setRunning(false);
  }

  function handleReplay(run: Run) {
    setActiveRun(run);
    setPromptText(run.prompt_text);
    const prompt = prompts.find(p => p.id === run.prompt_id);
    if (prompt) setSelectedPromptId(prompt.id);
  }

  return (
    <div className="analysis-page">
      <header className="analysis-header">
        <Link to="/" className="back-link">&larr; Back</Link>
        <h1 className="analysis-title">
          <span className="analysis-label">Analysing</span>
          {filename ? displayName(filename) : ''}
        </h1>
      </header>

      <div className="analysis-layout">
        {/* Left: Prompt editor */}
        <section className="analysis-prompt">
          <div className="prompt-controls">
            <label className="prompt-label">Prompt</label>
            <select
              className="prompt-select"
              value={selectedPromptId}
              onChange={e => handlePromptSelect(e.target.value)}
            >
              {prompts.map(p => (
                <option key={p.id} value={p.id}>
                  {p.text.slice(0, 60)}...
                </option>
              ))}
            </select>
          </div>
          <textarea
            className="prompt-editor"
            value={promptText}
            onChange={e => setPromptText(e.target.value)}
            spellCheck={false}
          />
          <button
            className="run-btn"
            onClick={handleRun}
            disabled={running || !promptText.trim()}
          >
            {running ? 'Running...' : 'Run Analysis'}
          </button>
          {error && <p className="analysis-error">{error}</p>}
        </section>

        {/* Right: Output */}
        <section className="analysis-output">
          <label className="output-label">Output</label>
          {running && <p className="output-status">Analysing document...</p>}
          {activeRun && activeRun.status === 'complete' && (
            <div className="output-meta">
              <span>{activeRun.model}</span>
              {activeRun.duration_ms && <span>{formatDuration(activeRun.duration_ms)}</span>}
            </div>
          )}
          {activeRun && activeRun.status === 'error' && (
            <p className="analysis-error">{activeRun.error_message}</p>
          )}
          <pre className="output-content">
            {activeRun?.output
              ? (() => {
                  try { return JSON.stringify(JSON.parse(activeRun.output), null, 2); }
                  catch { return activeRun.output; }
                })()
              : running ? '' : 'Run an analysis to see output here.'}
          </pre>
        </section>
      </div>

      {/* Run history */}
      {runs.length > 0 && (
        <section className="run-history">
          <label className="history-label">Run History</label>
          <ul className="history-list">
            {runs.map(r => (
              <li
                key={r.id}
                className={`history-item ${activeRun?.id === r.id ? 'active' : ''}`}
                onClick={() => handleReplay(r)}
              >
                <span className={`history-status ${r.status}`}>{r.status}</span>
                <span className="history-prompt">{r.prompt_text.slice(0, 50)}...</span>
                <span className="history-meta">
                  {formatTime(r.created_at)}
                  {r.duration_ms && ` \u00b7 ${formatDuration(r.duration_ms)}`}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
