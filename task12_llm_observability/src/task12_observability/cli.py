import uvicorn

def main():
    uvicorn.run("task12_observability.main:app", host="127.0.0.1", port=8000, reload=True)
