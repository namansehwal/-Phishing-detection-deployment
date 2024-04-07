import os
import datetime
import requests


def get_changed_file(directory):
    # today's date
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(directory, date + ".log")

    return file_path


def to_github(
    repo_owner,
    repo_name,
    branch_name,
    github_token,
    commit_message,
    file_path,
):
    if file_path is None:
        print("No file to commit. Skipping.")
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

    # Get content of the file
    with open(file_path, "r", encoding="utf-8") as file:
        file_content = file.read()

    # Create a new tree with the updated file
    tree_data = {
        "base_tree": latest_commit_sha,
        "tree": [
            {
                "path": file_path.split("/")[-1],  # Only take the filename
                "mode": "100644",
                "content": file_content,
            }
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
    log_directory = "./logs"
    repo_owner = "namansehwal"
    repo_name = "Phishing-detection-based-Associative-Classification-data-mining"
    branch_name = "logs"
    from dotenv import load_dotenv

    load_dotenv()
    github_token = os.environ["GITHUB_TOKEN"]
    # print("GitHub Token is ", github_token)

    file_path = get_changed_file(log_directory)

    to_github(
        repo_owner,
        repo_name,
        branch_name,
        github_token,
        commit_message,
        file_path,
    )


# # Call commit_to_github with your commit message
# commit_to_github("Your commit message here")
