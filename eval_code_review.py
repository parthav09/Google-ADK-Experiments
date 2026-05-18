import asyncio
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from code_review_pipeline.agent import root_agent


APP_NAME = "code_review_eval_app"
USER_ID = "eval_user"


load_dotenv(".env")


EVAL_CASES = [
    {
        "name": "sql_injection",
        "code": """
def get_user(username, db):
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return db.execute(query)
""",
        "expected_keywords": ["sql", "injection"],
    },
    {
        "name": "hardcoded_secret",
        "code": """
API_KEY = "sk-123456789-secret"

def call_service():
    return API_KEY
""",
        "expected_keywords": ["hardcoded", "secret"],
    },
    {
        "name": "division_by_zero",
        "code": """
def average(numbers):
    return sum(numbers) / len(numbers)
""",
        "expected_keywords": ["zero", "empty"],
    },
]


async def run_case(case):
    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
    )

    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
    )

    message = f"""
Please review the following Python code.

CODE START

{case["code"]}

CODE END
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

    async for _ in events:
        pass

    updated_session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session.id,
    )

    final_review = updated_session.state.get("final_review", "")
    review_text = final_review.lower()

    passed = all(
        keyword.lower() in review_text
        for keyword in case["expected_keywords"]
    )

    return {
        "name": case["name"],
        "passed": passed,
        "expected_keywords": case["expected_keywords"],
        "final_review": final_review,
    }


async def main():
    results = []

    for case in EVAL_CASES:
        print(f"Running eval: {case['name']}")
        result = await run_case(case)
        results.append(result)

    print("\nEvaluation Results")
    print("=" * 80)

    passed_count = 0

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"

        if result["passed"]:
            passed_count += 1

        print(f"{status}: {result['name']}")
        print(f"Expected keywords: {result['expected_keywords']}")
        print()

    print("=" * 80)
    print(f"Passed {passed_count}/{len(results)} evals")


if __name__ == "__main__":
    asyncio.run(main())