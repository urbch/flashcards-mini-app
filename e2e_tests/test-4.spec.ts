import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('http://localhost:5173/?test_mode=true');
  await page.getByRole('textbox', { name: 'Введите название колоды' }).click();
  await page.getByRole('textbox', { name: 'Введите название колоды' }).fill('изучаю английский');
  await page.locator('span').first().click();
  await page.getByRole('combobox').first().selectOption('en');
  await page.getByRole('combobox').nth(1).selectOption('ru');
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  await page.getByRole('button', { name: '► Показать' }).click();
  await page.getByRole('button', { name: 'Редактировать карточки' }).first().click();
  await page.getByRole('button', { name: '+' }).click();
  await page.getByRole('textbox', { name: 'Слово' }).click();
  await page.getByRole('textbox', { name: 'Слово' }).fill('dog');
  await page.getByRole('textbox', { name: 'Перевод' }).click();
  await page.getByRole('button', { name: 'Сохранить' }).click();
});
//создаем языковую колоду, записываем слово dog с автоматическим переводом и сохраняем