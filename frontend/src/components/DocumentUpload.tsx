import { useEffect, useRef, useState } from 'react';
import { apiDelete, apiFetch, apiUpload } from '../api/client';

interface FileInfo {
  filename: string;
  size: number;
  uploaded_at: string;
}

interface FilesResponse {
  files: FileInfo[];
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function displayName(filename: string): string {
  return filename.replace(/^\d{8}_\d{6}_/, '');
}

function fileExtension(filename: string): string {
  const dot = filename.lastIndexOf('.');
  return dot >= 0 ? filename.slice(dot + 1).toUpperCase() : '';
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

const FILE_ICON = (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M10.5 1.5H4.5C3.67157 1.5 3 2.17157 3 3V15C3 15.8284 3.67157 16.5 4.5 16.5H13.5C14.3284 16.5 15 15.8284 15 15V6L10.5 1.5Z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M10.5 1.5V6H15" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export default function DocumentUpload() {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function loadFiles() {
    const result = await apiFetch<FilesResponse>('/api/v1/documents');
    if (result.ok) {
      setFiles(result.data.files);
    }
  }

  useEffect(() => {
    loadFiles();
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    const result = await apiUpload('/api/v1/documents', file);
    if (!result.ok) {
      setError(result.error);
    }

    await loadFiles();
    setUploading(false);

    if (inputRef.current) inputRef.current.value = '';
  }

  async function handleDelete(filename: string) {
    setError(null);
    const result = await apiDelete(`/api/v1/documents/${encodeURIComponent(filename)}`);
    if (!result.ok) {
      setError(result.error);
    }
    await loadFiles();
  }

  const acceptTypes = '.pdf,.docx,.doc,.txt,.csv,.xlsx,.xls,.md,.rtf';

  return (
    <div className="doc-upload">
      <button
        className="upload-btn"
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        aria-label="Upload document"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10 2L10 14M10 2L6 6M10 2L14 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M3 12V15C3 16.1046 3.89543 17 5 17H15C16.1046 17 17 16.1046 17 15V12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        {uploading ? 'Uploading...' : 'Upload'}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={acceptTypes}
        onChange={handleUpload}
        hidden
      />

      {error && <p className="upload-error">{error}</p>}

      {files.length === 0 ? (
        <p className="upload-empty">No documents yet</p>
      ) : (
        <ul className="file-list">
          {files.map((f) => (
            <li key={f.filename} className="file-item">
              <div className="file-icon">{FILE_ICON}</div>
              <div className="file-info">
                <span className="file-name" title={displayName(f.filename)}>
                  {displayName(f.filename)}
                </span>
                <span className="file-meta">
                  <span className="file-ext">{fileExtension(f.filename)}</span>
                  <span className="file-sep">&middot;</span>
                  <span>{formatSize(f.size)}</span>
                  <span className="file-sep">&middot;</span>
                  <span>{formatDate(f.uploaded_at)}</span>
                </span>
              </div>
              <button
                className="file-delete"
                onClick={() => handleDelete(f.filename)}
                aria-label={`Delete ${displayName(f.filename)}`}
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 3L11 11M3 11L11 3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
                </svg>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
