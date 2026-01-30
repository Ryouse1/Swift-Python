from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import io, sys, ast

app = FastAPI()

# CORS設定（iPad Playgroundからアクセス可能にする）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ASTで禁止するノード
FORBIDDEN_NODES = (ast.Import, ast.ImportFrom, ast.Exec, ast.Global)

def is_safe_code(code: str):
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, FORBIDDEN_NODES):
                return False, f"Forbidden syntax detected: {type(node).__name__}"
        return True, ""
    except Exception as e:
        return False, str(e)

@app.post("/run")
async def run_python(request: Request):
    code = (await request.body()).decode()

    # ASTで危険判定
    safe, msg = is_safe_code(code)
    if not safe:
        return {"error": msg}

    # 標準出力をキャプチャ
    buffer = io.StringIO()
    stdout_backup = sys.stdout
    sys.stdout = buffer

    try:
        # builtins制限なし
        exec(code)
        sys.stdout = stdout_backup
        return {"result": buffer.getvalue()}
    except Exception as e:
        sys.stdout = stdout_backup
        return {"error": str(e)}
