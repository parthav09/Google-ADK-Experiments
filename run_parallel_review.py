import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from code_review_pipeline.parallel_agent import root_agent


APP_NAME = "parallel_code_review_app"
USER_ID = "local_user"

MAX_CHARS = 60000

ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".go",
    ".rs",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".adk",
}


load_dotenv(".env")


def should_skip(path):
    parts = set(path.parts)

    if parts & SKIP_DIRS:
        return True

    if path.name.startswith("."):
        return True

    return False


def read_code_file(file_path):
    return file_path.read_text(encoding="utf-8", errors="ignore")

def read_codebase(path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if path.is_file():
        files = [path]
    else:
        files = []

        for file_path in path.rglob("*"):
            if file_path.is_file() and not should_skip(file_path):
                if file_path.suffix in ALLOWED_EXTENSIONS:
                    files.append(file_path)

    code_parts = []
    total_chars = 0

    for file_path in files:
        file_text = read_code_file(file_path)

        block = f"""
FILE: {file_path}

{file_text}
"""

        if total_chars + len(block) > MAX_CHARS:
            break

        code_parts.append(block)
        total_chars += len(block)

    return "\n\n" + "=" * 80 + "\n\n".join(code_parts)

async def run_pipeline(codebase_text):
    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state={
            "user:project": "ADK ParallelAgent code review pipeline",
        },
    )

    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
    )

    message = f"""
Please review the following codebase.

Each file is marked with FILE: path.

CODEBASE START

{codebase_text}

CODEBASE END
"""

    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    events = runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=content,
    )

    print("\nRunning parallel code review pipeline...\n")

    async for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(part.text for part in event.content.parts if part.text)

            if text.strip():
                print("=" * 80)
                print(f"Stage: {event.author}")
                print("=" * 80)
                print(text)
                print()

    updated_session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session.id,
    )

    print("=" * 80)
    print("Session state keys")
    print("=" * 80)

    for key in updated_session.state.keys():
        print(f"- {key}")


async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run_parallel_review.py path/to/file.py")
        print("  python run_parallel_review.py path/to/codebase")
        return

    path = sys.argv[1]
    codebase_text = read_codebase(path)

    if not codebase_text.strip():
        print("No readable code files found.")
        return

    await run_pipeline(codebase_text)


if __name__ == "__main__":
    asyncio.run(main())