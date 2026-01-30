from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import io, sys, ast

app = FastAPI()

# CORS設定（iPadからアクセス可能）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 危険構文ノード
FORBIDDEN_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.Global,
    # ast.Exec は Python 3.13 では存在しないので削除
)

# 危険な関数呼び出し
FORBIDDEN_CALLS = {"open", "eval", "exec", "__import__", "compile"}

def is_safe_code(code: str):
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, FORBIDDEN_NODES):
                return False, f"Forbidden syntax: {type(node).__name__}"
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name in FORBIDDEN_CALLS:
                    return False, f"Forbidden function call: {func_name}"
        return True, ""
    except Exception as e:
        return False, str(e)

@app.post("/run")
async def run_python(request: Request):
    code = (await request.body()).decode()
    
    safe, msg = is_safe_code(code)
    if not safe:
        return {"error": msg}
    
    buffer = io.StringIO()
    stdout_backup = sys.stdout
    sys.stdout = buffer

    try:
        exec(code)  # builtins制限なし
        sys.stdout = stdout_backup
        return {"result": buffer.getvalue()}
    except Exception as e:
        sys.stdout = stdout_backup
        return {"error": str(e)}
