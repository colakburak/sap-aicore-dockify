import os
import tempfile

from celery import Celery
import docker

from app.tasks_utils import build_image, push_image


app = Celery('tasks', backend='rpc://', broker='amqp://localhost')


@app.task
def build_and_push_image(
    user_name: str,
    repo: str,
    tag: str,
    dockerfile: bytes,
    optional_files: dict,
) -> str:
    client = docker.from_env()

    image_reference = f"{user_name}/{repo}:{tag}"
    print(f"[INFO] Building image: {image_reference}")

    build_image(client, image_reference, dockerfile, optional_files)
    push_image(client, image_reference)

    url = "https://hub.docker.com/r/" + user_name + "/" + repo
    print(f"[INFO] Image URL: {url}")

    return {"image_url": url,
            "image_reference": image_reference} 

