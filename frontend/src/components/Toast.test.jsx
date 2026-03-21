import { render, screen, fireEvent, act } from '@testing-library/react';
import { vi } from 'vitest';
import Toast from './Toast.jsx';

vi.mock('./Toast.css', () => ({}));

describe('Toast', () => {
    const mockOnClose = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('renders correctly', () => {
        render(<Toast id={1} message="Test" onClose={mockOnClose} />);
        expect(screen.getByText('Test')).toBeInTheDocument();
        expect(screen.getByText('×')).toBeInTheDocument();
    });

    it('handles different types', () => {
        const { rerender } = render(<Toast id={1} message="Test" type="success" onClose={mockOnClose} />);
        expect(screen.getByText('Test').parentElement).toHaveClass('toast-success');

        rerender(<Toast id={1} message="Test" type="error" onClose={mockOnClose} />);
        expect(screen.getByText('Test').parentElement).toHaveClass('toast-error');
    });

    it('closes after duration', () => {
        render(<Toast id={1} message="Test" duration={1000} onClose={mockOnClose} />);
        act(() => vi.advanceTimersByTime(1000));
        expect(mockOnClose).toHaveBeenCalledWith(1);
    });

    it('closes on button click', () => {
        render(<Toast id={1} message="Test" onClose={mockOnClose} />);
        fireEvent.click(screen.getByRole('button'));
        expect(mockOnClose).toHaveBeenCalledWith(1);
    });
});