from fastapi import FastAPI
from pydantic import BaseModel
import ast, io, contextlib

app = FastAPI()

# ===== 危険判定 =====
FORBIDDEN_CALLS = {"exec", "eval", "compile", "__import__", "open"}
FORBIDDEN_MODULES = {"os", "sys", "subprocess", "socket", "pathlib", "shutil"}

class Detector(ast.NodeVisitor):
    def __init__(self):
        self.bad = None

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                self.bad = f"Forbidden function: {node.func.id}"
        if isinstance(node.func, ast.Attribute):
            if node.func.attr.startswith("__"):
                self.bad = f"Dunder access: {node.func.attr}"
        self.generic_visit(node)

    def visit_Import(self, node):
        for n in node.names:
            if n.name.split(".")[0] in FORBIDDEN_MODULES:
                self.bad = f"Forbidden module: {n.name}"

    def visit_ImportFrom(self, node):
        if node.module and node.module.split(".")[0] in FORBIDDEN_MODULES:
            self.bad = f"Forbidden module: {node.module}"

def is_safe(code: str):
    tree = ast.parse(code)
    d = Detector()
    d.visit(tree)
    return d.bad

# ===== sandbox =====
SAFE_BUILTINS = {
    "print": print,
    "range": range,
    "len": len,
    "int": int,
    "float": float,
    "str": str,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "sum": sum,
    "min": min,
    "max": max,
}

class Code(BaseModel):
    code: str

@app.post("/run")
def run(code: Code):
    bad = is_safe(code.code)
    if bad:
        return {"ok": False, "error": bad}

    env = {"__builtins__": SAFE_BUILTINS}
    buf = io.StringIO()

    try:
        with contextlib.redirect_stdout(buf):
            exec(code.code, env, {})
    except Exception as e:
        return {"ok": False, "error": str(e)}

    return {"ok": True, "output": buf.getvalue()}
