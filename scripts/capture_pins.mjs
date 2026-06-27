/**
 * 12星座のPinterestピン画像を一括撮影
 * - 各星座のページにアクセスし、ピン領域だけをスクショ
 * - 1000x1500のPNG画像として保存
 */
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join } from 'node:path';

const ZODIACS = [
  'sagittarius',
  'aries',
  'taurus',
  'gemini',
  'cancer',
  'leo',
  'virgo',
  'libra',
  'scorpio',
  'capricorn',
  'aquarius',
  'pisces',
];

const BASE_URL = 'https://www.birthdaywellness.com/en/pin';
const OUTPUT_DIR = join(homedir(), 'Desktop', 'BirthdayWellness_Pins');

async function main() {
  await mkdir(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1200, height: 1700 },
    deviceScaleFactor: 2, // Retina相当の高解像度
  });
  const page = await context.newPage();

  console.log(`🎨 12星座のピン画像を撮影します`);
  console.log(`保存先: ${OUTPUT_DIR}\n`);

  for (let i = 0; i < ZODIACS.length; i++) {
    const zodiac = ZODIACS[i];
    const url = `${BASE_URL}/${zodiac}/`;
    const outputPath = join(
      OUTPUT_DIR,
      `pin_${String(i + 1).padStart(2, '0')}_${zodiac}.png`,
    );

    process.stdout.write(
      `[${i + 1}/12] ${zodiac.padEnd(12)} 撮影中... `,
    );

    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
      // フォントが完全に読み込まれるのを少し待つ
      await page.waitForTimeout(2500);

      // article要素（ピン本体）だけをスクショ
      const article = await page.locator('article').first();
      await article.screenshot({ path: outputPath, type: 'png' });

      process.stdout.write(`✓ 保存\n`);
    } catch (err) {
      process.stdout.write(`✗ 失敗: ${err.message}\n`);
    }
  }

  await browser.close();
  console.log(`\n🎉 完了！デスクトップの「BirthdayWellness_Pins」フォルダに12枚保存しました。`);
}

main().catch((err) => {
  console.error('エラー:', err);
  process.exit(1);
});
