/**
 * Pinterest用ピン画像を一括スクリーンショット
 * 実行: node scripts/screenshot-pins.js
 * 出力: pinterest-images/ フォルダに PNG保存
 *
 * 前提: npm run build && npx wrangler pages dev dist --port=4321 を別ターミナルで起動しておく
 * または BASE_URL=https://birthdaywellness.com node scripts/screenshot-pins.js でも可
 */

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const BASE_URL = process.env.BASE_URL || 'http://localhost:4321';
const OUTPUT_DIR = path.join(__dirname, '..', 'pinterest-images');

const ZODIAC_SIGNS = [
  'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
  'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces',
];

async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Pinterest推奨サイズ: 1000×1500px
  await page.setViewportSize({ width: 1000, height: 1500 });

  for (const sign of ZODIAC_SIGNS) {
    const url = `${BASE_URL}/en/pin/${sign}/`;
    console.log(`📸 Screenshotting: ${url}`);

    await page.goto(url, { waitUntil: 'networkidle' });

    // Google Fontsの読み込み待機
    await page.waitForTimeout(2000);

    // pin articleのみをクリップ（背景グレーを除外）
    const article = page.locator('article');
    const outPath = path.join(OUTPUT_DIR, `pin-${sign}.png`);

    await article.screenshot({ path: outPath });
    console.log(`   ✓ Saved: pinterest-images/pin-${sign}.png`);
  }

  await browser.close();
  console.log('\n✅ 全12星座のスクリーンショット完了！');
  console.log(`📂 保存先: ${OUTPUT_DIR}`);
  console.log('\n次のステップ:');
  console.log('1. pinterest-images/ フォルダを開く');
  console.log('2. Pinterest → ピン作成 → 画像をアップロード');
  console.log('3. リンク先: https://birthdaywellness.com/en/[month]/15/ (各星座の代表日)');
}

main().catch(console.error);
