import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test.describe('ResearchPilot End-to-End Workflow', () => {
  const timestamp = Date.now();
  const testUser = {
    name: `Dr. Alex ${timestamp}`,
    email: `alex_${timestamp}@university.edu`,
    password: 'SecurePassword123!',
  };
  const projectTitle = `Brain Tumor Segmentation Benchmark ${timestamp}`;

  test('complete literature review journey: register, upload, plan, execute, verify provenance', async ({ page }) => {
    // 1. Visit the app and register
    await page.goto('/register');
    await expect(page.locator('h2')).toContainText('Create a ResearchPilot account');

    await page.fill('input[placeholder="Dr. Jane Doe"]', testUser.name);
    await page.fill('input[placeholder="researcher@university.edu"]', testUser.email);
    await page.fill('input[placeholder="••••••••"]', testUser.password);
    await page.click('button[type="submit"]');

    // 2. Lands on Dashboard
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.locator('h1')).toContainText('Research Workspaces');

    // 3. Create a Research Project
    await page.click('button:has-text("New Research Project")');
    await page.fill('input[placeholder="e.g. Brain Tumor Segmentation: CNN vs ViT"]', projectTitle);
    await page.fill('textarea[placeholder*="Goals, target benchmarks"]', 'Systematic evaluation across deep learning architectures.');
    await page.click('button:has-text("Create Project")');

    // 4. Open the created workspace
    const projectCard = page.locator(`h3:has-text("${projectTitle}")`);
    await expect(projectCard).toBeVisible();
    await projectCard.click();

    await expect(page).toHaveURL(/.*\/projects\/.+/);
    await expect(page.locator('h1')).toContainText(projectTitle);

    // 5. Upload 3 sample PDF papers
    const samplePapersDir = path.resolve(__dirname, '../../data/sample_papers');
    const filesToUpload = [
      path.join(samplePapersDir, 'chen_2023_deep_cnn_glioma.pdf'),
      path.join(samplePapersDir, 'gupta_2024_vision_transformers_neuro.pdf'),
      path.join(samplePapersDir, 'thorne_2024_comparative_benchmark_mri.pdf'),
    ];

    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.locator('div:has-text("Upload Academic Research Papers (PDF)")').last().click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(filesToUpload);

    // Wait until all 3 papers appear
    await expect(page.locator('text=chen_2023_deep_cnn_glioma.pdf')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=gupta_2024_vision_transformers_neuro.pdf')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=thorne_2024_comparative_benchmark_mri.pdf')).toBeVisible({ timeout: 15000 });

    // Wait for the worker to process documents to "Ready" state
    await expect(page.locator('span:has-text("Ready")').first()).toBeVisible({ timeout: 25000 });
    await expect(page.locator('a:has-text("Start Literature Review")')).not.toHaveClass(/cursor-not-allowed/, { timeout: 20000 });

    // 6. Navigate to New Literature Review
    await page.click('a:has-text("Start Literature Review")');
    await expect(page).toHaveURL(/.*\/new-run/);

    // 7. Enter research question
    await page.fill('textarea[placeholder*="How do Convolutional Neural Networks"]', 'What are the reported Dice score benchmarks for Brain Tumor segmentation across CNN and Transformer models?');
    
    // Submit for plan generation
    await page.click('button:has-text("Generate & Review Plan")');

    // 8. Review Research Plan
    await expect(page).toHaveURL(/.*\/plan/, { timeout: 20000 });
    await expect(page.locator('h1')).toContainText('Inspect & Approve Research Plan');
    await expect(page.locator('text=Phase 1: Plan Review')).toBeVisible();

    // 9. Approve Plan and start execution
    await page.click('button:has-text("Approve & Run Agent")');

    // 10. Observability & Activity timeline
    await expect(page).toHaveURL(/.*\/activity/, { timeout: 20000 });
    await expect(page.locator('h1')).toContainText('Research Orchestrator Activity');

    // Wait for run completion and redirect to report
    await expect(page).toHaveURL(/.*\/report/, { timeout: 40000 });
    await expect(page.locator('h1')).toContainText('Literature Review:');
    await expect(page.locator('text=Verified Literature Review')).toBeVisible();

    // 11. Test Report interaction and Provenance
    await page.click('button:has-text("Methodology Comparison Matrix")');
    await expect(page.locator('table')).toBeVisible();

    await page.click('button:has-text("Thematic Review & Scope")');
    // Click citation to view ground-truth drawer
    const citationBadge = page.locator('button:has-text("[1]")').first();
    await expect(citationBadge).toBeVisible();
    await citationBadge.click();

    await expect(page.locator('text=Verified exact excerpt from stored chunk')).toBeVisible();

    // Close citation modal
    await page.locator('div.fixed button').first().click();

    // Verify Copy Markdown button works
    await page.click('button:has-text("Copy Markdown")');
    await expect(page.locator('button:has-text("Copied MD!")')).toBeVisible();

    // Verify refresh persistence: data survives browser reload
    await page.reload();
    await expect(page.locator('h1')).toContainText('Literature Review:');
    await expect(page.locator('text=Verified Literature Review')).toBeVisible();
  });
});
