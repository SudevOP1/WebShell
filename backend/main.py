from fastapi import FastAPI

app = FastAPI()


@app.get("/hi")
def hi():
    return {"success": True, "msg": "hi"}
