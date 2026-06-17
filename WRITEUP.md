# WRITEUP.md

## What I Did

I forked the [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) — a full-stack project with FastAPI, React/TypeScript, PostgreSQL, and Docker. It already had tests for the happy path so I read through the existing test files and source code to find what was genuinely missing.

### Part 1 — Tests

I added  new tests across 4 files under `backend/tests/api/routes/`:

- unauthenticated access on every item endpoint (401), input validation (empty title, missing title, title too long), pagination edge cases, and normal user item ownership flows which were completely untested in the original repo
-  missing required fields (422), and a documented bug where the private user creation route has no duplicate email guard so the DB throws an unhandled IntegrityError instead of a clean 400
- inactive user blocked at login, malformed/missing JWT tokens on protected endpoints, reset password edge cases
-  health check endpoint  test-email auth guards

The focus was failure cases and permission boundaries, not coverage numbers.

### Part 2 — CI/CD

I added `.github/workflows/ci.yml` which runs on every push and pull request with three jobs:

- **Backend** — runs ruff lint, spins up the DB container, runs migrations, runs the full pytest suite. Fails loudly if anything breaks.
- **Frontend** — runs Biome lint and TypeScript type-check. Fails if lint finds issues.
- **Docker build** — only runs after both jobs pass (`needs: [backend, frontend]`). Builds the backend image without pushing it.

One honest note: this project uses Playwright for all frontend tests which requires the full stack running via Docker Compose. I ran Biome lint and TypeScript type-check in CI instead and noted this gap rather than pretending Playwright runs without the full stack.




---

## How to Run Tests Locally

```bash


# Run only the new tests
 run pytest tests/api/routes/test_items_extended.py \
               tests/api/routes/test_private_extended.py \
               tests/api/routes/test_login_extended.py \
               tests/api/routes/test_utils_routes.py -v
```


```

---

## What I Would Do With More Time

- Add Vitest for frontend unit tests since Playwright is overkill for component-level testing
- Set up a real ECS deployment to verify the task definition works end to end
- Add dependency caching to CI to speed up runs


## What I Deliberately Skipped

- Build matrix across Python versions — understand the concept but didn't want to add complexity I couldn't fully explain
- Pushing the Docker image to ECR — no personal AWS account available
- Full Playwright e2e tests in CI — requires the full stack and significantly more setup time

---

## AI Tools Used

I used Claude  throughout the process to understand some concepts, check whether I had missed anything, and help write the write-up.

How I checked the output: I read every test before adding it to the repository, understood what each assertion was checking, ran all tests locally inside Docker, and verified that they passed. I then fixed two tests that had incorrect status code assumptions.

I did not submit anything that I could not explain or defend.
