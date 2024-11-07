import multiprocessing
import uvicorn

def run_main():
    uvicorn.run(
        "main:app",  #
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

def run_service():
    uvicorn.run(
        "service_main:app",
        host="0.0.0.0",
        port=8003,
        log_level="info",
    )

if __name__ == "__main__":
    process_1 = multiprocessing.Process(target=run_main)
    process_2 = multiprocessing.Process(target=run_service)

    process_1.start()
    process_2.start()

    process_1.join()
    process_2.join()