import multiprocessing
import uvicorn

def run_main():
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        log_level="info",
    )

if __name__ == "__main__":
    process_1 = multiprocessing.Process(target=run_main())
    process_1.start()
    process_1.join()