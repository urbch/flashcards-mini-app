import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('http://localhost:5173/?test_mode=true');
  await page.getByRole('button', { name: '► Показать' }).click();
  await page.getByRole('button', { name: 'Редактировать карточки' }).first().click();
  await page.getByRole('button', { name: '×' }).first().click();
  await page.getByRole('button', { name: 'Сохранить' }).click();
  await page.getByRole('button', { name: '▼ Скрыть' }).click();
});
// заходим в приложение, и смотрим колоды, выбираем первую колоду, удалем первую карточку, скрываем колоды