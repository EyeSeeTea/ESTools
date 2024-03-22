import subprocess
import argparse

def update_from_repo(folder, branch='main'):
    try:
        folder = folder.replace("logger.sh", "")
        folder = folder.replace("reporter.sh", "")
        subprocess.check_call(['git', 'stash'], cwd=folder)
        subprocess.check_call(['git', 'checkout', branch], cwd=folder)
        # Fetch the latest changes
        subprocess.check_call(['git', 'pull'], cwd=folder)
        
        print(f"Repository updated '{branch}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error updating repository: {e}")



def main(repo_folder, branch):
    print(f"Updating repo in {repo_folder}  {branch}.")
    update_from_repo(repo_folder, branch)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update repo from Git.')
    parser.add_argument('repo_folder', help='Repo folder')
    parser.add_argument('branch', help='Branch name')
    args = parser.parse_args()

    main(args.repo_folder, args.branch)