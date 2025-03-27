from esphome import git
import utils

def init_submodules(path=utils.root_path):
    utils.logger.info("Initializing submodules...")
    try:
        git.run_git_command([
            "git", "submodule", "update", "--init"
        ], path)
    except:
        logger.error("Failed to update submodules")

def get_submodules_status(path=utils.root_path):
	submodules_status = ""
	try:
		submodules_status = git.run_git_command([
		    "git", "submodule", "status"
		], path)
	except:
		logger.error("Failed to get submodules status")
	return submodules_status

def get_commit_tag(path=utils.root_path):
    try:
        commit_tag = git.run_git_command(['git', 'describe', '--tags', '--always', '--dirty'], path)
    except:
        logger.warning("Failed to extract git commit tag, defaulting to main")
        commit_tag = "main"
    return commit_tag

def get_user_repo_name(path=utils.root_path):
    try:
        user_repo = git.run_git_command(['git', 'remote', 'get-url', 'origin'], path).replace("https://github.com/","").replace(".git","")
    except:
        logger.warning("Failed to extract git user and repo name, defaulting to jbdman/esphome-config-backup")
        user_repo = "jbdman/esphome-config-backup"
    return user_repo