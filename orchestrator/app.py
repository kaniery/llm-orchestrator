import requests
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

# ==========================================
# 1. State（状態）の定義
# ==========================================
class AgentState(TypedDict):
    requirements: str      # オーケストレーターが作成した要件・テストケース
    current_code: str      # コーダーが生成した最新のPythonコード
    execution_result: str  # Dockerでの実行結果・エラー
    feedback: str          # エバリュエーターによる修正指示
    loop_count: int        # 無限ループ防止用のカウンター

# ==========================================
# 2. 各ノードの定義
# ==========================================
def orchestrator_node(state: AgentState):
    print("\n--- [Node] Orchestrator: 要件の定義 ---")
    user_prompt = "ユーザーからの入力（例: データを集計してグラフ化するマクロ）"
    return {
        "requirements": f"【要件】{user_prompt} を満たすPython関数を実装せよ。",
        "loop_count": 0
    }

def coder_node(state: AgentState):
    print(f"\n--- [Node] Coder: コード生成 (試行回数: {state.get('loop_count', 0) + 1}) ---")
    
    # モック用のダミーコード（最初はわざとエラーになるコードを生成）
    if state.get("loop_count", 0) == 0:
        generated_code = "print(undefined_variable)" 
    else:
        generated_code = "print('Hello, Python Macro successfully executed in Docker!')"
        
    return {
        "current_code": generated_code,
        "loop_count": state.get("loop_count", 0) + 1
    }

def executor_node(state: AgentState):
    print("\n--- [Node] Executor: Docker環境での実行 ---")
    code_to_run = state["current_code"]
    
    try:
        # docker-compose内の "executor" コンテナへPOST通信
        response = requests.post(
            "http://executor:8000/execute", 
            json={"code": code_to_run},
            timeout=10
        )
        result_data = response.json()
        
        if result_data["status"] == "success":
            result = f"Success:\n{result_data['output']}"
        else:
            result = f"Error:\n{result_data['output']}"
            
    except Exception as e:
        result = f"API Error: {str(e)}"
        
    print(f"-> 実行結果: {result.strip()}")
    return {"execution_result": result}

def evaluator_node(state: AgentState):
    print("\n--- [Node] Evaluator: ジャッジ ---")
    result = state["execution_result"]
    
    if "Success" in result:
        print("-> [ジャッジ] 合格")
        return {"feedback": "PASS"}
    else:
        print("-> [ジャッジ] 不合格: コードの修正を指示します")
        return {"feedback": f"コードにエラーがあります。エラー内容: {result}"}

# ==========================================
# 3. 条件付き遷移の定義
# ==========================================
def should_continue(state: AgentState) -> Literal["continue", "exit"]:
    if state.get("loop_count", 0) >= 3:
        print("\n[安全装置] ループ上限に達したため終了します。")
        return "exit"
    if state.get("feedback") == "PASS":
        return "exit"
    return "continue"

# ==========================================
# 4. グラフの構築
# ==========================================
workflow = StateGraph(AgentState)

workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("coder", coder_node)
workflow.add_node("executor", executor_node)
workflow.add_node("evaluator", evaluator_node)

workflow.set_entry_point("orchestrator")
workflow.add_edge("orchestrator", "coder")
workflow.add_edge("coder", "executor")
workflow.add_edge("executor", "evaluator")

workflow.add_conditional_edges(
    "evaluator",
    should_continue,
    {"continue": "coder", "exit": END}
)

app = workflow.compile()

# ==========================================
# 5. 実行エントリポイント
# ==========================================
if __name__ == "__main__":
    initial_state = {
        "requirements": "",
        "current_code": "",
        "execution_result": "",
        "feedback": "",
        "loop_count": 0
    }
    final_output = app.invoke(initial_state)
    print("\n==========================================")
    print("最終成果物コード:")
    print(final_output["current_code"])