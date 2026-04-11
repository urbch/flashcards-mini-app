import { test as base, Page } from '@playwright/test';

// Функция очистки
async function cleanupAllDecks(page: Page) {
  try {
    await page.goto('http://localhost:5173/?test_mode=true');
    
    const showButton = page.getByRole('button', { name: '► Показать' });
    if (await showButton.isVisible()) {
      await showButton.click();
      await page.waitForTimeout(500);
    }
    
    // Удаляем все колоды
    let deleteButtons = page.getByRole('button', { name: 'Удалить колоду' });
    let count = await deleteButtons.count();
    
    for (let i = 0; i < count; i++) {
      try {
        await deleteButtons.first().click();
        await page.getByRole('button', { name: 'Подтвердить' }).click();
        await page.waitForTimeout(300);
      } catch (e) {
        // Продолжаем, даже если какой-то элемент не удалился
      }
    }
  } catch (error) {
    console.log('Cleanup error:', error);
  }
}

// Расширяем базовый тест
export const test = base.extend({
  page: async ({ page }, use) => {
    // Очистка ПЕРЕД каждым тестом
    await cleanupAllDecks(page);
    
    // Используем страницу в тесте
    await use(page);
    
    // Очистка ПОСЛЕ каждого теста (даже если упал)
    try {
      await cleanupAllDecks(page);
    } catch (e) {
      // Игнорируем ошибки очистки
    }
  },
});

export { expect } from '@playwright/test';