import { test, expect } from './test.setup';

test('E2E-05: Стресс-тест с максимальным количеством карточек (100)', async ({ page }) => {
  const TOTAL_CARDS = 100;
  const deckName = 'Стресс-тест колода';
  
  await page.goto('http://localhost:5173/?test_mode=true');
  
  await page.getByRole('textbox', { name: 'Введите название колоды' }).fill(deckName);
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  await page.waitForTimeout(500);
  
  await page.getByRole('button', { name: '► Показать' }).click();
  await page.getByRole('button', { name: 'Редактировать карточки' }).click();
  
  for (let i = 1; i <= TOTAL_CARDS; i++) {
    await page.getByRole('button', { name: '+' }).click();
    await page.getByRole('textbox', { name: 'Термин' }).last().fill(`Термин ${i}`);
    await page.getByRole('textbox', { name: 'Определение' }).last().fill(`Определение ${i}`);
    
    if (i % 10 === 0) {
      console.log(`Добавлено ${i} карточек`);
    }
  }
  
  await page.getByRole('button', { name: 'Сохранить' }).click();
  await expect(page.locator('.toast-success')).toBeVisible();
  
  await page.getByRole('button', { name: 'Закрыть' }).click();
  await page.getByRole('button', { name: 'Учить карточки' }).click();
  await expect(page.getByText(`1 из ${TOTAL_CARDS}`)).toBeVisible();
  
  // проходим первые 15 карточек для проверки
  for (let i = 1; i <= 15; i++) {
    await page.getByRole('button', { name: 'Знаю →' }).click();
  }
  
  await page.getByRole('button', { name: 'Завершить' }).click();
});