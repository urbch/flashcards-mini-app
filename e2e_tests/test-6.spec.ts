import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('http://localhost:5173/?test_mode=true');
  await page.getByRole('textbox', { name: 'Введите название колоды' }).click();
  await page.getByRole('textbox', { name: 'Введите название колоды' }).fill('новая колода');
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  await page.getByRole('button', { name: '► Показать' }).click();
  await page.getByRole('button', { name: 'Удалить колоду' }).first().click();
  await page.getByRole('button', { name: 'Подтвердить' }).click();
});