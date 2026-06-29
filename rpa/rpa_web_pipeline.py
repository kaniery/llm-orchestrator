# rpa_web_pipeline.py
import re
import os
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

# ==========================================
# 1. テキスト解析モジュール
# ==========================================
def extract_value_from_txt(file_path: str, target_key: str) -> str:
    """
    テキストファイルから特定のキーに紐づく文字列を抽出する。
    例: "注文番号: 12345" という行から "12345" だけを抜き出す。
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    for line in lines:
        if target_key in line:
            # キーワード（例："注文番号:"）以降の文字列を取得し、空白や改行を削除
            extracted_str = line.split(target_key)[-1].strip()
            # 抽出した文字列から、さらに不要な記号（コロンやスペース）を正規表現でクリーニング
            clean_str = re.sub(r'^[:：\s]+', '', extracted_str)
            return clean_str
            
    raise ValueError(f"ファイル内にキー '{target_key}' が見つかりませんでした。")


# ==========================================
# 2. Web操作モジュール（Playwrightラッパー）
# ==========================================
def safe_web_fill(page: Page, selector: str, input_text: str, timeout_ms: int = 15000):
    """
    Webの入力欄が「表示され、操作可能になるまで」待機してからテキストを入力する。
    PyAutoGUIのクリップボードペーストの代わりとなる、Web特化の堅牢な入力方式。
    """
    try:
        # 要素がDOM上に存在し、かつ表示されている状態になるまで待機
        page.wait_for_selector(selector, state="visible", timeout=timeout_ms)
        
        # 既存の入力値をクリアしてから、確実に入力（人間のタイピングをシミュレート）
        page.fill(selector, "")
        page.type(selector, input_text, delay=50) # AI検知システム回避のため少し遅延を入れる
        
    except PlaywrightTimeoutError:
        # エラー時は自動でスクリーンショットを保存
        os.makedirs("./rpa_logs", exist_ok=True)
        page.screenshot(path="./rpa_logs/web_timeout_error.png")
        raise TimeoutError(f"タイムアウト: 入力対象の要素({selector})が画面に表示されませんでした。")