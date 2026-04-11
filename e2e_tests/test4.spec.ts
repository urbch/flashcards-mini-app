import { test, expect } from './test.setup';

test('E2E-04: Ограничение количества колод (лимит 20)', async ({ page }) => {
  const MAX_DECKS_PER_USER = 20;
  
  await page.goto('http://localhost:5173/?test_mode=true');
  await page.getByRole('button', { name: '► Показать' }).click();
  
  // создаем 20 колод
  for (let i = 1; i <= MAX_DECKS_PER_USER; i++) {
    const deckName = `Колода ${i}`;
    await page.getByRole('textbox', { name: 'Введите название колоды' }).clear();
    await page.getByRole('textbox', { name: 'Введите название колоды' }).fill(deckName);
    await page.getByRole('button', { name: 'Создать колоду' }).click();
    await page.waitForTimeout(500);
  }
  
  const deckCount = await page.locator('.deck-card').count();
  console.log(`количество колод: ${deckCount}`);
  
  // пытаемся создать 21-ю
  await page.getByRole('textbox', { name: 'Введите название колоды' }).clear();
  await page.getByRole('textbox', { name: 'Введите название колоды' }).fill('Колода 21');
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  await page.waitForTimeout(500);
  
  await expect(page.getByText('Колода 21')).not.toBeVisible();
  await expect(page.locator('.toast-error')).toBeVisible();
  const deckCount2 = await page.locator('.deck-card').count();
  console.log(`количество колод после попытки создать 21: ${deckCount2}`);
});