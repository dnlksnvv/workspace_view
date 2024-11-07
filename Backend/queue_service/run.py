import uvicorn

from config import this_port

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=this_port,
        reload=True
    )