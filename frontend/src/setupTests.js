globalThis.IS_REACT_ACT_ENVIRONMENT = true;
import { expect } from 'vitest';
import * as matchers from '@testing-library/jest-dom/matchers';
import { vi } from 'vitest';

// Расширяем expect с matchers из jest-dom
expect.extend(matchers);

// Мокаем TelegramWebApp
vi.mock('@twa-dev/sdk', () => ({
    default: {
        ready: vi.fn(),
        initDataUnsafe: { user: { id: 1, first_name: 'Test User' } },
    },
}));

