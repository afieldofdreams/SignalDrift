import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DocumentUpload from './DocumentUpload';

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('DocumentUpload', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders upload button and empty state', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({ files: [] }),
    } as Response);

    renderWithRouter(<DocumentUpload />);

    expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('No documents yet')).toBeInTheDocument();
    });
  });

  it('displays file list from API with clean names', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        files: [
          { filename: '20260216_120000_report.pdf', size: 2048, uploaded_at: '2026-02-16T12:00:00Z' },
        ],
      }),
    } as Response);

    renderWithRouter(<DocumentUpload />);

    await waitFor(() => {
      expect(screen.getByText('report.pdf')).toBeInTheDocument();
      expect(screen.getByText('2.0 KB')).toBeInTheDocument();
      expect(screen.getByText('PDF')).toBeInTheDocument();
    });
  });

  it('uploads a file and refreshes the list', async () => {
    const user = userEvent.setup();

    const fetchSpy = vi.spyOn(global, 'fetch')
      // Initial list load
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ files: [] }),
      } as Response)
      // Upload response
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ filename: '20260216_test.txt', original_name: 'test.txt', size: 5 }),
      } as Response)
      // Refreshed list
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          files: [{ filename: '20260216_120000_test.txt', size: 5, uploaded_at: '2026-02-16T12:00:00Z' }],
        }),
      } as Response);

    renderWithRouter(<DocumentUpload />);

    await waitFor(() => {
      expect(screen.getByText('No documents yet')).toBeInTheDocument();
    });

    const file = new File(['hello'], 'test.txt', { type: 'text/plain' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText('test.txt')).toBeInTheDocument();
    });

    expect(fetchSpy).toHaveBeenCalledTimes(3);
  });

  it('shows error on upload failure', async () => {
    vi.spyOn(global, 'fetch')
      // Initial list load
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ files: [] }),
      } as Response)
      // Upload fails
      .mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ detail: "File type '.exe' not allowed" }),
      } as Response)
      // Refreshed list (still empty)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ files: [] }),
      } as Response);

    renderWithRouter(<DocumentUpload />);

    await waitFor(() => {
      expect(screen.getByText('No documents yet')).toBeInTheDocument();
    });

    const file = new File(['bad'], 'malware.exe', { type: 'application/octet-stream' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("File type '.exe' not allowed")).toBeInTheDocument();
    });
  });
});
