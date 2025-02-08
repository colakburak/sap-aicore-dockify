from fastapi import FastAPI, UploadFile
from celery.result import AsyncResult

from app.tasks import build_and_push_image

app = FastAPI()


@app.post("/build")
async def build_image(
    user_name: str,
    repo: str,
    dockerfile: UploadFile,
    tag: str = "latest",
    optional_files: list[UploadFile] = [],
):

    # DockerFile Reading
    dockerfileb = await dockerfile.read()

    # Optional File Reading
    files_dict = {}
    for file in optional_files:
        files_dict[file.filename] = await file.read()

    task = build_and_push_image.delay(
        user_name, 
        repo, 
        tag, 
        dockerfileb, 
        files_dict, 
    )

    return {
        "task_id": task.id,
        "image_reference": f"{user_name}/{repo}:{tag}",
        "status": "Sent to processing queue",
        "data": {
            "dockerfile": dockerfile,
            "optional_files": files_dict
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
