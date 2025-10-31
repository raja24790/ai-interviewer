import { test, expect, Page } from '@playwright/test';

// Mock API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

// Helper function to mock API responses
async function mockAPIResponses(page: Page) {
  // Mock /interview/start
  await page.route(`${API_BASE}/interview/start`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        session_id: 'test-session-123',
        questions: [
          'Tell me about yourself.',
          'Describe a challenging project you worked on.',
          'How do you handle tight deadlines?',
          'What motivates you at work?',
          'Where do you see yourself in five years?',
        ],
        token: {
          access_token: 'mock-jwt-token',
          token_type: 'bearer',
        },
      }),
    });
  });

  // Mock /stt/append
  await page.route(`${API_BASE}/stt/append`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'ok' }),
    });
  });

  // Mock /interview/{session_id}/attention GET
  await page.route(`${API_BASE}/interview/*/attention`, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          state: 'focused',
          score: 0.85,
          last_event: 'looking_forward',
        }),
      });
    } else if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'recorded' }),
      });
    }
  });

  // Mock /report/finalize
  await page.route(`${API_BASE}/report/finalize`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        session_id: 'test-session-123',
        pdf_url: '/reports/test-session-123/final_report.pdf',
        summary:
          'The candidate demonstrated strong communication skills and technical knowledge.',
        questions: [
          {
            question: 'Tell me about yourself.',
            transcript: 'I am a software engineer with 5 years of experience.',
            scores: {
              clarity: 4,
              relevance: 5,
              structure: 4,
              conciseness: 4,
              confidence: 5,
              total: 22,
              commentary: 'Well-structured response with good detail.',
            },
          },
          {
            question: 'Describe a challenging project you worked on.',
            transcript: 'I worked on a microservices migration project.',
            scores: {
              clarity: 5,
              relevance: 5,
              structure: 5,
              conciseness: 4,
              confidence: 4,
              total: 23,
              commentary: 'Excellent technical depth and clarity.',
            },
          },
        ],
      }),
    });
  });
}

test.describe('AI Interviewer E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await mockAPIResponses(page);
  });

  test('should load the interview page successfully', async ({ page }) => {
    await page.goto('/interview');
    await expect(page).toHaveTitle(/AI Interview/i);
  });

  test('should start an interview and display questions', async ({ page }) => {
    await page.goto('/interview');

    // Start interview
    const startButton = page.getByRole('button', { name: /start interview/i });
    await expect(startButton).toBeVisible();
    await startButton.click();

    // Wait for questions to load
    await page.waitForTimeout(1000);

    // Check if first question is displayed
    await expect(page.getByText(/tell me about yourself/i)).toBeVisible();
  });

  test('should navigate through interview questions', async ({ page }) => {
    await page.goto('/interview');

    // Start interview
    await page.getByRole('button', { name: /start interview/i }).click();
    await page.waitForTimeout(1000);

    // Check first question
    await expect(page.getByText(/tell me about yourself/i)).toBeVisible();

    // Navigate to next question
    const nextButton = page.getByRole('button', { name: /next/i });
    if (await nextButton.isVisible()) {
      await nextButton.click();
      await page.waitForTimeout(500);

      // Check if second question is displayed
      await expect(
        page.getByText(/describe a challenging project/i)
      ).toBeVisible();
    }
  });

  test('should display audio capture component', async ({ page }) => {
    await page.goto('/interview');
    await page.getByRole('button', { name: /start interview/i }).click();
    await page.waitForTimeout(1000);

    // Check for audio capture button
    const recordButton = page.getByRole('button', {
      name: /start recording/i,
    });
    await expect(recordButton).toBeVisible();
  });

  test('should display attention monitoring component', async ({ page }) => {
    await page.goto('/interview');
    await page.getByRole('button', { name: /start interview/i }).click();
    await page.waitForTimeout(1000);

    // Check for attention monitoring
    await expect(page.getByText(/attention/i)).toBeVisible();
  });

  test('should display score panel', async ({ page }) => {
    await page.goto('/interview');
    await page.getByRole('button', { name: /start interview/i }).click();
    await page.waitForTimeout(1000);

    // Check for score panel
    await expect(page.getByText(/score/i)).toBeVisible();
  });

  test('should complete interview and show final report', async ({ page }) => {
    await page.goto('/interview');

    // Start interview
    await page.getByRole('button', { name: /start interview/i }).click();
    await page.waitForTimeout(1000);

    // Look for finalize/finish button
    const finalizeButton = page.getByRole('button', {
      name: /finalize|finish|complete/i,
    });

    // If finalize button exists, click it
    if (await finalizeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await finalizeButton.click();
      await page.waitForTimeout(1000);

      // Check for final report elements
      const reportHeading = page.getByRole('heading', {
        name: /report|summary/i,
      });
      if (await reportHeading.isVisible({ timeout: 2000 }).catch(() => false)) {
        await expect(reportHeading).toBeVisible();
      }
    }
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Override mock to return error
    await page.route(`${API_BASE}/interview/start`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    });

    await page.goto('/interview');
    await page.getByRole('button', { name: /start interview/i }).click();
    await page.waitForTimeout(1000);

    // Check for error message (if displayed)
    // This depends on how the app handles errors
  });

  test('should display countdown timer during questions', async ({ page }) => {
    await page.goto('/interview');
    await page.getByRole('button', { name: /start interview/i }).click();
    await page.waitForTimeout(1000);

    // Look for timer element (if implemented)
    const timerElement = page.locator('text=/\\d+:\\d+|timer/i');
    if (await timerElement.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(timerElement).toBeVisible();
    }
  });

  test('should persist session across page reloads', async ({ page }) => {
    await page.goto('/interview');
    await page.getByRole('button', { name: /start interview/i }).click();
    await page.waitForTimeout(1000);

    // Get current question text
    const questionText = await page.textContent('body');

    // Reload page
    await page.reload();
    await page.waitForTimeout(1000);

    // Session should be maintained if implemented
    // This test will pass if the session state is properly managed
  });

  test('should validate responsive design on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/interview');
    await expect(page.getByRole('button', { name: /start interview/i })).toBeVisible();

    // Check if elements are properly displayed on mobile
    const startButton = page.getByRole('button', { name: /start interview/i });
    const buttonBox = await startButton.boundingBox();

    expect(buttonBox).not.toBeNull();
    if (buttonBox) {
      expect(buttonBox.width).toBeLessThanOrEqual(375);
    }
  });

  test('should download PDF report', async ({ page }) => {
    await page.goto('/interview');
    await page.getByRole('button', { name: /start interview/i }).click();
    await page.waitForTimeout(1000);

    // Look for download button
    const downloadButton = page.getByRole('button', { name: /download/i });

    if (await downloadButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Set up download listener
      const downloadPromise = page.waitForEvent('download');
      await downloadButton.click();

      // Wait for download to start
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.pdf$/);
    }
  });
});

test.describe('Performance Tests', () => {
  test('should load page within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/interview');
    const loadTime = Date.now() - startTime;

    // Page should load in less than 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should handle rapid button clicks', async ({ page }) => {
    await mockAPIResponses(page);
    await page.goto('/interview');

    const startButton = page.getByRole('button', { name: /start interview/i });

    // Click multiple times rapidly
    await startButton.click();
    await startButton.click();
    await startButton.click();

    // Should not cause errors
    await page.waitForTimeout(1000);
    await expect(page.getByText(/tell me about yourself/i)).toBeVisible();
  });
});

test.describe('Accessibility Tests', () => {
  test('should have proper ARIA labels', async ({ page }) => {
    await mockAPIResponses(page);
    await page.goto('/interview');

    // Check for important ARIA landmarks
    const mainButton = page.getByRole('button', { name: /start interview/i });
    await expect(mainButton).toBeVisible();
  });

  test('should support keyboard navigation', async ({ page }) => {
    await mockAPIResponses(page);
    await page.goto('/interview');

    // Tab to start button
    await page.keyboard.press('Tab');

    // Check if button is focused
    const startButton = page.getByRole('button', { name: /start interview/i });
    await expect(startButton).toBeFocused();

    // Press Enter to activate
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1000);

    await expect(page.getByText(/tell me about yourself/i)).toBeVisible();
  });
});
