from fastapi import FastAPI, UploadFile
from celery.result import AsyncResult

app = FastAPI()


@app.post("/build")
async def build_image(
    image_name: str,
    dockerfile: UploadFile,
    optional_files: list[UploadFile] = []
):

    # DockerFile Reading
    dockerfile = await dockerfile.read()

    # Optional File Reading
    files_dict = {}
    for file in optional_files:
        files_dict[file.filename] = await file.read()

    # TODO Send files and image name to celery task queue
    # Will get task_id from celery for each task
    task = {}
    task["id"] = "PLACEHOLDER-TASK-ID-123"

    return {
        "task_id": task["id"],
        "image_name": image_name,
        "status": "Sent to processing queue",
        "data": {
            "dockerfile": dockerfile,
            "optional_files": optional_files
        }
    }


@app.get("/status/{task_id}")
async def get_status(task_id: str):
    results = AsyncResult(task_id)
    if results.ready():
        return {
            "status": "Completed",
            "image_url": results.result
        }
    return {"status": "processing"}
