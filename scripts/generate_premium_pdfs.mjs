/**
 * 12星座のプレミアムSoul Reading PDFを一括生成（Gumroad納品物用）
 * - 各星座の代表日ページからプレミアムブロックだけを抽出してPDF化
 * - 出力先: ~/Desktop/BirthdayWellness_PremiumPDFs/
 */
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join } from 'node:path';

// 星座 → 代表日ページのマッピング
const ZODIAC_PAGES = [
  { zodiac: 'aries',       path: '/en/april/15/' },
  { zodiac: 'taurus',      path: '/en/may/15/' },
  { zodiac: 'gemini',      path: '/en/june/15/' },
  { zodiac: 'cancer',      path: '/en/july/15/' },
  { zodiac: 'leo',         path: '/en/august/15/' },
  { zodiac: 'virgo',       path: '/en/september/15/' },
  { zodiac: 'libra',       path: '/en/october/15/' },
  { zodiac: 'scorpio',     path: '/en/november/15/' },
  { zodiac: 'sagittarius', path: '/en/november/25/' },
  { zodiac: 'capricorn',   path: '/en/january/15/' },
  { zodiac: 'aquarius',    path: '/en/february/15/' },
  { zodiac: 'pisces',      path: '/en/march/15/' },
];

const BASE_URL = 'https://www.birthdaywellness.com';
const OUTPUT_DIR = join(homedir(), 'Desktop', 'BirthdayWellness_PremiumPDFs');

// プレミアムブロックだけを表示するための印刷用CSS
const PRINT_CSS = `
  header, footer, nav { display: none !important; }
  article > *:not(.bg-premium-night) { display: none !important; }
  body { background: #0f0a1f !important; margin: 0 !important; padding: 0 !important; }
  main { padding: 0 !important; margin: 0 !important; max-width: none !important; }
  article { margin: 0 !important; }
  .bg-premium-night { border-radius: 0 !important; box-shadow: none !important; }
  .cosmic-decoration { display: none !important; }
`;

async function main() {
  await mkdir(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 900, height: 1200 } });

  console.log(`📜 12星座のプレミアムPDFを生成します`);
  console.log(`保存先: ${OUTPUT_DIR}\n`);

  for (let i = 0; i < ZODIAC_PAGES.length; i++) {
    const { zodiac, path } = ZODIAC_PAGES[i];
    const url = `${BASE_URL}${path}`;
    const outputPath = join(
      OUTPUT_DIR,
      `Premium_Soul_Reading_${zodiac.charAt(0).toUpperCase() + zodiac.slice(1)}.pdf`,
    );

    process.stdout.write(`[${i + 1}/12] ${zodiac.padEnd(12)} 生成中... `);

    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
      await page.addStyleTag({ content: PRINT_CSS });
      // フォント読み込み待ち
      await page.waitForTimeout(2500);

      // プレミアムブロックが存在するか確認
      const premiumCount = await page.locator('article > .bg-premium-night').count();
      if (premiumCount === 0) {
        process.stdout.write(`✗ プレミアムブロックが見つかりません\n`);
        continue;
      }

      // printメディアだと白紙になるためscreenメディアで出力する
      await page.emulateMedia({ media: 'screen' });
      await page.pdf({
        path: outputPath,
        format: 'A4',
        printBackground: true,
        margin: { top: '0', bottom: '0', left: '0', right: '0' },
      });

      process.stdout.write(`✓ 保存\n`);
    } catch (err) {
      process.stdout.write(`✗ 失敗: ${err.message}\n`);
    }
  }

  await browser.close();
  console.log(`\n🎉 完了！デスクトップの「BirthdayWellness_PremiumPDFs」フォルダに保存しました。`);
}

main().catch((err) => {
  console.error('エラー:', err);
  process.exit(1);
});
