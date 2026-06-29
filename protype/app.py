import pyautogui
import pyperclip

pyautogui.FAILSAFE = True  # マウスが四隅に達するとマクロを停止
pyautogui.PAUSE = 0.5      # 各操作間の待ち時間（秒）
 
# アドレスバーに移動する座標（仮）
address_bar_coords = (100, 100)  # 実際の座標は変更が必要
 
# アドレスバーをクリック
pyautogui.click(address_bar_coords)
 
# https://google.com を入力
pyperclip.copy("https://google.com")  # URLをクリップボードにコピー
pyautogui.hotkey('ctrl', 'v')          # Ctrl + Vで貼り付け
 
# テキスト検索入力（例：日本語検索クエリ）
search_query = "例：AI技術の進歩"
pyperclip.copy(search_query)
time.sleep(2)  # URL入力完了後にsleep
pyautogui.press('enter')               # Enterキーを押して検索
 
# 検索結果画面で、日本語のテキストが入力される位置に移動（座標例）
input_coords = (500, 300)
pyautogui.moveRel(*input_coords)       # 移動する
time.sleep(1)                          # 移動完了後にsleep
 
# 日本語の文字をタイピング
pyperclip.copy(search_query)
pyautogui.write(search_query, interval=0.1)
 
# 画面をスクリーンショット（オプション）
screenshot = pyautogui.screenshot()
screenshot.save("search_result.png")