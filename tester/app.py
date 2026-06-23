import os
import sys
import boto3
import requests

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
    query = "私の名前は？"
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
        res = requests.post(
            OLLAMA_URL, 
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False  # 今回は検証用のため一括で取得
            },
            timeout=90  # ローカルの推論速度に合わせてタイムアウトを長めに設定
        )
        
        if res.status_code == 200:
            answer = res.json().get('response', '')
            print("\n✨ --- [ローカルAIからの最終回答] --- ✨")
            print(answer)
            print("---------------------------------------")
        else:
            print(f"❌ Ollamaエラー: Status Code {res.status_code} - {res.text}")
            
    except Exception as e:
        print(f"❌ Ollamaとの通信に失敗しました (URL: {OLLAMA_URL}): {e}")

if __name__ == "__main__":
    run_hybrid_rag()