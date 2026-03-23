import { vi } from 'vitest';

vi.mock('react-dom/client', () => ({
    createRoot: vi.fn().mockReturnValue({ render: vi.fn() })
}));

vi.mock('./App', () => ({ default: () => null }));
vi.mock('./index.css', () => ({}));

describe('main', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="root"></div>';
    });

    it('renders without crashing', async () => {
        await import('./main.jsx');
        const { createRoot } = await import('react-dom/client');
        expect(createRoot).toHaveBeenCalledWith(document.getElementById('root'));
    });
});