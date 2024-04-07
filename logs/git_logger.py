import os
import datetime
import requests


def get_changed_files(directory):
    # Retrieve list of changed log files
    changed_files = []
    # today date
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(os.path.dirname(__file__), date + ".log")
    changed_files.append(file_path)
    print("Changed files are ", changed_files)
    return changed_files


def to_github(
    repo_owner,
    repo_name,
    branch_name,
    github_token,
    commit_message,
    files,
    log_directory,
):
    if not files:
        print("No files have changed. Skipping commit.")
        return

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs/heads/{branch_name}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Get the latest commit SHA for the branch
    response = requests.get(url, headers=headers)
    response_json = response.json()
    print(response_json)
    # Check if 'object' key exists in the response
    if "object" not in response_json:
        print("Error: 'object' key not found in response.")
        return

    latest_commit_sha = response_json["object"]["sha"]

    # Create a new tree with the updated files
    tree_data = {
        "base_tree": latest_commit_sha,
        "tree": [
            {
                "path": file_path.split("/")[-1],  # Only take the filename
                "mode": "100644",
                "content": open(
                    file_path, "r", encoding="utf-8"
                ).read(),  # Specify encoding
            }
            for file_path in files
        ],
    }
    response = requests.post(
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/trees",
        json=tree_data,
        headers=headers,
    )
    tree_sha = response.json()["sha"]
    commit_data = {
        "message": commit_message,
        "parents": [latest_commit_sha],
        "tree": tree_sha,
    }
    response = requests.post(
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/commits",
        json=commit_data,
        headers=headers,
    )
    commit_sha = response.json()["sha"]

    # Update the branch reference to the new commit
    ref_data = {"sha": commit_sha}
    response = requests.patch(url, json=ref_data, headers=headers)


def commit_to_github(commit_message):
    log_directory = "./"
    repo_owner = "namansehwal"
    repo_name = "Phishing-detection-based-Associative-Classification-data-mining"
    branch_name = "logs"
    from dotenv import load_dotenv

    load_dotenv()
    github_token = os.environ["GITHUB_TOKEN"]
    # print("GitHub Token is ", github_token)
    files = get_changed_files(log_directory)

    to_github(
        repo_owner,
        repo_name,
        branch_name,
        github_token,
        commit_message,
        files,
        log_directory,
    )
