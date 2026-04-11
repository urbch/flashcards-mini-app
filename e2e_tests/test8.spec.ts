import { test, expect } from './test.setup';

test('E2E-08: Прохождение режима изучения', async ({ page }) => {
  await page.goto('http://localhost:5173/?test_mode=true');
  
  const TOTAL_CARDS = 3;
  
  await page.getByRole('textbox', { name: 'Введите название колоды' }).fill('Колода для изучения');
  await page.getByRole('button', { name: 'Создать колоду' }).click();
  await page.waitForTimeout(500);
  
  await page.getByRole('button', { name: '► Показать' }).click();
  await page.getByRole('button', { name: 'Редактировать карточки' }).first().click();
  
  for (let i = 1; i <= TOTAL_CARDS; i++) {
    await page.getByRole('button', { name: '+' }).click();
    await page.getByRole('textbox', { name: 'Термин' }).nth(i - 1).fill(`Термин ${i}`);
    await page.getByRole('textbox', { name: 'Определение' }).nth(i - 1).fill(`Определение ${i}`);
  }
  
  await page.getByRole('button', { name: 'Сохранить' }).click();
  await page.waitForTimeout(500);
  
  await page.getByRole('button', { name: 'Учить карточки' }).first().click();
  
  let correct = 0;
  let incorrect = 0;

  for (let current = 1; current <= TOTAL_CARDS; current++) {
    // проверяем, что счетчик показывает правильный номер
    await expect(page.getByText(new RegExp(`${current} из ${TOTAL_CARDS}`))).toBeVisible();
    
    if (current === 2) {
      await page.getByRole('button', { name: '← Не знаю' }).click();
      incorrect++;
    } else {
      await page.getByRole('button', { name: 'Знаю →' }).click();
      correct++;
    }
    await page.waitForTimeout(300);
  }
  
  await expect(page.getByText('Результаты изучения')).toBeVisible();
  
  await expect(page.getByText('Правильно', { exact: true })).toBeVisible();
  await expect(page.getByText(correct.toString())).toBeVisible();
  
  await expect(page.getByText('Неправильно', { exact: true })).toBeVisible();
  await expect(page.getByText(incorrect.toString())).toBeVisible();
  
  await expect(page.getByText(TOTAL_CARDS.toString())).toBeVisible();
  await expect(page.getByText('Всего')).toBeVisible();
  
  const percentage = Math.round((correct / TOTAL_CARDS) * 100);
  await expect(page.getByText(`${percentage}% выучено`)).toBeVisible();
  
  await page.getByRole('button', { name: 'Вернуться к колодам' }).click();
});