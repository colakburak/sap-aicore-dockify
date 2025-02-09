from fastapi import FastAPI, UploadFile, HTTPException
from celery.result import AsyncResult

from app.tasks import build_and_push_image

app = FastAPI()


@app.get("/", status_code=418)
def root():
    return {"message": "Please go to /docs to interect with API"}


@app.post("/build")
async def build_image(
    user_name: str,
    repo: str,
    dockerfile: UploadFile,
    tag: str = "latest",
    optional_files: list[UploadFile] = [],
    password: str = None,
):

    # DockerFile Reading
    if not dockerfile.filename.lower().endswith("dockerfile"):
        raise HTTPException(
            status_code=418,
            detail="[API] Uploaded file seems like not a Dockerfile!"
        )

    try:
        dockerfileb = await dockerfile.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"[API] Failed to read Dockerfile: {str(e)}"
        )

    # Optional File Reading
    files_dict = {}
    if optional_files:
        for file in optional_files:
            try:
                files_dict[file.filename] = await file.read()
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"[API] Failed to read optional file '{file.filename}': {str(e)}"
                )
    
    task = build_and_push_image.delay(
        user_name,
        repo,
        tag,
        dockerfileb,
        files_dict,
        password
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
        return results.result
    return {"status": "processing"}
