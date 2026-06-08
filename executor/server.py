from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import tempfile
import os

app = FastAPI()

class CodeRequest(BaseModel):
    code: str

@app.post("/execute")
def execute_code(request: CodeRequest):
    # 一時ファイルにコードを書き込んで実行する
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(request.code)
        temp_file_path = temp_file.name

    try:
        # サンドボックス実行 (タイムアウト5秒)
        result = subprocess.run(
            ['python', temp_file_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # 標準エラーがあればエラーとして返す
        if result.stderr:
            return {"status": "error", "output": result.stderr}
            
        return {"status": "success", "output": result.stdout}
        
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "Execution timed out (5s)."}
    except Exception as e:
        return {"status": "error", "output": str(e)}
    finally:
        os.remove(temp_file_path)