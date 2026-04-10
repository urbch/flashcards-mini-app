import { test, expect } from '@playwright/test';

test('E2E-07: Удаление колоды с карточками', async ({ page }) => {
  await page.goto('http://localhost:5173/?test_mode=true');
  await page.getByRole('textbox', { name: 'Введите название колоды' }).click();
  await page.getByRole('textbox', { name: 'Введите название колоды' }).fill('removable deck ');
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  await page.getByRole('button', { name: '► Показать' }).click();
  await page.getByRole('button', { name: 'Редактировать карточки' }).first().click();
  await page.getByRole('button', { name: '+' }).click();
  await page.getByRole('textbox', { name: 'Термин' }).click();
  await page.getByRole('textbox', { name: 'Термин' }).fill('term 1');
  await page.getByRole('textbox', { name: 'Определение' }).click();
  await page.getByRole('textbox', { name: 'Определение' }).fill('deff 1');
  await page.getByRole('button', { name: '+' }).click();
  await page.getByRole('textbox', { name: 'Термин' }).nth(1).click();
  await page.getByRole('textbox', { name: 'Термин' }).nth(1).fill('term 2');
  await page.getByRole('textbox', { name: 'Определение' }).nth(1).click();
  await page.getByRole('textbox', { name: 'Определение' }).nth(1).fill('deff 2');
  await page.getByRole('button', { name: 'Сохранить' }).click();
  await page.getByRole('button', { name: 'Удалить колоду' }).first().click();
  await page.getByRole('button', { name: 'Подтвердить' }).click();
  await page.getByText('Колода успешно удалена').click();
});