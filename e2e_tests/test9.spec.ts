import { test, expect } from './test.setup';

test('E2E-09: Ошибка сервиса перевода', async ({ page }) => {
  await page.goto('http://localhost:5173/?test_mode=true');
  
  await page.getByRole('textbox', { name: 'Введите название колоды' }).fill('Тест ошибки');
  await page.locator('span').first().click();
  await page.getByRole('combobox').first().selectOption('en');
  await page.getByRole('combobox').nth(1).selectOption('ru');
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  await page.waitForTimeout(500);
  
  await page.getByRole('button', { name: '► Показать' }).click();
  await page.getByRole('button', { name: 'Редактировать карточки' }).click();
  await page.getByRole('button', { name: '+' }).click();
  
  // мокаем ошибку API
  await page.route('**/translate', async (route) => {
    await route.fulfill({ status: 500, body: 'Service unavailable' });
  });
  
  const wordInput = page.getByRole('textbox', { name: 'Слово' }).first();
  await wordInput.fill('hello');
  await wordInput.blur();
  
  await expect(page.locator('.toast-warning, .toast-error')).toBeVisible();
  
  // проверяем, что можно ввести перевод вручную
  const translationInput = page.getByRole('textbox', { name: 'Перевод' }).first();
  await expect(translationInput).toBeVisible();
  await translationInput.fill('привет');
  
  await page.getByRole('button', { name: 'Сохранить' }).click();
  await expect(page.locator('.toast-success')).toBeVisible();
  
  await page.getByRole('button', { name: 'Редактировать карточки' }).click();
  await expect(page.getByRole('textbox', { name: 'Слово' }).first()).toHaveValue('hello');
  await expect(page.getByRole('textbox', { name: 'Перевод' }).first()).toHaveValue('привет');
  await page.getByRole('button', { name: 'Сохранить' }).click();
  });