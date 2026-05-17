from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent


MODEL = "gemini-2.5-flash"


security_reviewer_agent = LlmAgent(
    name="SecurityReviewerAgent",
    model=MODEL,
    description="Reviews the codebase for security risks.",
    instruction="""
You are a security-focused code reviewer.

Review the submitted codebase only for security issues.

Look for:
- injection risks
- unsafe file access
- hardcoded secrets
- insecure auth logic
- unsafe dependencies or patterns
- risky input handling

Output format:

## Security Review
- Issue:
  - File:
  - Risk:
  - Severity: Low/Medium/High
  - Suggested fix:

If there are no clear security issues, say so.
""",
    output_key="security_review",
)


performance_reviewer_agent = LlmAgent(
    name="PerformanceReviewerAgent",
    model=MODEL,
    description="Reviews the codebase for performance and scalability issues.",
    instruction="""
You are a performance-focused code reviewer.

Review the submitted codebase only for performance and scalability issues.

Look for:
- inefficient loops
- repeated expensive operations
- unnecessary file reads
- blocking operations
- memory-heavy behavior
- poor scaling patterns

Output format:

## Performance Review
- Issue:
  - File:
  - Why it matters:
  - Severity: Low/Medium/High
  - Suggested fix:

If there are no clear performance issues, say so.
""",
    output_key="performance_review",
)


maintainability_reviewer_agent = LlmAgent(
    name="MaintainabilityReviewerAgent",
    model=MODEL,
    description="Reviews the codebase for readability and maintainability issues.",
    instruction="""
You are a maintainability-focused code reviewer.

Review the submitted codebase only for readability, structure, and maintainability.

Look for:
- unclear naming
- duplicated logic
- overly large functions
- confusing structure
- weak separation of concerns
- hard-to-test code

Output format:

## Maintainability Review
- Issue:
  - File:
  - Why it matters:
  - Severity: Low/Medium/High
  - Suggested fix:

If there are no clear maintainability issues, say so.
""",
    output_key="maintainability_review",
)


parallel_review_agent = ParallelAgent(
    name="ParallelCodeReviewAgent",
    description="Runs security, performance, and maintainability reviewers in parallel.",
    sub_agents=[
        security_reviewer_agent,
        performance_reviewer_agent,
        maintainability_reviewer_agent,
    ],
)


final_aggregator_agent = LlmAgent(
    name="FinalAggregatorAgent",
    model=MODEL,
    description="Combines all parallel code review results into one final review.",
    instruction="""
You are the final code review aggregator.

Use only the three review results below:

Security review:
{security_review}

Performance review:
{performance_review}

Maintainability review:
{maintainability_review}

Create a combined final review.

Output format:

# Final Parallel Code Review

## Summary
Briefly summarize the overall state of the codebase.

## Security Findings
Summarize the security review.

## Performance Findings
Summarize the performance review.

## Maintainability Findings
Summarize the maintainability review.

## Top Priorities
List the top 3 fixes in order of importance.

## Final Verdict
Say whether the codebase looks safe, risky, or acceptable.
""",
    output_key="final_parallel_review",
)


root_agent = SequentialAgent(
    name="ParallelCodeReviewPipelineAgent",
    description="Runs parallel specialist reviews, then aggregates the results.",
    sub_agents=[
        parallel_review_agent,
        final_aggregator_agent,
    ],
)