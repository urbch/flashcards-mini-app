import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import App from './App';

// =========================
// Mocks
// =========================

vi.mock('@twa-dev/sdk', () => ({
    default: {
        ready: vi.fn(),
        initDataUnsafe: {
            user: { id: 1, first_name: 'Test User' },
        },
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
    }),
}));

// =========================
// Mock data
// =========================

const mockUser = { id: 1, first_name: 'Test User' };

const mockLanguages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
];

const mockDecks = [
    { id: 1, name: 'Default Deck', is_language_deck: false },
    {
        id: 2,
        name: 'Lang Deck',
        is_language_deck: true,
        source_lang: 'en',
        target_lang: 'es',
    },
];

const mockCards = [
    { id: 1, term: 'Term 1', definition: 'Definition 1' },
    { id: 2, term: 'Term 2', definition: 'Definition 2' },
];

// =========================
// Fetch factory
// =========================

const createFetchMock = (overrides = {}) =>
    vi.fn((url, options = {}) => {
        const method = options.method || 'GET';

        if (overrides[url]) {
            return overrides[url](url, options);
        }

        if (url.includes('/user/')) {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve(mockUser),
            });
        }

        if (url.includes('/languages')) {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve(mockLanguages),
            });
        }

        if (url.includes('/decks/1') && method === 'GET') {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve(mockDecks),
            });
        }

        if (url.includes('/decks') && method === 'POST') {
            return Promise.resolve({
                ok: true,
                json: () =>
                    Promise.resolve({
                        id: 3,
                        name: 'Test Deck',
                        is_language_deck: false,
                        source_lang: null,
                        target_lang: null,
                    }),
            });
        }

        if (url.includes('/decks/1') && method === 'DELETE') {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve({}),
            });
        }

        if (url.includes('/cards/1') && method === 'GET') {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve(mockCards),
            });
        }

        if (url.includes('/lang_cards/2') && method === 'GET') {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve([]),
            });
        }

        if (url.includes('/translate')) {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ translatedText: 'hola' }),
            });
        }

        if (url.includes('/cards/') && method === 'PUT') {
            return Promise.resolve({
                ok: true,
                json: () =>
                    Promise.resolve({
                        id: 1,
                        term: 'Term 1 updated',
                        definition: 'Def updated',
                    }),
            });
        }

        if (url.includes('/cards/') && method === 'POST') {
            return Promise.resolve({
                ok: true,
                json: () =>
                    Promise.resolve({
                        id: 4,
                        term: 'New Term',
                        definition: 'New Definition',
                    }),
            });
        }

        if (url.includes('/cards/') && method === 'DELETE') {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve({}),
            });
        }

        return Promise.reject(new Error(`Unhandled fetch for ${url} [${method}]`));
    });

// =========================
// Test helpers
// =========================

const renderApp = async () => {
    await act(async () => {
        render(<App />);
    });
};

const openDecksList = async () => {
    await userEvent.click(screen.getByRole('button', { name: /Показать/i }));
    await waitFor(() => {
        expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
    });
};

const openEditModalForDeck = async (index = 0) => {
    await openDecksList();

    const editButtons = screen.getAllByRole('button', {
        name: /Редактировать карточки/i,
    });

    await userEvent.click(editButtons[index]);

    await waitFor(() => {
        expect(screen.getByText(/Редактировать карточки/i)).toBeInTheDocument();
    });
};

const openStudyModeForDeck = async (index = 0) => {
    await openDecksList();

    const studyButtons = screen.getAllByRole('button', {
        name: /Учить карточки/i,
    });

    await userEvent.click(studyButtons[index]);

    await waitFor(() => {
        expect(screen.getByText(/Изучение карточек/i)).toBeInTheDocument();
    });
};

// =========================
// Test suite
// =========================

describe('App Component', () => {
    beforeEach(() => {
        Object.defineProperty(window, 'location', {
            value: { search: '?test_mode=true&telegram_id=1' },
            writable: true,
        });

        global.fetch = createFetchMock();
    });

    afterEach(() => {
        vi.clearAllMocks();
        vi.useRealTimers();
    });

    describe('Initial render and deck creation', () => {
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

        it('shows error toast when createDeck fails', async () => {
            global.fetch = vi.fn((url, options = {}) => {
                if (options.method === 'POST') {
                    return Promise.resolve({
                        ok: false,
                        json: () => Promise.resolve({ error: 'fail' }),
                    });
                }

                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve([]),
                });
            });

            await renderApp();

            await userEvent.type(
                screen.getByPlaceholderText(/Введите название/i),
                'Test'
            );
            await userEvent.click(screen.getByRole('button', { name: /Создать колоду/i }));

            await waitFor(() => {
                expect(screen.getByTestId('toast-error')).toBeInTheDocument();
            });
        });
    });

    describe('Deck list interactions', () => {
        it('toggles deck list visibility and displays decks', async () => {
            await renderApp();

            await openDecksList();

            expect(screen.getByText(/Default Deck/i)).toBeInTheDocument();
            expect(screen.getByText(/Lang Deck/i)).toBeInTheDocument();
        });

        it('deletes a deck with confirmation', async () => {
            await renderApp();

            await openDecksList();

            const deleteButtons = screen.getAllByRole('button', {
                name: /Удалить колоду/i,
            });

            await userEvent.click(deleteButtons[0]);

            await waitFor(() => {
                expect(screen.getByTestId('confirm-modal')).toBeInTheDocument();
            });

            await userEvent.click(screen.getByText(/Подтвердить/i));

            await waitFor(() => {
                expect(screen.getByTestId('toast-success')).toBeInTheDocument();
            });
        });

        it('closes confirm modal on cancel delete', async () => {
            await renderApp();

            await openDecksList();

            const deleteButtons = screen.getAllByRole('button', {
                name: /Удалить колоду/i,
            });

            await userEvent.click(deleteButtons[0]);
            await userEvent.click(screen.getByText(/Отменить/i));

            await waitFor(() => {
                expect(screen.queryByTestId('confirm-modal')).not.toBeInTheDocument();
            });
        });
    });

    describe('Card editing modal', () => {
        it('opens card modal when clicking edit button', async () => {
            await renderApp();

            await openEditModalForDeck(0);

            expect(screen.getAllByPlaceholderText(/Термин/i).length).toBeGreaterThan(0);
        });

        it('removes a card row when clicking remove button', async () => {
            await renderApp();

            await openEditModalForDeck(0);

            await userEvent.click(screen.getByText('+'));

            const rowsBefore = screen.getAllByPlaceholderText('Термин').length;
            const removeButtons = screen.getAllByText('×');

            await userEvent.click(removeButtons[0]);

            await waitFor(() => {
                expect(screen.queryAllByPlaceholderText('Термин').length).toBeLessThan(rowsBefore);
            });
        });

        it('saves edited cards successfully', async () => {
            await renderApp();

            await openEditModalForDeck(0);

            const termInputs = screen.getAllByPlaceholderText('Термин');
            const firstTermInput = termInputs[0];

            await userEvent.clear(firstTermInput);
            await userEvent.type(firstTermInput, 'Updated term');

            await userEvent.click(screen.getByText(/Сохранить/i));

            await waitFor(() => {
                expect(screen.getByTestId('toast-success')).toBeInTheDocument();
            });
        });

        it('creates new cards successfully', async () => {
            await renderApp();

            await openEditModalForDeck(0);

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

            await openEditModalForDeck(0);

            const termInput = screen.getByDisplayValue('Term 1');

            await userEvent.clear(termInput);
            await userEvent.type(termInput, 'Updated Term');

            await userEvent.click(screen.getByText(/Сохранить/i));

            await waitFor(() => {
                expect(screen.getByTestId('toast-success')).toBeInTheDocument();
            });
        });

        it('shows warning toast when trying to save cards with empty fields', async () => {
            await renderApp();

            await openEditModalForDeck(0);

            await userEvent.click(screen.getByText('+'));
            await userEvent.click(screen.getByText(/Сохранить/i));

            await waitFor(() => {
                expect(screen.getByTestId('toast-warning')).toBeInTheDocument();
            });
        });

        it('closes modal when clicking close button', async () => {
            await renderApp();

            await openEditModalForDeck(0);

            await userEvent.click(screen.getByText(/Закрыть/i));

            await waitFor(() => {
                expect(screen.queryByText(/Редактировать карточки/i)).not.toBeInTheDocument();
            });
        });

        it('shows error toast when saveCards fails', async () => {
            global.fetch = vi.fn((url, options = {}) => {
                if (url.includes('/decks')) {
                    return Promise.resolve({
                        ok: true,
                        json: () =>
                            Promise.resolve([
                                { id: 1, name: 'Default Deck', is_language_deck: false },
                            ]),
                    });
                }

                if (url.includes('/cards/1') && options.method !== 'POST' && options.method !== 'PUT') {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve([]),
                    });
                }

                if (options.method === 'POST' || options.method === 'PUT') {
                    return Promise.resolve({
                        ok: false,
                        json: () => Promise.resolve({ error: 'fail' }),
                    });
                }

                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve([]),
                });
            });

            await renderApp();

            await openEditModalForDeck(0);

            await userEvent.click(screen.getByText('+'));

            const termInputs = screen.getAllByPlaceholderText('Термин');
            const defInputs = screen.getAllByPlaceholderText('Определение');

            await userEvent.type(termInputs.at(-1), 'A');
            await userEvent.type(defInputs.at(-1), 'B');

            await userEvent.click(screen.getByText(/Сохранить/i));

            await waitFor(() => {
                expect(screen.getByTestId('toast-error')).toBeInTheDocument();
            });
        });

        it('handles error when fetching cards in modal', async () => {
            global.fetch = vi.fn((url) => {
                if (url.includes('/cards/')) {
                    return Promise.resolve({ ok: false });
                }

                return Promise.resolve({
                    ok: true,
                    json: () =>
                        Promise.resolve([
                            { id: 1, name: 'Deck', is_language_deck: false },
                        ]),
                });
            });

            await renderApp();

            await userEvent.click(screen.getByRole('button', { name: /Показать/i }));

            const editButtons = screen.getAllByRole('button', {
                name: /Редактировать карточки/i,
            });

            await userEvent.click(editButtons[0]);

            await waitFor(() => {
                expect(screen.getByText(/Редактировать карточки/i)).toBeInTheDocument();
            });
        });
    });

    describe('Language deck translation', () => {
        it('auto-translates a word on blur for language deck', async () => {
            await renderApp();

            await openEditModalForDeck(1);

            await userEvent.click(screen.getByText('+'));

            const wordInput = screen.getByPlaceholderText('Слово');

            await userEvent.clear(wordInput);
            await userEvent.type(wordInput, 'hello');
            fireEvent.blur(wordInput);

            await waitFor(() => {
                expect(screen.getByDisplayValue('hola')).toBeInTheDocument();
            });
        });

        it('does not translate empty word', async () => {
            await renderApp();

            await openEditModalForDeck(1);

            await userEvent.click(screen.getByText('+'));

            const input = screen.getByPlaceholderText('Слово');

            await userEvent.clear(input);
            fireEvent.blur(input);

            expect(input.value).toBe('');
        });

        it('skips translation if word was already translated', async () => {
            await renderApp();

            await openEditModalForDeck(1);

            await userEvent.click(screen.getByText('+'));

            const input = screen.getByPlaceholderText('Слово');

            await userEvent.type(input, 'hello');
            fireEvent.blur(input);

            await waitFor(() => {
                expect(screen.getByDisplayValue('hola')).toBeInTheDocument();
            });

            const fetchCallsBefore = global.fetch.mock.calls.length;

            fireEvent.blur(input);

            expect(global.fetch.mock.calls.length).toBe(fetchCallsBefore);
        });
    });

    describe('Study mode', () => {
        it('starts study mode when clicking study button', async () => {
            await renderApp();

            await openStudyModeForDeck(0);

            expect(screen.getByText(/Term 1/i)).toBeInTheDocument();
        });

        it('displays study mode UI correctly', async () => {
            await renderApp();

            await openStudyModeForDeck(0);

            expect(screen.getByText(/Изучение карточек/i)).toBeInTheDocument();
            expect(screen.getByText(/1 из 2/i)).toBeInTheDocument();
            expect(screen.getByText(/Term 1/i)).toBeInTheDocument();
            expect(
                screen.getByText(/Свайп влево — не запомнил, вправо — запомнил/i)
            ).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /Завершить/i })).toBeInTheDocument();
        });

        it('flips card to show definition on click', async () => {
            await renderApp();

            await openStudyModeForDeck(0);

            const card = screen.getByText(/Term 1/i).closest('.study-card');

            await userEvent.click(card);

            await waitFor(() => {
                expect(screen.getByText(/Definition 1/i)).toBeInTheDocument();
            });

            expect(card).toHaveClass('flipped');
        });

        it('flips card back to term on second click', async () => {
            await renderApp();

            await openStudyModeForDeck(0);

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

        it('exits study mode when clicking "Завершить"', async () => {
            await renderApp();

            await openStudyModeForDeck(0);

            await userEvent.click(screen.getByRole('button', { name: /Завершить/i }));

            await waitFor(() => {
                expect(screen.getByText(/Создать новую колоду/i)).toBeInTheDocument();
                expect(screen.queryByText(/Изучение карточек/i)).not.toBeInTheDocument();
            });
        });

        it('shows message when selected deck has no cards', async () => {
            global.fetch = vi.fn((url) => {
                if (url.includes('/cards/1')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve([]),
                    });
                }

                if (url.includes('/user/')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve(mockUser),
                    });
                }

                if (url.includes('/decks/1')) {
                    return Promise.resolve({
                        ok: true,
                        json: () =>
                            Promise.resolve([
                                { id: 1, name: 'Empty Deck', is_language_deck: false },
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

            const studyButtons = screen.getAllByRole('button', {
                name: /Учить карточки/i,
            });

            await userEvent.click(studyButtons[0]);

            await waitFor(() => {
                expect(
                    screen.getByText(/Добавьте карточки, чтобы начать изучение/i)
                ).toBeInTheDocument();
            });
        });

        it('shows message when no cards in deck (edge case)', async () => {
            global.fetch = vi.fn((url) => {
                if (url.includes('/cards/1')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve([]),
                    });
                }

                if (url.includes('/user/')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve(mockUser),
                    });
                }

                if (url.includes('/decks/1')) {
                    return Promise.resolve({
                        ok: true,
                        json: () =>
                            Promise.resolve([
                                { id: 1, name: 'Default Deck', is_language_deck: false },
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

            const studyButtons = screen.getAllByRole('button', {
                name: /Учить карточки/i,
            });

            await userEvent.click(studyButtons[0]);

            await waitFor(() => {
                expect(
                    screen.getByText(/Добавьте карточки, чтобы начать изучение/i)
                ).toBeInTheDocument();
            });
        });
    });

    describe('Exception and fallback scenarios', () => {
        it('returns fallback user when fetchUserInfo fails', async () => {
            global.fetch = vi.fn(() => Promise.resolve({ ok: false }));

            await renderApp();

            await waitFor(() => {
                expect(screen.getByText(/FlashCards/i)).toBeInTheDocument();
            });
        });

        it('handles fetchLanguages error gracefully', async () => {
            global.fetch = vi.fn((url) => {
                if (url.includes('/languages')) {
                    return Promise.resolve({ ok: false });
                }

                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve([]),
                });
            });

            await renderApp();

            await waitFor(() => {
                expect(screen.getByText(/FlashCards/i)).toBeInTheDocument();
            });
        });
    });
});