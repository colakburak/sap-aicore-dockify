import os
import tempfile
import logging
import docker

logger = logging.getLogger(__name__)

def build_image(
    client: docker.DockerClient,
    image_reference: str,
    dockerfile: bytes,
    optional_files: dict
) -> str:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Path to the Dockerfile in the temporary directory
        dockerfile_path = os.path.join(tmp_dir, "Dockerfile")
        # Write the Dockerfile
        with open(dockerfile_path, "wb") as df:
            df.write(dockerfile)

        # Write any optional files
        for filename, content in optional_files.items():
            file_path = os.path.join(tmp_dir, filename)
            with open(file_path, "wb") as f:
                f.write(content)

        try:
            build = client.images.build(
                path=tmp_dir,
                dockerfile="Dockerfile",
                tag=image_reference,
                rm=True
            )
            image = build[0]
            logger.info("Image with id: %s and tags: %s built successfully.", image.id, image.tags)
            return image_reference
        except docker.errors.BuildError as err:
            logger.error("Build error: %s", err)
            raise
        except docker.errors.APIError as err:
            logger.error("API error: %s", err)
            raise
        except Exception as err:
            logger.error("Unexpected error during build: %s", err)
            raise

def push_image(
    client: docker.DockerClient,
    image_reference: str,
) -> str:
    # pushing the img to repo
    try:
        push = client.images.push(image_reference, stream=True, decode=True)

        for log in push:
            logger.info("Push log: %s", log)

        logger.info("Image %s pushed to the registry successfully.", image_reference)        
        return image_reference
    except docker.errors.APIError as err:
        logger.error("Push API error: %s", err)
        raise
    except Exception as err:
        logger.error("Unexpected error during push: %s", err)
        raise