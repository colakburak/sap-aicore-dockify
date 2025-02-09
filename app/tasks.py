import logging
import docker
from celery import Celery
from app.tasks_utils import build_image, push_image


# logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


app = Celery('tasks', backend='rpc://', broker='amqp://localhost')


@app.task
def build_and_push_image(
    user_name: str,
    repo: str,
    tag: str,
    dockerfile: bytes,
    optional_files: dict,
    password: str = None,
) -> str:
    client = docker.from_env()

    if password:
        client.login(username=user_name, password=password)
        
    image_reference = f"{user_name}/{repo}:{tag}"
    logger.info("Building image: %s", image_reference)
    try:
        build_image(client, image_reference, dockerfile, optional_files)
    except Exception as e:
        logger.error("Error during build step: %s", e)
        return {
            "status": "failed",
            "step": "build",
            "error": str(e)
        }
    
    try:
        push_image(client, image_reference)
    except Exception as e:
        logger.error("Error during push step: %s", e)
        return {
            "status": "failed",
            "step": "push",
            "error": str(e)
        }

    # Image URL from docker hub This can be changed to any other registry
    url = "https://hub.docker.com/r/" + user_name + "/" + repo
    logger.info("Image URL: %s", url)

    return {
        "status": "success",
        "image_url": url,
        "image_reference": image_reference
    } 

