from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import io, sys, ast

app = FastAPI()

# CORS設定
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
)

# 危険関数
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
    data = await request.json()
    code = data.get("code", "")
    input_values = data.get("input_values", [])
    input_iter = iter(input_values)

    safe, msg = is_safe_code(code)
    if not safe:
        return {"error": msg}

    buffer = io.StringIO()
    stdout_backup = sys.stdout
    sys.stdout = buffer

    # input() の安全な上書き
    def safe_input(prompt=""):
        try:
            return next(input_iter)
        except StopIteration:
            return ""

    try:
        exec_globals = {"input": safe_input, "__builtins__": __builtins__}
        exec(code, exec_globals)
        sys.stdout = stdout_backup
        return {"result": buffer.getvalue()}
    except Exception as e:
        sys.stdout = stdout_backup
        return {"error": str(e)}
