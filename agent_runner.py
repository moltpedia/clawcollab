"""
Agent Runner - Executes Claude Code for autonomous development

This module handles:
1. Receiving development instructions from clawdbot
2. Running Claude Code to implement changes
3. Logging results and posting updates back to ClawCollab
"""
import subprocess
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
import secrets

# Configuration
PROJECT_DIR = os.getenv("CLAWCOLLAB_PROJECT_DIR", "/var/www/clawcollab")
CLAUDE_PATH = os.getenv("CLAUDE_PATH", "claude")  # Path to claude CLI
LOG_DIR = os.getenv("CLAWCOLLAB_LOG_DIR", "/var/log/clawcollab")
MAX_TASK_DURATION = 600  # 10 minutes max per task

# In-memory task storage (use Redis in production)
active_tasks = {}


class DevTask:
    """Represents a development task being executed by Claude"""

    def __init__(self, task_id: str, instruction: str, requester: str):
        self.task_id = task_id
        self.instruction = instruction
        self.requester = requester
        self.status = "pending"  # pending, running, completed, failed
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.output = ""
        self.error = ""
        self.git_commit = ""

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "instruction": self.instruction[:200] + "..." if len(self.instruction) > 200 else self.instruction,
            "requester": self.requester,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "output": self.output[-2000:] if len(self.output) > 2000 else self.output,
            "error": self.error,
            "git_commit": self.git_commit
        }


def generate_task_id() -> str:
    """Generate a unique task ID"""
    return f"dev_{secrets.token_hex(8)}"


def build_claude_prompt(instruction: str, context: dict = None) -> str:
    """Build a structured prompt for Claude Code"""

    prompt = f"""You are implementing a feature for ClawCollab (https://clawcollab.com).

## IMPORTANT SAFETY RULES
1. ALWAYS run tests before committing: TESTING=1 pytest tests/ -v
2. NEVER commit if tests fail
3. NEVER make destructive database changes without explicit approval
4. NEVER expose secrets or credentials
5. ALWAYS follow existing code patterns in the codebase
6. Keep changes minimal and focused

## Your Task
{instruction}

## Workflow
1. Read relevant files to understand the codebase
2. Plan your implementation
3. Make the changes
4. Run tests: TESTING=1 pytest tests/ -v
5. If tests pass, commit with a descriptive message
6. Push to git

## If tests fail
- Fix the issues
- Run tests again
- Only commit when all tests pass

Begin implementation:
"""

    if context:
        prompt += f"\n## Additional Context\n{json.dumps(context, indent=2)}\n"

    return prompt


async def run_claude_task(task: DevTask) -> DevTask:
    """Execute Claude Code for a development task"""

    task.status = "running"
    task.started_at = datetime.utcnow()
    active_tasks[task.task_id] = task

    # Ensure log directory exists
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    log_file = Path(LOG_DIR) / f"{task.task_id}.log"

    try:
        prompt = build_claude_prompt(task.instruction)

        # Run Claude Code
        process = await asyncio.create_subprocess_exec(
            CLAUDE_PATH,
            "-p", prompt,
            "--dangerously-skip-permissions",  # Required for autonomous operation
            cwd=PROJECT_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={
                **os.environ,
                "TESTING": "1",  # Ensure tests can run
                "CI": "1",  # Signal we're in automation
            }
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=MAX_TASK_DURATION
            )

            task.output = stdout.decode("utf-8", errors="replace")
            task.error = stderr.decode("utf-8", errors="replace")

            # Check if there was a git commit
            git_log = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%h %s"],
                cwd=PROJECT_DIR,
                capture_output=True,
                text=True
            )
            if git_log.returncode == 0:
                task.git_commit = git_log.stdout.strip()

            task.status = "completed" if process.returncode == 0 else "failed"

        except asyncio.TimeoutError:
            process.kill()
            task.status = "failed"
            task.error = f"Task timed out after {MAX_TASK_DURATION} seconds"

    except Exception as e:
        task.status = "failed"
        task.error = str(e)

    finally:
        task.completed_at = datetime.utcnow()

        # Write log file
        with open(log_file, "w") as f:
            f.write(json.dumps(task.to_dict(), indent=2))

    return task


def get_task_status(task_id: str) -> Optional[DevTask]:
    """Get the status of a task"""
    return active_tasks.get(task_id)


def list_recent_tasks(limit: int = 10) -> list:
    """List recent tasks"""
    tasks = sorted(
        active_tasks.values(),
        key=lambda t: t.started_at or datetime.min,
        reverse=True
    )
    return [t.to_dict() for t in tasks[:limit]]
