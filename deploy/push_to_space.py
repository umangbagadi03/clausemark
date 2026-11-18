"""Uploads the app to a Hugging Face Space, which builds it with the Dockerfile.

First log in once in your own terminal: .venv/bin/hf auth login
Then run: .venv/bin/python deploy/push_to_space.py <your-hf-username>/clausemark
"""
import sys

from huggingface_hub import HfApi

# The same files Docker leaves out, plus the GitHub README (the Space gets its own)
SKIP = [
    ".git/*", ".github/*", ".venv/*", ".env", ".claude/*", ".pytest_cache/*",
    "__pycache__/*", "*/__pycache__/*", "*.pyc", "data/*", "results/*", "notes/*",
    "model_cache/*", ".DS_Store", "README.md",
]


def main():
    if len(sys.argv) != 2:
        print("Usage: python deploy/push_to_space.py <your-hf-username>/clausemark")
        return

    space_id = sys.argv[1]
    api = HfApi()

    api.create_repo(space_id, repo_type="space", space_sdk="docker", exist_ok=True)
    api.upload_folder(
        folder_path=".",
        repo_id=space_id,
        repo_type="space",
        ignore_patterns=SKIP,
        commit_message="Update the app",
    )
    api.upload_file(
        path_or_fileobj="deploy/space_readme.md",
        path_in_repo="README.md",
        repo_id=space_id,
        repo_type="space",
        commit_message="Update the Space card",
    )

    owner, name = space_id.split("/")
    print("Uploaded. It builds in a few minutes at:")
    print("https://huggingface.co/spaces/" + space_id)
    print("The app itself: https://" + owner + "-" + name + ".hf.space")


if __name__ == "__main__":
    main()
