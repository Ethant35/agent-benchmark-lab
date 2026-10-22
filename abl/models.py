"""Versioned configuration contracts; reject unknown or unsafe options."""
from pathlib import Path
from typing import Literal
import hashlib
import json
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Task(Strict):
    schema_version: Literal[1]
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]+$")
    version: str
    category: Literal['bug_fix', 'feature', 'navigation', 'refactor', 'extraction', 'multistep']
    description: str
    fixture: str = 'fixture'
    setup: list[str] = []
    allowed_tools: list[Literal['read_file', 'write_file', 'shell', 'finish']]
    network: Literal['none'] = 'none'
    runtime_seconds: float = Field(default=30, gt=0, le=3600)
    max_tool_steps: int = Field(default=20, ge=1, le=1000)
    token_budget: int | None = Field(default=None, gt=0)
    cost_budget_usd: float | None = Field(default=None, gt=0)
    verifier: list[str]
    expected_artifacts: list[str]
    cleanup: Literal['always'] = 'always'

    @model_validator(mode='after')
    def paths(self):
        for p in [self.fixture, *self.expected_artifacts]:
            if Path(p).is_absolute() or '..' in Path(p).parts:
                raise ValueError('Paths must be relative without traversal')
        if self.fixture != 'fixture':
            raise ValueError('v1 fixtures must be in fixture/')
        if self.verifier != ['python', '/verifier/check.py']:
            raise ValueError('v1 verifier must be python /verifier/check.py')
        return self

class Config(Strict):
    schema_version: Literal[1] = 1
    runner: Literal['reference', 'agent'] = 'reference'
    provider: Literal['none', 'openrouter', 'openai-compatible'] = 'none'
    model: str = 'deterministic-reference'
    endpoint: str = 'https://openrouter.ai/api/v1'
    api_key_env: str = 'OPENROUTER_API_KEY'
    supports_tools: bool = False
    streaming: bool = False
    stream_usage: bool = False
    temperature: float | None = Field(default=None, ge=0, le=2)
    reasoning_effort: str | None = None
    max_requests: int = Field(default=12, ge=1, le=100)
    max_output_tokens: int = Field(default=2048, ge=1, le=32768)
    max_tool_steps: int | None = Field(default=None, ge=1, le=1000)
    runtime_seconds: float | None = Field(default=None, gt=0, le=3600)
    token_budget: int | None = Field(default=None, gt=0)
    spend_limit_usd: float = Field(default=0.25, gt=0, le=100)
    # Conservative operator-supplied upper bounds, USD per million tokens.
    input_price_per_million: float | None = Field(default=None, ge=0)
    output_price_per_million: float | None = Field(default=None, ge=0)
    repeats: int = Field(default=1, ge=1, le=100)
    tasks: list[str] = []
    runtime: Literal['auto','docker','podman'] = 'auto'
    image: str = 'docker.io/library/python:3.12-slim'
    reference_mode: Literal['success','fail','timeout','tool_failure','isolation'] = 'success'

    @model_validator(mode='after')
    def consistency(self):
        if self.runner == 'agent' and self.provider == 'none':
            raise ValueError('agent runner requires a provider')
        if self.runner == 'reference' and self.provider != 'none':
            raise ValueError('reference runner cannot claim a model provider')
        if self.runner == 'reference' and self.model != 'deterministic-reference':
            raise ValueError('reference model must be deterministic-reference')
        from urllib.parse import urlparse
        u = urlparse(self.endpoint)
        if u.username or u.password or u.query or u.fragment:
            raise ValueError('Endpoint must not contain credentials, query, or fragment')
        if u.scheme != 'https' and not (u.scheme == 'http' and u.hostname in ('localhost','127.0.0.1','::1')):
            raise ValueError('Endpoint must use HTTPS except loopback endpoints')
        return self

    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.model_dump(), sort_keys=True).encode()).hexdigest()

def corpus_root():
    installed = Path(__file__).parent / 'corpus'
    return installed if installed.exists() else Path(__file__).parent.parent / 'corpus'

def load_tasks(root=None):
    root = root or corpus_root()
    result = {}
    for path in sorted(root.glob('*/task.yaml')):
        task = Task.model_validate(yaml.safe_load(path.read_text()))
        if task.id in result or task.id != path.parent.name:
            raise ValueError(f'Duplicate or mismatched task ID: {task.id}')
        for folder in ('fixture','verifier'):
            if not (path.parent/folder).is_dir():
                raise ValueError(f'Missing {folder}: {task.id}')
            if any(p.is_symlink() for p in (path.parent/folder).rglob('*')):
                raise ValueError('Corpus symlinks are forbidden')
        if not (path.parent/'verifier/check.py').is_file():
            raise ValueError('Missing verifier/check.py')
        result[task.id] = (task, path.parent)
    if not result:
        raise ValueError('No tasks found')
    return result

def tree_hash(path):
    h = hashlib.sha256()
    for p in sorted(path.rglob('*')):
        if p.is_file():
            h.update(str(p.relative_to(path)).encode()); h.update(p.read_bytes())
    return h.hexdigest()
