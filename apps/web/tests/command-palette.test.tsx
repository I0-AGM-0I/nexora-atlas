import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CommandPalette } from '../src/components/CommandPalette';

describe('CommandPalette Component', () => {
  it('does not render when isOpen is false', () => {
    const handleClose = vi.fn();
    render(
      <MemoryRouter>
        <CommandPalette isOpen={false} onClose={handleClose} />
      </MemoryRouter>
    );

    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('renders modal and options when isOpen is true', () => {
    const handleClose = vi.fn();
    render(
      <MemoryRouter>
        <CommandPalette isOpen={true} onClose={handleClose} />
      </MemoryRouter>
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Type a command/i)).toBeInTheDocument();
    expect(screen.getByText('Overview Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Spend Explorer')).toBeInTheDocument();
  });

  it('filters results based on search input', () => {
    const handleClose = vi.fn();
    render(
      <MemoryRouter>
        <CommandPalette isOpen={true} onClose={handleClose} />
      </MemoryRouter>
    );

    const input = screen.getByPlaceholderText(/Type a command/i);
    fireEvent.change(input, { target: { value: 'Forecast' } });

    expect(screen.getByText('Cost Forecast')).toBeInTheDocument();
    expect(screen.queryByText('Spend Explorer')).toBeNull();
  });

  it('calls onClose when close button is clicked', () => {
    const handleClose = vi.fn();
    render(
      <MemoryRouter>
        <CommandPalette isOpen={true} onClose={handleClose} />
      </MemoryRouter>
    );

    const closeBtn = screen.getByLabelText(/Close command palette/i);
    fireEvent.click(closeBtn);

    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
