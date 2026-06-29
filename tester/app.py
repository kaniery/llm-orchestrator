import os
import sys
import boto3
import requests
import re

# 1. 環境変数の読み込み（設定漏れがあればエラーを吐いて落とす安全設計）
AWS_REGION = os.environ.get("AWS_REGION")
KB_ID = os.environ.get("AWS_KNOWLEDGE_BASE_ID")
OLLAMA_BASE = os.environ.get("LLM_API_BASE")
MODEL_NAME = os.environ.get("OLLAMA_MODEL")

if not all([AWS_REGION, KB_ID, OLLAMA_BASE, MODEL_NAME]):
    print("エラー: .env ファイルの設定が不足しています。確認してください。")
    sys.exit(1)

OLLAMA_URL = f"{OLLAMA_BASE}/api/generate"

def run_hybrid_rag():
    query = "Please write a Python macro that presses the Windows key, types “notepad,” and, once Notepad launches, types “Hello” into Notepad.                 "  # ここにユーザーからの質問を入れる
    print(f"🧐 ユーザーからの質問: {query}")

    # 2. AWS Bedrock Knowledge Base から関連コンテキストを検索（Retrieve）
    print("🔍 AWS Bedrock ナレッジベースを検索中...")
    try:
        # 最新の agent-runtime クライアントを初期化
        bedrock_runtime = boto3.client(
            service_name='bedrock-agent-runtime', 
            region_name=AWS_REGION
        )
        
        response = bedrock_runtime.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={'text': query},
            # 必要に応じて検索件数を絞る場合は以下を有効化（デフォルトは最大5件）
            # retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': 3}}
        )
        
        retrieved_results = response.get('retrievalResults', [])
        if not retrieved_results:
            print("⚠️ ナレッジベースから関連するドキュメントが見つかりませんでした。")
            context = "（関連ドキュメントなし）"
        else:
            context = "\n".join([r['content']['text'] for r in retrieved_results])
            print(f"✅ AWSからのデータ取得成功 ({len(retrieved_results)} 件のテキスト断片を結合)")
            
    except Exception as e:
        print(f"❌ AWS Retrieve 失敗: {e}")
        return

    # 3. 取得した文脈をプロンプトに埋め込んで、ホストマシンのOllamaに送信
    prompt = f"""以下の参考ドキュメントの内容に基づいて、ユーザーからの質問に正確に答えてください。
ドキュメントに記載がない情報については、推測で答えず「記載がありません」と回答してください。

# 参考ドキュメント:
{context}

# ユーザーからの質問:
{query}

# 回回答:"""

    print(f"🚀 ローカルLLM ({MODEL_NAME}) で回答を生成中...")
    try:
        import json # ファイルの先頭になければ追加してください
        
        res = requests.post(
            OLLAMA_URL, 
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": True  # ★ここを True に変更
            },
            stream=True,     # ★requests側のストリーミングも有効化
            timeout=300      # ★最初の1文字目が出るまでの待機時間を長めに（300秒）
        )
        
        if res.status_code == 200:
            print("\n✨ --- [ローカルAIからの最終回答] --- ✨\n")
            
            full_response = "" # ★AIの回答をすべて結合するための変数
            
            # ストリーミングで返ってくるデータを1行ずつ読み込んで表示
            for line in res.iter_lines():
                if line:
                    chunk = json.loads(line)
                    text_chunk = chunk.get("response", "")
                    
                    # 画面にリアルタイム出力
                    print(text_chunk, end="", flush=True)
                    
                    # 変数にも蓄積していく
                    full_response += text_chunk
                    
            print("\n\n---------------------------------------")
            
            # ★ ここから追加：マークダウンのコードブロックだけを抽出してファイル保存
            # "```python" から "```" までの間にある文字列を抜き出す
            code_match = re.search(r'```python\n(.*?)\n```', full_response, re.DOTALL)
            
            if code_match:
                extracted_code = code_match.group(1)
                
                # generated_macro.py として同じ階層に保存
                with open("generated_macro.py", "w", encoding="utf-8") as f:
                    f.write(extracted_code)
                print("✅ 実行用マクロ (generated_macro.py) を自動保存しました！")
            else:
                print("⚠️ コードブロック (```python ... ```) が見つからなかったため、保存をスキップしました。")

        else:
            print(f"\n❌ Ollamaエラー: Status Code {res.status_code} - {res.text}")

if __name__ == "__main__":
    run_hybrid_rag()