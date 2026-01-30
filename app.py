from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import io
import sys

app = FastAPI()

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 公開時は特定のドメインだけに
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/run")
async def run_python(request: Request):
    code = await request.body()
    code_str = code.decode()

    # 標準出力をキャプチャ
    buffer = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = buffer

    try:
        exec(code_str, {})
        sys.stdout = sys_stdout
        return {"result": buffer.getvalue()}
    except Exception as e:
        sys.stdout = sys_stdout
        return {"error": str(e)}
