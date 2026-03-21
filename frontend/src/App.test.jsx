import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import { vi } from 'vitest';
import App from './App';
import userEvent from '@testing-library/user-event';

// --- MOCKS ---

vi.mock('@twa-dev/sdk', () => ({
    default: {
        ready: vi.fn(),
        initDataUnsafe: { user: { id: 1, first_name: 'Test User' } },
    },
}));

vi.mock('./components/ConfirmModal', () => ({
    default: ({ isOpen, message, onConfirm, onCancel }) =>
        isOpen ? (
            <div data-testid="confirm-modal">
                <p>{message}</p>
                <button onClick={onConfirm}>Подтвердить</button>
                <button onClick={onCancel}>Отменить</button>
            </div>
        ) : null,
}));

vi.mock('./components/Toast', () => ({
    default: ({ id, message, type, duration, onClose }) => {
        setTimeout(() => onClose(id), duration);
        return (
            <div data-testid={`toast-${type}`}>
                <span>{message}</span>
                <button onClick={() => onClose(id)}>×</button>
            </div>
        );
    },
}));

vi.mock('react-swipeable', () => ({
    useSwipeable: () => ({
        onMouseDown: vi.fn(),
        onTouchStart: vi.fn(),
    })
}));

// --- TEST SUITE ---

describe('App Component (unit tests)', () => {
    beforeEach(() => {
        Object.defineProperty(window, 'location', {
            value: { search: '?test_mode=true&telegram_id=1' },
            writable: true,
        });

        global.fetch = vi.fn((url, options) => {
            const method = options?.method || 'GET';

            if (url.includes('/user/')) {
                return Promise.resolve({ ok: true, json: () => Promise.resolve({ id: 1, first_name: 'Test User' }) });
            }

            if (url.includes('/languages')) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve([
                        { code: 'en', name: 'English' },
                        { code: 'es', name: 'Spanish' },
                    ]),
                });
            }

            if (url.includes('/decks/1') && method === 'GET') {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve([
                        { id: 1, name: 'Default Deck', is_language_deck: false },
                        {
                            id: 2,
                            name: 'Lang Deck',
                            is_language_deck: true,
                            source_lang: 'en',
                            target_lang: 'es',
                        },
                    ]),
                });
            }

            if (url.includes('/decks') && method === 'POST') {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({
                        id: 3,
                        name: 'Test Deck',
                        is_language_deck: false,
                        source_lang: null,
                        target_lang: null,
                    }),
                });
            }

            if (url.includes('/cards/1') && method === 'GET') {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve([
                        { id: 1, term: 'Term 1', definition: 'Definition 1' },
                        { id: 2, term: 'Term 2', definition: 'Definition 2' }
                    ]),
                });
            }

            if (url.includes('/lang_cards/2') && method === 'GET') {
                return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
            }

            if (url.includes('/translate')) {
                return Promise.resolve({ ok: true, json: () => Promise.resolve({ translatedText: 'hola' }) });
            }

            if (url.includes('/cards/') && method === 'PUT') {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({ id: 1, term: 'Term 1 updated', definition: 'Def updated' }),
                });
            }

            if (url.includes('/cards/') && method === 'POST') {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({
                        id: 4,
                        term: 'New Term',
                        definition: 'New Definition'
                    }),
                });
            }

            if (url.includes('/cards/') && method === 'DELETE') {
                return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
            }

            if (url.includes('/decks/1') && method === 'DELETE') {
                return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
            }

            return Promise.reject(new Error(`Unhandled fetch for ${url}`));
        });
    });

    afterEach(() => {
        vi.clearAllMocks();
        vi.useRealTimers();
    });

    const renderApp = async () => {
        await act(async () => {
            render(<App />);
        });
    };

    it('renders the deck creation form', async () => {
        await renderApp();
        expect(screen.getByText(/Создать новую колоду/i)).toBeInTheDocument();
    });

    it('toggles language deck checkbox and shows language selectors', async () => {
        await renderApp();
        await userEvent.click(screen.getByLabelText(/Языковая колода/i));
        await waitFor(() => {
            expect(screen.getByText(/Выберите исходный язык/i)).toBeInTheDocument();
            expect(screen.getByText(/Выберите целевой язык/i)).toBeInTheDocument();
        });
    });

    it('creates a new deck successfully', async () => {
        await renderApp();
        const input = screen.getByPlaceholderText(/Введите название/i);
        const button = screen.getByRole('button', { name: /Создать колоду/i });
        await userEvent.type(input, 'Test Deck');
        await userEvent.click(button);
        await waitFor(() => {
            expect(screen.getByTestId('toast-success')).toBeInTheDocument();
        });
    });

    it('shows warning toast when deck name is empty', async () => {
        await renderApp();
        await userEvent.click(screen.getByRole('button', { name: /Создать колоду/i }));
        await waitFor(() => {
            expect(screen.getByTestId('toast-warning')).toBeInTheDocument();
        });
    });

    it('toggles show decks and displays deck list', async () => {
        await renderApp();
        const toggleButton = screen.getByRole('button', { name: /Показать/i });
        await userEvent.click(toggleButton);
        await waitFor(() => {
            expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
        });
    });

    it('opens card modal when clicking edit button on a deck', async () => {
        await renderApp();
        const toggleButton = screen.getByRole('button', { name: /Показать/i });
        await userEvent.click(toggleButton);
        await waitFor(() => {
            expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
        });
        const editButtons = screen.getAllByRole('button', { name: /Редактировать карточки/i });
        await userEvent.click(editButtons[0]);
        await waitFor(() => {
            expect(screen.getByText(/Редактировать карточки/i)).toBeInTheDocument();
            expect(screen.getAllByPlaceholderText(/Термин/i).length).toBeGreaterThan(0);
        });
    });

    it('removes a card row when clicking ×', async () => {
        await renderApp();
        await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
        await waitFor(() => screen.getByText(/Default Deck/i));
        const editButtons = screen.getAllByRole('button', { name: /Редактировать карточки/i });
        await userEvent.click(editButtons[0]);
        await waitFor(() => {
            expect(screen.getByText(/Редактировать карточки/i)).toBeInTheDocument();
        });
        await userEvent.click(screen.getByText('+'));
        const rows = screen.getAllByPlaceholderText('Термин');
        const removeButtons = screen.getAllByText('×');
        await userEvent.click(removeButtons[0]);
        await waitFor(() => {
            expect(screen.queryAllByPlaceholderText('Термин').length).toBeLessThan(rows.length);
        });
    });

    it('saves edited cards', async () => {
        await renderApp();
        await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
        await waitFor(() => screen.getByText(/Default Deck/i));
        const editButtons = screen.getAllByRole('button', { name: /Редактировать карточки/i });
        await userEvent.click(editButtons[0]);
        const termInputs = screen.getAllByPlaceholderText('Термин');
        const firstTermInput = termInputs[0];

        await userEvent.clear(firstTermInput);
        await userEvent.type(firstTermInput, 'Updated term');
        await userEvent.click(screen.getByText(/Сохранить/i));
        await waitFor(() => {
            expect(screen.getByTestId('toast-success')).toBeInTheDocument();
        });
    });

    it('auto-translates a word on blur for language deck', async () => {
        await renderApp();
        await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
        await waitFor(() => {
            expect(screen.getByText('Lang Deck')).toBeInTheDocument();
        });
        const editButtons = screen.getAllByRole('button', { name: /Редактировать карточки/i });
        await userEvent.click(editButtons[1]);
        await waitFor(() => {
            expect(screen.getByText(/Редактировать карточки/i)).toBeInTheDocument();
        });
        await userEvent.click(screen.getByText('+'));
        const wordInput = screen.getByPlaceholderText('Слово');
        await userEvent.clear(wordInput);
        await userEvent.type(wordInput, 'hello');
        fireEvent.blur(wordInput);
        await waitFor(() => {
            expect(screen.getByDisplayValue('hola')).toBeInTheDocument();
        });
    });

    it('deletes a deck with confirmation', async () => {
        await renderApp();
        await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
        await waitFor(() => {
            expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
        });
        const deleteButtons = screen.getAllByRole('button', { name: /Удалить колоду/i });
        await userEvent.click(deleteButtons[0]);
        await waitFor(() => {
            expect(screen.getByTestId('confirm-modal')).toBeInTheDocument();
        });
        await userEvent.click(screen.getByText(/Подтвердить/i));
        await waitFor(() => {
            expect(screen.getByTestId('toast-success')).toBeInTheDocument();
        });
    });

    it('starts study mode when clicking study button', async () => {
        await renderApp();
        await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
        await waitFor(() => {
            expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
        });
        const studyButtons = screen.getAllByRole('button', { name: /Учить карточки/i });
        await userEvent.click(studyButtons[0]);
        await waitFor(() => {
            expect(screen.getByText(/Изучение карточек/i)).toBeInTheDocument();
            expect(screen.getByText(/Term 1/i)).toBeInTheDocument();
        });
    });

    describe('Card editing validations', () => {
        it('shows warning toast when trying to save cards with empty fields', async () => {
            await renderApp();

            await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
            await waitFor(() => {
                expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
            });

            const editButtons = screen.getAllByRole('button', { name: /Редактировать карточки/i });
            await userEvent.click(editButtons[0]);

            await waitFor(() => {
                expect(screen.getByText(/Редактировать карточки/i)).toBeInTheDocument();
            });

            await userEvent.click(screen.getByText('+'));
            await userEvent.click(screen.getByText(/Сохранить/i));

            await waitFor(() => {
                expect(screen.getByTestId('toast-warning')).toBeInTheDocument();
            });
        });

        it('closes modal when clicking close button', async () => {
            await renderApp();

            await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
            await waitFor(() => {
                expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
            });

            const editButtons = screen.getAllByRole('button', { name: /Редактировать карточки/i });
            await userEvent.click(editButtons[0]);

            await waitFor(() => {
                expect(screen.getByText(/Редактировать карточки/i)).toBeInTheDocument();
            });

            await userEvent.click(screen.getByText(/Закрыть/i));

            await waitFor(() => {
                expect(screen.queryByText(/Редактировать карточки/i)).not.toBeInTheDocument();
            });
        });
    });

    describe('Study mode interactions', () => {
        const setupStudyMode = async () => {
            await renderApp();

            await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
            await waitFor(() => {
                expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
            });

            const studyButtons = screen.getAllByRole('button', { name: /Учить карточки/i });
            await userEvent.click(studyButtons[0]);

            await waitFor(() => {
                expect(screen.getByText(/Изучение карточек/i)).toBeInTheDocument();
            });
        };

        it('displays study mode UI correctly', async () => {
            await setupStudyMode();

            expect(screen.getByText(/Изучение карточек/i)).toBeInTheDocument();
            expect(screen.getByText(/1 из 2/)).toBeInTheDocument();
            expect(screen.getByText(/Term 1/i)).toBeInTheDocument();
            expect(screen.getByText(/Свайп влево — не запомнил, вправо — запомнил/i)).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /Завершить/i })).toBeInTheDocument();
        });

        it('flips card to show definition on click', async () => {
            await setupStudyMode();

            const card = screen.getByText(/Term 1/i).closest('.study-card');
            await userEvent.click(card);

            await waitFor(() => {
                expect(screen.getByText(/Definition 1/i)).toBeInTheDocument();
            });

            expect(card).toHaveClass('flipped');
        });

        it('flips card back to term on second click', async () => {
            await setupStudyMode();

            const card = screen.getByText(/Term 1/i).closest('.study-card');

            await userEvent.click(card);
            await waitFor(() => {
                expect(screen.getByText(/Definition 1/i)).toBeInTheDocument();
            });

            await userEvent.click(card);
            await waitFor(() => {
                expect(screen.getByText(/Term 1/i)).toBeInTheDocument();
            });
        });

        it('exits study mode when clicking "Завершить" button', async () => {
            await setupStudyMode();

            await userEvent.click(screen.getByRole('button', { name: /Завершить/i }));

            await waitFor(() => {
                expect(screen.getByText(/Создать новую колоду/i)).toBeInTheDocument();
                expect(screen.queryByText(/Изучение карточек/i)).not.toBeInTheDocument();
            });
        });

        it('shows message when deck has no cards', async () => {
            const originalFetch = global.fetch;
            global.fetch = vi.fn((url) => {
                if (url.includes('/cards/1')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve([]),
                    });
                }
                if (url.includes('/user/')) {
                    return Promise.resolve({ ok: true, json: () => Promise.resolve({ id: 1, first_name: 'Test User' }) });
                }
                if (url.includes('/decks/1')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve([
                            { id: 1, name: 'Empty Deck', is_language_deck: false }
                        ]),
                    });
                }
                return Promise.reject(new Error(`Unhandled fetch for ${url}`));
            });

            await renderApp();

            await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
            await waitFor(() => {
                expect(screen.getByText(/Empty Deck/i)).toBeInTheDocument();
            });

            const studyButtons = screen.getAllByRole('button', { name: /Учить карточки/i });
            await userEvent.click(studyButtons[0]);

            await waitFor(() => {
                expect(screen.getByText(/Добавьте карточки, чтобы начать изучение/i)).toBeInTheDocument();
            });

            global.fetch = originalFetch;
        });
    });

    describe('Study mode edge cases', () => {
        it('shows message when no cards in deck', async () => {
            const originalFetch = global.fetch;
            global.fetch = vi.fn((url, options) => {
                if (url.includes('/cards/1')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve([]),
                    });
                }
                // Для остальных запросов используем оригинальный мок из beforeEach
                if (url.includes('/user/')) {
                    return Promise.resolve({ ok: true, json: () => Promise.resolve({ id: 1, first_name: 'Test User' }) });
                }
                if (url.includes('/decks/1')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve([
                            { id: 1, name: 'Default Deck', is_language_deck: false }
                        ]),
                    });
                }
                return Promise.reject(new Error(`Unhandled fetch for ${url}`));
            });

            await renderApp();

            await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
            await waitFor(() => {
                expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
            });

            const studyButtons = screen.getAllByRole('button', { name: /Учить карточки/i });
            await userEvent.click(studyButtons[0]);

            await waitFor(() => {
                expect(screen.getByText(/Добавьте карточки, чтобы начать изучение/i)).toBeInTheDocument();
            });

            global.fetch = originalFetch;
        });
    });

    describe('saveCards function scenarios', () => {
        it('creates new cards successfully', async () => {
            await renderApp();

            await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
            await waitFor(() => {
                expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
            });

            const editButtons = screen.getAllByRole('button', { name: /Редактировать карточки/i });
            await userEvent.click(editButtons[0]);

            await waitFor(() => {
                expect(screen.getByText(/Редактировать карточки/i)).toBeInTheDocument();
            });

            await userEvent.click(screen.getByText('+'));

            const termInputs = screen.getAllByPlaceholderText('Термин');
            const defInputs = screen.getAllByPlaceholderText('Определение');

            await userEvent.type(termInputs[termInputs.length - 1], 'New Term');
            await userEvent.type(defInputs[defInputs.length - 1], 'New Definition');

            await userEvent.click(screen.getByText(/Сохранить/i));

            await waitFor(() => {
                expect(screen.getByTestId('toast-success')).toBeInTheDocument();
            });
        });

        it('updates existing cards successfully', async () => {
            await renderApp();

            await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
            await waitFor(() => {
                expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
            });

            const editButtons = screen.getAllByRole('button', { name: /Редактировать карточки/i });
            await userEvent.click(editButtons[0]);

            await waitFor(() => {
                expect(screen.getByText(/Редактировать карточки/i)).toBeInTheDocument();
            });

            const termInput = screen.getByDisplayValue('Term 1');
            await userEvent.clear(termInput);
            await userEvent.type(termInput, 'Updated Term');

            await userEvent.click(screen.getByText(/Сохранить/i));

            await waitFor(() => {
                expect(screen.getByTestId('toast-success')).toBeInTheDocument();
            });
        });
    });
});