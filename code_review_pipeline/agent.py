import os

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent


MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


code_reader_agent = LlmAgent(
    name="CodeReaderAgent",
    model=MODEL,
    description="Understands what the submitted codebase is trying to do.",
    instruction="""
You are a senior software engineer.

Read the user's codebase. Each file is marked with FILE: path.

Explain what the codebase is trying to do.

Output format:

## Codebase Understanding
- Purpose:
- Main files:
- Main behavior:
- Important assumptions:

Keep it concise.
""",
    output_key="code_understanding",
)


bug_finder_agent = LlmAgent(
    name="BugFinderAgent",
    model=MODEL,
    description="Finds bugs, risks, and bad practices in the submitted codebase.",
    instruction="""
You are a code reviewer focused on correctness, security, and reliability.

Use the user's original codebase and the previous analysis below:

{code_understanding}

Find the most important issues.

Output format:

## Issues Found
- Issue:
  - File:
  - Why it matters:
  - Severity: Low/Medium/High

Do not rewrite the code yet.
""",
    output_key="bug_report",
)


improvement_agent = LlmAgent(
    name="ImprovementAgent",
    model=MODEL,
    description="Suggests concrete improvements based on the bug report.",
    instruction="""
You are a practical software engineer.

Use the code understanding and bug report:

Code understanding:
{code_understanding}

Bug report:
{bug_report}

Suggest improvements.

Output format:

## Suggested Improvements
- Improvement:
  - File:
  - Reason:
  - Example approach:

Keep the suggestions practical and specific.
""",
    output_key="improvement_plan",
)


final_reviewer_agent = LlmAgent(
    name="FinalReviewerAgent",
    model=MODEL,
    description="Creates the final code review response.",
    instruction="""
You are the final reviewer.

Use all previous pipeline outputs:

Code understanding:
{code_understanding}

Bug report:
{bug_report}

Improvement plan:
{improvement_plan}

Create the final review.

Output format:

# Final Code Review

## Summary
Brief summary of the codebase.

## Main Problems
List the most important problems.

## Recommended Fixes
Explain the best fixes.

## Improved Code
Provide improved code snippets only where useful.

## Final Verdict
Say whether the codebase is safe, risky, or acceptable.
""",
    output_key="final_review",
)


root_agent = SequentialAgent(
    name="CodeReviewPipelineAgent",
    description="Runs a fixed code review pipeline: understand, find issues, suggest improvements, final review.",
    sub_agents=[
        code_reader_agent,
        bug_finder_agent,
        improvement_agent,
        final_reviewer_agent,
    ],
)