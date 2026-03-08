import os
from fastapi import APIRouter, Depends, HTTPException
from git import Repo
from git.exc import BadName, GitCommandError
from typing import List, Dict, Any
from pydantic import BaseModel
import datetime

from app.core.security import require_viewer

router = APIRouter(dependencies=[Depends(require_viewer)])

# Configuration
# Default to sibling directory for development
DEFAULT_REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../JTYU-OBC"))

class CommitInfo(BaseModel):
    hexsha: str
    message: str
    author: str
    date: str


def _open_repo(repo_path: str) -> Repo:
    if not os.path.exists(repo_path):
        raise HTTPException(status_code=404, detail=f"Repository not found at {repo_path}")

    try:
        return Repo(repo_path)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Git error: {str(error)}") from error


def _serialize_commit(commit) -> Dict[str, str]:
    return {
        "hash": commit.hexsha[:7],
        "full_hash": commit.hexsha,
        "author": commit.author.name,
        "email": commit.author.email,
        "date": datetime.datetime.fromtimestamp(commit.committed_date).isoformat(),
        "message": commit.message.strip(),
    }


def _get_commits(repo_path: str, limit: int, relative_path: str = None):
    repo = _open_repo(repo_path)
    iter_kwargs = {"max_count": limit}
    if relative_path:
        iter_kwargs["paths"] = relative_path

    try:
        return [_serialize_commit(commit) for commit in repo.iter_commits(**iter_kwargs)]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Git error: {str(error)}") from error


def get_commits_list_filtered(repo_path: str, relative_path: str = None, limit: int = 50):
    """
    Get list of commits from repository, optionally filtered to a subdirectory.
    For Type-2 projects, relative_path scopes commits to the subproject.
    """
    return _get_commits(repo_path, limit, relative_path)


def _count_tree_entries(commit, relative_path: str) -> int | None:
    try:
        target = commit.tree / relative_path
        if target.type == "tree":
            return len(list(target.traverse()))
    except Exception:
        return None
    return None


def _get_releases(repo_path: str, relative_path: str = None):
    repo = _open_repo(repo_path)
    releases = []
    try:
        for tag in repo.tags:
            commit = tag.commit
            release = {
                "tag": tag.name,
                "commit_hash": commit.hexsha[:7],
                "date": datetime.datetime.fromtimestamp(commit.committed_date).isoformat(),
                "message": commit.message.strip(),
            }
            if relative_path:
                release["subproject_files_changed"] = _count_tree_entries(commit, relative_path)
            releases.append(release)

        releases.sort(key=lambda item: item["date"], reverse=True)
        return releases
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Git error: {str(error)}") from error


def get_releases_filtered(repo_path: str, relative_path: str = None):
    """
    Get list of Git tags/releases from repository.
    For Type-2 projects, shows file count under relative_path for each tag.
    """
    return _get_releases(repo_path, relative_path)


def get_file_from_commit_with_prefix(repo_path: str, commit_hash: str, file_path: str, relative_prefix: str = None) -> str:
    """
    Get file content from a specific commit.
    For Type-2 projects, relative_prefix is prepended to file_path.
    """
    try:
        repo = Repo(repo_path)
        commit = repo.commit(commit_hash)
        
        # Prepend relative_prefix for Type-2 projects
        full_path = file_path
        if relative_prefix:
            full_path = os.path.join(relative_prefix, file_path)
        
        try:
            blob = commit.tree / full_path
            content = blob.data_stream.read()
            return content.decode('utf-8')
        except KeyError:
            raise HTTPException(status_code=404, detail=f"File {file_path} not found in commit")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Binary file cannot be decoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git error: {str(e)}")


def file_exists_in_commit_with_prefix(repo_path: str, commit_hash: str, file_path: str, relative_prefix: str = None) -> bool:
    """
    Check if a file exists in a specific commit.
    For Type-2 projects, relative_prefix is prepended to file_path.
    """
    try:
        repo = Repo(repo_path)
        commit = repo.commit(commit_hash)
        
        full_path = file_path
        if relative_prefix:
            full_path = os.path.join(relative_prefix, file_path)
        
        try:
            _ = commit.tree / full_path
            return True
        except KeyError:
            return False
    except:
        return False


class FileContentRequest(BaseModel):
    repo_path: str = DEFAULT_REPO_PATH
    commit_sha: str
    file_path: str

@router.get("/commits", response_model=List[CommitInfo])
async def list_commits(repo_path: str = DEFAULT_REPO_PATH, limit: int = 50):
    """
    List commits for a given repository.
    """
    try:
        repo = _open_repo(repo_path)
        commits = []
        for commit in repo.iter_commits(max_count=limit):
            commits.append(CommitInfo(
                hexsha=commit.hexsha,
                message=commit.message.strip(),
                author=commit.author.name,
                date=datetime.datetime.fromtimestamp(commit.committed_date).isoformat()
            ))
        return commits
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Git error: {str(error)}") from error

def get_releases(repo_path: str):
    """
    Get list of Git tags/releases from repository.
    """
    return _get_releases(repo_path)

def get_commits_list(repo_path: str, limit: int = 50):
    """
    Get list of commits from repository.
    """
    return _get_commits(repo_path, limit)


def get_commit_distance(repo_path: str, commit_hash: str, relative_path: str = None) -> int:
    """
    Count commits between the requested commit and HEAD.
    When relative_path is provided, only count commits that affect that path.
    """
    try:
        repo = _open_repo(repo_path)
        repo.commit(commit_hash)

        rev_list_args = ["--count", f"{commit_hash}..HEAD"]
        if relative_path:
            rev_list_args.extend(["--", relative_path])

        return int(repo.git.rev_list(*rev_list_args).strip() or "0")
    except BadName as error:
        raise HTTPException(status_code=404, detail=f"Commit not found: {commit_hash}") from error
    except GitCommandError as error:
        message = str(error).lower()
        if "bad revision" in message or "unknown revision" in message:
            raise HTTPException(status_code=404, detail=f"Commit not found: {commit_hash}") from error
        raise HTTPException(status_code=500, detail=f"Git error: {str(error)}") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Git error: {str(error)}") from error

@router.get("/content")
async def get_file_content(commit_sha: str, file_path: str, repo_path: str = DEFAULT_REPO_PATH):
    """
    Get file content from a specific commit.
    """
    try:
        repo = _open_repo(repo_path)
        commit = repo.commit(commit_sha)
        
        try:
            target_file = commit.tree / file_path
            # For text files, we decode. For binaries, we might need a different strategy (e.g. base64)
            # For now, let's assume text or try to decode utf-8
            blob = target_file.data_stream.read()
            return {"content": blob.decode('utf-8'), "size": target_file.size}
        except KeyError:
             raise HTTPException(status_code=404, detail=f"File {file_path} not found in commit {commit_sha}")
        except UnicodeDecodeError:
             return {"content": "Binary file (preview not available)", "size": target_file.size, "is_binary": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git error: {str(e)}")

def get_file_from_commit(repo_path: str, commit_hash: str, file_path: str) -> str:
    """
    Get file content from a specific commit.
    Returns file content as string.
    """
    try:
        repo = Repo(repo_path)
        commit = repo.commit(commit_hash)
        
        try:
            blob = commit.tree / file_path
            content = blob.data_stream.read()
            return content.decode('utf-8')
        except KeyError:
            raise HTTPException(status_code=404, detail=f"File {file_path} not found in commit")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Binary file cannot be decoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git error: {str(e)}")

def file_exists_in_commit(repo_path: str, commit_hash: str, file_path: str) -> bool:
    """
    Check if a file exists in a specific commit.
    """
    try:
        repo = Repo(repo_path)
        commit = repo.commit(commit_hash)
        try:
            _ = commit.tree / file_path
            return True
        except KeyError:
            return False
    except:
        return False


def sync_with_remote(repo_path: str) -> Dict[str, Any]:
    """
    Sync local repository with remote by performing a git pull.
    
    This fetches and merges the latest changes from the remote tracking branch.
    
    Returns:
        Dict with sync status information including:
        - success: bool
        - previous_commit: str
        - current_commit: str
        - commits_pulled: int
        - message: str
    """
    if not os.path.exists(repo_path):
        raise HTTPException(status_code=404, detail=f"Repository not found at {repo_path}")
    
    try:
        repo = Repo(repo_path)
        
        # Get current HEAD before sync
        previous_commit = repo.head.commit.hexsha
        
        # Perform git pull
        origin = repo.remotes.origin
        
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'
        # Trust On First Use (TOFU) for SSH
        env['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=accept-new'
        
        pull_info = origin.pull(env=env)
        
        # Get new HEAD after sync
        current_commit = repo.head.commit.hexsha
        
        # Count how many commits were pulled
        commits_pulled = 0
        if previous_commit != current_commit:
            try:
                commits_pulled = len(list(repo.iter_commits(f'{previous_commit}..{current_commit}')))
            except Exception:
                commits_pulled = 1  # At least one if heads differ
        
        return {
            "success": True,
            "previous_commit": previous_commit[:7],
            "current_commit": current_commit[:7],
            "commits_pulled": commits_pulled,
            "message": f"Successfully pulled {commits_pulled} commit(s) from remote."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
