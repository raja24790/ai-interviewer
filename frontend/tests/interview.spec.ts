import { expect, test } from '@playwright/test';

const sessionFixture = {
  session_id: 'session123',
  questions: [
    'Tell me about yourself.',
    'Describe a challenging project you worked on.',
    'How do you handle tight deadlines?',
  ],
  token: { access_token: 'fake-token' },
};

const attentionFixture = {
  state: 'focused',
  score: 0.92,
  last_event: 'looking-forward',
};

test('user can start an interview and view the first question', async ({ page }) => {
  await page.route('http://127.0.0.1:5001/interview/start', async (route) => {
    await route.fulfill({
      status: 200,
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(sessionFixture),
    });
  });

  await page.route('http://127.0.0.1:5001/interview/session123/attention', async (route) => {
    await route.fulfill({
      status: 200,
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(attentionFixture),
    });
  });

  await page.goto('/interview');
  await page.getByRole('button', { name: 'Start' }).click();

  await expect(page.getByText(sessionFixture.questions[0])).toBeVisible();
  await expect(page.getByText('Question 1 of 3')).toBeVisible();
  await expect(page.getByText('Live Scores')).toBeVisible();
});
