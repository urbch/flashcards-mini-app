import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('http://localhost:5173/?test_mode=true');
  await page.getByRole('textbox', { name: 'Введите название колоды' }).click();
  await page.getByRole('textbox', { name: 'Введите название колоды' }).fill('тест');
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  await page.getByRole('button', { name: '► Показать' }).click();
  await page.getByRole('button', { name: 'Редактировать карточки' }).nth(2).click();
  await page.getByRole('button', { name: '+' }).click();
  await page.getByRole('textbox', { name: 'Термин' }).click();
  await page.getByRole('textbox', { name: 'Термин' }).fill('1');
  await page.getByRole('textbox', { name: 'Определение' }).click();
  await page.getByRole('textbox', { name: 'Определение' }).fill('определение');
  await page.getByRole('button', { name: 'Сохранить' }).click();
  await page.getByRole('button', { name: 'Учить карточки' }).nth(2).click();
  await page.locator('div').nth(4).click();
  await page.locator('body').click();
  await page.locator('div').nth(4).click();
  await page.locator('div').filter({ hasText: 'определение' }).nth(4).click();
  await page.locator('div').nth(4).click();
  await page.getByRole('button', { name: 'Завершить' }).click();
});

//можно удалить