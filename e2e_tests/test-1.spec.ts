import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('http://localhost:5173/?test_mode=true');
  await page.locator('span').first().click();
  await page.getByRole('textbox', { name: 'Введите название колоды' }).click();
  await page.getByRole('textbox', { name: 'Введите название колоды' }).fill('изучаю английский');
  await page.getByRole('textbox', { name: 'Введите название колоды' }).press('ArrowLeft');
  await page.getByRole('textbox', { name: 'Введите название колоды' }).press('ArrowLeft');
  await page.getByRole('textbox', { name: 'Введите название колоды' }).press('ArrowLeft');
  await page.getByRole('textbox', { name: 'Введите название колоды' }).press('ArrowLeft');
  await page.getByRole('combobox').first().selectOption('ru');
  await page.getByRole('combobox').nth(1).selectOption('en');
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  await page.getByRole('button', { name: '► Показать' }).click();
  await page.getByRole('button', { name: 'Удалить колоду' }).nth(2).click();
  await page.getByRole('button', { name: 'Подтвердить' }).click();
});

