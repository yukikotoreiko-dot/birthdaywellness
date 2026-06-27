#!/usr/bin/env python3
"""
誕生日占いデータ自動生成スクリプト
- OpenAI GPT-4o-mini で日本語データ生成
- 同じく英訳して英語版データを生成
- src/data/birthdays/{ja,en}/MM-DD.json として保存

使い方:
  python3 generate_birthdays.py                # 3日分テスト (1/1, 6/15, 12/31)
  python3 generate_birthdays.py --all          # 366日分全件
  python3 generate_birthdays.py --date 03-14   # 特定日のみ
"""
import os, json, time, sys
import urllib.request
import urllib.error
from pathlib import Path

# === 設定 ===
OPENAI_API_KEY = open("/Users/makiyukiko/.claude/config/openai_api_key").read().strip()
PROJECT_DIR = Path("/Users/makiyukiko/Documents/birthdaywellness")
DATA_DIR_JA = PROJECT_DIR / "src/data/birthdays/ja"
DATA_DIR_EN = PROJECT_DIR / "src/data/birthdays/en"
MODEL = "gpt-4o-mini"

# === 占星術データ ===
ZODIAC_RANGES = [
    (1, 1, 1, 19,  "山羊座",  "Capricorn",   "earth", "12/22〜1/19"),
    (1, 20, 2, 18, "水瓶座",  "Aquarius",    "air",   "1/20〜2/18"),
    (2, 19, 3, 20, "魚座",    "Pisces",      "water", "2/19〜3/20"),
    (3, 21, 4, 19, "牡羊座",  "Aries",       "fire",  "3/21〜4/19"),
    (4, 20, 5, 20, "牡牛座",  "Taurus",      "earth", "4/20〜5/20"),
    (5, 21, 6, 21, "双子座",  "Gemini",      "air",   "5/21〜6/21"),
    (6, 22, 7, 22, "蟹座",    "Cancer",      "water", "6/22〜7/22"),
    (7, 23, 8, 22, "獅子座",  "Leo",         "fire",  "7/23〜8/22"),
    (8, 23, 9, 22, "乙女座",  "Virgo",       "earth", "8/23〜9/22"),
    (9, 23, 10, 23, "天秤座", "Libra",       "air",   "9/23〜10/23"),
    (10, 24, 11, 22, "蠍座",  "Scorpio",     "water", "10/24〜11/22"),
    (11, 23, 12, 21, "射手座","Sagittarius", "fire",  "11/23〜12/21"),
    (12, 22, 12, 31, "山羊座","Capricorn",   "earth", "12/22〜1/19"),
]

ELEMENT_EN = {"fire": "fire", "earth": "earth", "air": "air", "water": "water"}

DAYS_IN_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def get_zodiac(month, day):
    """誕生日から星座情報を取得"""
    for sm, sd, em, ed, ja, en, elem, rng in ZODIAC_RANGES:
        if (month == sm and day >= sd) or (month == em and day <= ed):
            return {"ja": ja, "en": en, "element": elem, "range": rng}
    return None


def get_life_path(month, day):
    """運命数を計算（マスターナンバー11/22/33は保持）"""
    digits = list(str(month) + str(day))
    total = sum(int(d) for d in digits)
    while total > 9 and total not in (11, 22, 33):
        total = sum(int(d) for d in str(total))
    return total


def is_valid_date(month, day):
    return 1 <= day <= DAYS_IN_MONTH[month - 1]


def call_openai(system, user, max_tokens=4000):
    """OpenAI APIを呼び出してJSONを返す"""
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": max_tokens,
        "temperature": 0.85,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as res:
                data = json.loads(res.read())
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                return json.loads(content), usage
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="ignore")
            print(f"    [retry {attempt+1}] HTTPError {e.code}: {err[:200]}")
            time.sleep(5 * (attempt + 1))
        except Exception as e:
            print(f"    [retry {attempt+1}] {type(e).__name__}: {e}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("OpenAI API failed after 3 retries")


def generate_ja(month, day):
    """日本語版データ生成"""
    z = get_zodiac(month, day)
    lp = get_life_path(month, day)

    system = """あなたは占星術と数秘術に精通し、薬剤師としての医学的知見を持つ占い記事ライターです。
誕生日占いの記事データをJSON形式で生成します。

【執筆ルール】
- 各セクションは指定の文字数程度でしっかり書く
- 薬剤師視点（体質・健康フード・セルフケア）を必ず含む
- 薬機法配慮：「○○と言われています」「サポート目的」等、効果効能の断定を避ける
- 治療目的の表現、特定の市販薬の推奨、診断を示唆する表現は避ける
- 占星術の四元素（火・地・風・水）と東洋医学体質論を融合
- 有名人は実在の人物を6名（日本人＋海外の有名人ミックス）
- 相性の良い/悪い誕生日は、星座の伝統的な相性論に基づいて選ぶ"""

    user = f"""以下の生年月日について、誕生日占い記事データをJSON形式で生成してください。

【日付】{month}月{day}日
【星座】{z["ja"]}（{z["range"]}）
【運命数】{lp}
【元素】{z["element"]}（火=情熱・地=堅実・風=知性・水=感情）

以下の構造でJSONを出力してください（全フィールド必須・配列の要素数も指定通り）:

{{
  "month": {month},
  "day": {day},
  "zodiac": "{z["ja"]}",
  "zodiacRange": "{z["range"]}",
  "lifePathNumber": {lp},
  "personality": {{
    "headline": "20字程度のキャッチフレーズ",
    "keywords": ["3つのキーワード", "...", "..."],
    "description": "500字程度の性格説明（星座×運命数の組み合わせを踏まえる）",
    "strengths": ["長所4つ", "...", "...", "..."],
    "weaknesses": ["短所4つ", "...", "...", "..."],
    "theme": "100字程度の人生のテーマ"
  }},
  "love": "400字程度の恋愛・結婚運",
  "career": {{
    "description": "200字程度の仕事・適職説明",
    "jobs": ["向いている職業5つ", "...", "...", "...", "..."]
  }},
  "compatibility": {{
    "best": [
      {{"date": "○月○日", "zodiac": "○○座", "reason": "相性理由"}},
      {{"date": "○月○日", "zodiac": "○○座", "reason": "相性理由"}},
      {{"date": "○月○日", "zodiac": "○○座", "reason": "相性理由"}}
    ],
    "challenging": [
      {{"date": "○月○日", "zodiac": "○○座", "reason": "注意理由"}},
      {{"date": "○月○日", "zodiac": "○○座", "reason": "注意理由"}},
      {{"date": "○月○日", "zodiac": "○○座", "reason": "注意理由"}}
    ]
  }},
  "luckyItems": {{
    "colors": ["カラー2つ", "..."],
    "stones": ["誕生石2つ（{month}月の伝統的な誕生石）", "..."],
    "flower": "誕生花（{month}月{day}日らしい花）",
    "flowerMeaning": "花言葉",
    "numbers": [ラッキー数字2つ],
    "direction": "ラッキー方位"
  }},
  "constitution": {{
    "description": "200字程度の体質傾向（{z["ja"]}が象徴する身体部位＋{z["element"]}元素の特性×東洋医学体質論）",
    "watchPoints": ["気をつけたい傾向3つ", "...", "..."],
    "seasonalNote": "100字程度の季節ケアアドバイス"
  }},
  "luckyFoods": {{
    "foods": [
      {{"name": "食材1", "reason": "なぜ良いか（栄養成分や働き）"}},
      {{"name": "食材2", "reason": "なぜ良いか"}},
      {{"name": "食材3", "reason": "なぜ良いか"}}
    ],
    "herbs": [
      {{"name": "ハーブ1", "reason": "効能"}},
      {{"name": "ハーブ2", "reason": "効能"}}
    ]
  }},
  "selfCare": {{
    "description": "100字程度のセルフケア主軸",
    "habits": ["おすすめ習慣4つ", "...", "...", "..."],
    "stressManagement": "150字程度のストレス対処法"
  }},
  "famousPeople": ["6名（日本人3名＋海外3名ミックス、職業も併記）", "...", "...", "...", "...", "..."]
}}"""

    return call_openai(system, user, max_tokens=4500)


def generate_en(ja_data):
    """日本語データを翻訳して英語版生成"""
    system = """You are a professional translator and astrology content writer for an English-speaking wellness audience (US/UK/Australia).
Translate the Japanese birthday horoscope data to natural, engaging English while preserving the EXACT JSON structure."""

    user = f"""Translate this Japanese birthday horoscope JSON to natural English. Preserve the exact JSON structure and all keys.

Translation rules:
- Use English zodiac names (Aries, Taurus, Gemini, etc.)
- Convert dates like "4月12日" to "April 12" format
- Use ordinal dates in compatibility (e.g., "April 12" not "April 12th")
- For famous people, keep Japanese names romanized + add international flair
- Make text natural for English readers, not literal translation
- Keep pharmacist wellness sections accurate and culturally adapted
- Preserve placeholder structure: month/day are numbers, lifePathNumber is a number, numbers in luckyItems are array of numbers

Source JSON:
{json.dumps(ja_data, ensure_ascii=False)}"""

    return call_openai(system, user, max_tokens=4500)


def save_json(month, day, data, lang):
    dir_path = DATA_DIR_JA if lang == "ja" else DATA_DIR_EN
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{month:02d}-{day:02d}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return file_path


def process_day(month, day):
    """指定日の日英両データを生成・保存"""
    print(f"\n📅 {month:02d}月{day:02d}日")

    # 既存ファイルチェック
    ja_path = DATA_DIR_JA / f"{month:02d}-{day:02d}.json"
    en_path = DATA_DIR_EN / f"{month:02d}-{day:02d}.json"
    if ja_path.exists() and en_path.exists():
        print(f"   ⏭  既に両方あるのでスキップ")
        return 0, 0

    total_in, total_out = 0, 0

    # 日本語生成
    print("   📝 日本語生成中...", end="", flush=True)
    ja_data, usage_ja = generate_ja(month, day)
    save_json(month, day, ja_data, "ja")
    total_in += usage_ja.get("prompt_tokens", 0)
    total_out += usage_ja.get("completion_tokens", 0)
    print(f" ✓ ({usage_ja.get('total_tokens', 0)} tokens)")

    time.sleep(1)

    # 英語生成
    print("   🌐 英訳中...", end="", flush=True)
    en_data, usage_en = generate_en(ja_data)
    save_json(month, day, en_data, "en")
    total_in += usage_en.get("prompt_tokens", 0)
    total_out += usage_en.get("completion_tokens", 0)
    print(f" ✓ ({usage_en.get('total_tokens', 0)} tokens)")

    return total_in, total_out


def main():
    args = sys.argv[1:]

    # 対象日決定
    if "--all" in args:
        days = [(m, d) for m in range(1, 13) for d in range(1, 32) if is_valid_date(m, d)]
    elif "--date" in args:
        i = args.index("--date")
        m, d = map(int, args[i + 1].split("-"))
        days = [(m, d)]
    else:
        # テスト3日分
        days = [(1, 1), (6, 15), (12, 31)]

    print(f"=== 誕生日占いデータ生成 ({len(days)}日分) ===")
    print(f"モデル: {MODEL}")
    print(f"保存先: {DATA_DIR_JA.relative_to(PROJECT_DIR)}, {DATA_DIR_EN.relative_to(PROJECT_DIR)}")

    total_in, total_out = 0, 0
    failed = []
    for i, (month, day) in enumerate(days, 1):
        print(f"\n[{i}/{len(days)}]", end="")
        try:
            ti, to = process_day(month, day)
            total_in += ti
            total_out += to
        except Exception as e:
            print(f"   ✗ FAILED: {e}")
            failed.append(f"{month:02d}-{day:02d}")
        time.sleep(1)

    # コスト計算（GPT-4o-mini: input $0.15/M, output $0.6/M）
    cost_usd = (total_in / 1_000_000) * 0.15 + (total_out / 1_000_000) * 0.60
    cost_jpy = cost_usd * 150  # 概算

    print(f"\n=== 完了 ===")
    print(f"成功: {len(days) - len(failed)}/{len(days)}")
    if failed:
        print(f"失敗: {failed}")
    print(f"トークン: input={total_in:,} output={total_out:,}")
    print(f"概算コスト: ${cost_usd:.4f} (約{cost_jpy:.1f}円)")


if __name__ == "__main__":
    main()
