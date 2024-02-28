import os
import subprocess
import argparse

def update_from_repo(folder, branch='main', proxy=None):
    try:
        if proxy:
            os.environ['http_proxy'] = proxy
            os.environ['https_proxy'] = proxy
        folder = folder.replace("logger.sh", "")
        folder = folder.replace("reporter.sh", "")
        subprocess.check_call(['git', 'stash'], cwd=folder)
        subprocess.check_call(['git', 'checkout', branch], cwd=folder)
        # Fetch the latest changes
        subprocess.check_call(['git', 'pull'], cwd=folder)
        # Reset the repository to the latest commit on the specified branch
        #subprocess.check_call(['git', 'reset', '--hard', f'origin/{branch}'], cwd=folder)
        # Clean up any untracked files
        #subprocess.check_call(['git', 'clean', '-fd'], cwd=folder)
        print(f"Repositorio actualizado a la última versión de la rama '{branch}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error al actualizar el repositorio: {e}")



def main(repo_path, branch, proxy=None):
    print(f"Updating repo from {repo_path}  {branch}.")
    update_from_repo(repo_path, branch, proxy)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update repo from Git.')
    parser.add_argument('repo_path', help='Repo url')
    parser.add_argument('branch', help='Branch name')
    args = parser.parse_args()

    main(args.repo_path, args.branch)