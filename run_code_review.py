import asyncio
from dotenv import load_dotenv
from pathlib import Path
import sys
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from datetime import datetime

APP_NAME = "code_review_pipeline_app"
USER_ID = "local_user"
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


MAX_CHARS = 60000


ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
}

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
}

def should_skip(path):
    parts = set(path.parts)

    if parts & IGNORED_DIRS:
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

    files = []

    if path.is_file():
        files = [path]
    else:
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

def save_report(final_review, reviewed_path):
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"code_review_report_{timestamp}.md"

    report_content = f"""# Code Review Report

## Reviewed Path

{reviewed_path}

---

{final_review}
"""

    report_path.write_text(report_content, encoding="utf-8")

    return report_path


async def run_pipeline(codebase_text, reviewed_path):
    from code_review_pipeline.agent import root_agent

    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state={
            "user:project": "ADK SequentialAgent code review pipeline",
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

    print("\nRunning code review pipeline...\n")

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

    final_review = updated_session.state.get("final_review")

    if final_review:
        report_path = save_report(final_review, reviewed_path)
        print("=" * 80)
        print("Report saved")
        print("=" * 80)
        print(report_path)

    print("=" * 80)
    print("Session state keys")
    print("=" * 80)

    for key in updated_session.state.keys():
        print(f"- {key}")


async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run_code_review.py path/to/file.py")
        print("  python run_code_review.py path/to/codebase")
        return

    path = sys.argv[1]
    codebase_text = read_codebase(path)

    if not codebase_text.strip():
        print("No readable code files found.")
        return

    await run_pipeline(codebase_text, path)

if __name__ == "__main__":
    asyncio.run(main())

