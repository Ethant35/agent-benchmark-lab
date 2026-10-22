import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './',
  testMatch: 'e2e.spec.ts',
  use: { baseURL: process.env.ABL_BASE_URL ?? 'http://127.0.0.1:8000', headless: true },
  reporter: 'list',
  timeout: 30_000,
});
