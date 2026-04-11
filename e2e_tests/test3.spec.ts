import { test, expect } from './test.setup';

test('E2E-03: Валидация создания колоды', async ({ page }) => {
  await page.goto('http://localhost:5173/?test_mode=true');
  
  // Шаг 1: Попытаться создать колоду без названия
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  
  // Проверяем warning тост (класс toast-warning)
  const warningToast = page.locator('.toast-warning');
  await expect(warningToast).toBeVisible({ timeout: 3000 });
  await expect(warningToast).toContainText('Введите название колоды');
  
  // Шаг 2: Ввести корректное название
  await page.getByRole('textbox', { name: 'Введите название колоды' }).fill('deck name');
  
  // Шаг 3: Создать колоду снова
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  
  // Проверяем success тост (класс toast-success)
  const successToast = page.locator('.toast-success');
  await expect(successToast).toBeVisible({ timeout: 3000 });
  await expect(successToast).toContainText('успешно создана');
  
  // Проверяем, что колода появилась в списке
  await page.getByRole('button', { name: '► Показать' }).click();
  await expect(page.getByText('deck name')).toBeVisible();
});