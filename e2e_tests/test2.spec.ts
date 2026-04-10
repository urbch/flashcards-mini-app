
import { test, expect } from '@playwright/test';

test('E2E-02: Создание и использование языковой колоды', async ({ page }) => {
  await page.goto('http://localhost:5173/?test_mode=true');
  await page.getByRole('textbox', { name: 'Введите название колоды' }).click();
  await page.getByRole('textbox', { name: 'Введите название колоды' }).fill('test lang deck');
  await page.locator('span').first().click();
  await page.getByRole('combobox').first().selectOption('en');
  await page.getByRole('combobox').nth(1).selectOption('ru');
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  await page.getByRole('button', { name: '► Показать' }).click();
  await page.getByRole('button', { name: 'Редактировать карточки' }).last().click();
  await page.getByRole('button', { name: '+' }).click();
  const wordInput1 = page.getByRole('textbox', { name: 'Слово' }).first();
  await wordInput1.fill('cat');
  await wordInput1.blur();
  await expect(page.getByRole('textbox', { name: 'Перевод' }).first()).not.toBeEmpty();
  await page.getByRole('button', { name: '+' }).click();
  const wordInput2 = page.getByRole('textbox', { name: 'Слово' }).nth(1);
  await wordInput2.fill('dog');
  await wordInput2.blur();
  await expect(page.getByRole('textbox', { name: 'Перевод' }).nth(1)).not.toBeEmpty();
  await page.getByRole('button', { name: 'Сохранить' }).click();
  await page.getByRole('button', { name: 'Учить карточки' }).last().click();
  await page.locator('div').nth(4).click();
  await page.getByRole('button', { name: 'Знаю →' }).click();
  await page.locator('div').nth(4).click();
  await page.getByRole('button', { name: 'Знаю →' }).click();
  await page.getByRole('button', { name: 'Вернуться к колодам' }).click();
  await page.getByRole('button', { name: 'Удалить колоду' }).first().click();
  await page.getByRole('button', { name: 'Подтвердить' }).click();
});