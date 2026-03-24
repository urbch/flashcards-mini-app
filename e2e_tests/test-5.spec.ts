import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('http://localhost:5173/?test_mode=true');
  await page.getByRole('button', { name: '► Показать' }).click();
  await page.getByRole('button', { name: 'Редактировать карточки' }).click();
  await page.getByRole('button', { name: '+' }).click();
  await page.getByRole('textbox', { name: 'Слово' }).nth(1).click();
  await page.getByRole('textbox', { name: 'Слово' }).nth(1).fill('new');
  await page.getByRole('textbox', { name: 'Перевод' }).nth(1).click();
  await page.getByRole('textbox', { name: 'Перевод' }).nth(1).click();
  await page.getByRole('textbox', { name: 'Перевод' }).nth(1).fill('новый');
  await page.getByRole('button', { name: '×' }).first().click();
  await page.getByRole('button', { name: 'Сохранить' }).click();
});