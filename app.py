from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# CORS 設定（iPad Playground からアクセスできるように）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 公開時は特定ドメインだけにするのがおすすめ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/run")
async def run_python(request: Request):
    code = await request.body()
    code_str = code.decode()
    try:
        local_vars = {}
        exec(code_str, {}, local_vars)
        return {"result": str(local_vars)}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
