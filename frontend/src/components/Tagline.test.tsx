import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Tagline from './Tagline';

describe('Tagline', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('shows loading state initially', () => {
    vi.spyOn(global, 'fetch').mockImplementation(
      () => new Promise(() => {}),
    );

    render(<Tagline />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays the tagline on success', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Mapping Business Resilience.' }),
    } as Response);

    render(<Tagline />);

    await waitFor(() => {
      expect(screen.getByText('Mapping Business Resilience.')).toBeInTheDocument();
    });
  });

  it('displays an error on fetch failure', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('Network error'));

    render(<Tagline />);

    await waitFor(() => {
      expect(screen.getByText('Error: Network error')).toBeInTheDocument();
    });
  });

  it('displays an error on non-ok response', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    } as Response);

    render(<Tagline />);

    await waitFor(() => {
      expect(screen.getByText('Error: HTTP 500: Internal Server Error')).toBeInTheDocument();
    });
  });
});
