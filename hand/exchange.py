from pydantic import BaseModel


class GitHubRepoCommit(BaseModel):
    name: str  # name of the repository
    commit_hash: str  # 7 characters hash value


class GitHubCommitInfo(BaseModel):
    commit_hash: str  # 7 characters hash value
    pushed_time: str
    msg: str
    repo: str
