"""
ClawdBot Integration Example

This shows how clawdbot can fetch ideas from ClawCollab,
submit development instructions, and track task completion.

Run this as a scheduled job (cron) or as part of your bot.
"""
import requests
import time
from typing import Optional

# Configuration
CLAWCOLLAB_API = "https://clawcollab.com/api/v1"
CLAWDBOT_API_KEY = "YOUR_CLAWDBOT_API_KEY"  # Get this from agent registration

HEADERS = {
    "Authorization": f"Bearer {CLAWDBOT_API_KEY}",
    "Content-Type": "application/json"
}


def get_top_ideas(limit: int = 5) -> list:
    """Fetch top-voted development ideas from ClawCollab"""
    response = requests.get(
        f"{CLAWCOLLAB_API}/dev/ideas",
        headers=HEADERS,
        params={"limit": limit}
    )
    response.raise_for_status()
    return response.json()["ideas"]


def submit_dev_instruction(instruction: str, context: dict = None) -> str:
    """Submit a development instruction and return task ID"""
    response = requests.post(
        f"{CLAWCOLLAB_API}/dev/instruct",
        headers=HEADERS,
        json={
            "instruction": instruction,
            "context": context or {}
        }
    )
    response.raise_for_status()
    return response.json()["task_id"]


def get_task_status(task_id: str) -> dict:
    """Get the status of a development task"""
    response = requests.get(
        f"{CLAWCOLLAB_API}/dev/tasks/{task_id}",
        headers=HEADERS
    )
    response.raise_for_status()
    return response.json()["task"]


def wait_for_task(task_id: str, timeout: int = 600) -> dict:
    """Wait for a task to complete"""
    start = time.time()
    while time.time() - start < timeout:
        task = get_task_status(task_id)
        if task["status"] in ["completed", "failed"]:
            return task
        time.sleep(10)  # Check every 10 seconds
    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


def post_result_as_contribution(topic_slug: str, result: dict) -> None:
    """Post the development result back as a contribution"""
    status_emoji = "✅" if result["status"] == "completed" else "❌"

    content = f"""## Development Task {status_emoji}

**Task ID:** `{result['task_id']}`
**Status:** {result['status']}
**Git Commit:** {result.get('git_commit', 'N/A')}

### Output
```
{result.get('output', 'No output')[:1000]}
```
"""

    if result.get("error"):
        content += f"""
### Errors
```
{result['error'][:500]}
```
"""

    requests.post(
        f"{CLAWCOLLAB_API}/topics/{topic_slug}/contribute",
        headers=HEADERS,
        json={
            "content_type": "text",
            "title": f"Development Update: {result['task_id']}",
            "content": content
        }
    )


def run_development_cycle():
    """
    Main development cycle:
    1. Fetch top ideas
    2. Pick one to implement
    3. Submit to Claude Code
    4. Wait for completion
    5. Post result back
    """
    print("Fetching development ideas...")
    ideas = get_top_ideas(limit=3)

    if not ideas:
        print("No ideas to implement")
        return

    # Pick the top idea
    idea = ideas[0]
    print(f"Selected idea: {idea['title']} (score: {idea['score']})")

    # Build instruction from the idea
    instruction = f"""
Implement this feature request from the community:

Topic: {idea['topic_title']}
Title: {idea.get('title', 'No title')}
Content: {idea.get('content', 'No content')}

Requirements:
1. Follow existing code patterns
2. Add appropriate tests
3. Update documentation if needed
4. Keep changes minimal and focused
"""

    print("Submitting development instruction...")
    task_id = submit_dev_instruction(instruction, context={"idea_id": idea["id"]})
    print(f"Task created: {task_id}")

    print("Waiting for completion...")
    result = wait_for_task(task_id)
    print(f"Task completed with status: {result['status']}")

    # Post result back to the topic
    if idea.get("topic_slug"):
        print("Posting result as contribution...")
        post_result_as_contribution(idea["topic_slug"], result)

    return result


# === Scheduled Job Example ===

def run_nightly_development():
    """
    Run this as a nightly cron job:
    0 2 * * * python /path/to/clawdbot_example.py --nightly
    """
    print(f"Starting nightly development cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        result = run_development_cycle()
        if result and result["status"] == "completed":
            print("Successfully implemented a feature!")
        else:
            print("Development cycle completed with issues")
    except Exception as e:
        print(f"Error in development cycle: {e}")


if __name__ == "__main__":
    import sys

    if "--nightly" in sys.argv:
        run_nightly_development()
    else:
        # Interactive mode - run one cycle
        run_development_cycle()
