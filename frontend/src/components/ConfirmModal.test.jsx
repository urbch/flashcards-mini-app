import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import ConfirmModal from './ConfirmModal.jsx';

vi.mock('./ConfirmModal.css', () => ({}));

describe('ConfirmModal', () => {
    const mockOnConfirm = vi.fn();
    const mockOnCancel = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should not render when isOpen is false', () => {
        const { container } = render(
            <ConfirmModal isOpen={false} message="Test" onConfirm={mockOnConfirm} onCancel={mockOnCancel} />
        );
        expect(container.firstChild).toBeNull();
    });

    it('should render when isOpen is true', () => {
        render(
            <ConfirmModal isOpen={true} message="Test message" onConfirm={mockOnConfirm} onCancel={mockOnCancel} />
        );

        expect(screen.getByText('Test message')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Подтвердить' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Отменить' })).toBeInTheDocument();
    });

    it('should call onConfirm when confirm button is clicked', () => {
        render(
            <ConfirmModal isOpen={true} message="Test" onConfirm={mockOnConfirm} onCancel={mockOnCancel} />
        );

        fireEvent.click(screen.getByRole('button', { name: 'Подтвердить' }));
        expect(mockOnConfirm).toHaveBeenCalledTimes(1);
        expect(mockOnCancel).not.toHaveBeenCalled();
    });

    it('should call onCancel when cancel button is clicked', () => {
        render(
            <ConfirmModal isOpen={true} message="Test" onConfirm={mockOnConfirm} onCancel={mockOnCancel} />
        );

        fireEvent.click(screen.getByRole('button', { name: 'Отменить' }));
        expect(mockOnCancel).toHaveBeenCalledTimes(1);
        expect(mockOnConfirm).not.toHaveBeenCalled();
    });
});