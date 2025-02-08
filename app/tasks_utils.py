import os
import tempfile

import docker

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
            print(f"[BUILD] Image with id: {image.id} tags:{image.tags} built successfully.")
            return image_reference
        except docker.errors.BuildError as err:
            print(f"[BUILD] [BUILD ERROR] {err}")
            raise
        except docker.errors.APIError as err:
            print(f"[BUILD] [API ERROR] {err}")
            raise
        except Exception as err:
            print(f"[BUILD] [ERROR] {err}")
            raise

def push_image(
    client: docker.DockerClient,
    image_reference: str,
) -> str:
    # pushing the img to repo
    try:
        push = client.images.push(image_reference, stream=True, decode=True)

        for log in push:
            print(f"[PUSH] {log}")

        print(f"[PUSH] Image {image_reference} pushed to the registry.")
        
        return image_reference
    except docker.errors.APIError as err:
        print(f"[PUSH ERROR] {err}")
        raise
    except Exception as err:
        print(f"[PUSH ERROR] {err}")
        raise