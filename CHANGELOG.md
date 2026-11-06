# Changelog

All notable changes to this project are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- OpenEnv environment for tabular data cleaning with four tasks: `fix_types`, `handle_missing`, `full_pipeline`, `outlier_cleanup`.
- Seven actions: `replace_value`, `convert_type`, `fill_missing`, `remove_duplicates`, `drop_rows`, `standardize`, `parse_date`.
- Graders that score the fraction of checks passing, with the per-step reward as the change in score.
- `inference.py` LLM baseline with the hackathon's `[START]`/`[STEP]`/`[END]` log format. It can start the env from a Docker image or connect to a running server by URL.
- Tests for all four graders, the client payload and the log format.
- Dockerfile, `openenv.yaml` and `uv.lock` for `openenv validate`.
- `examples/scripted_policy.py`, a fixed action plan that solves all four tasks with no model or API key.
- CI: lint, tests, and a scripted episode against the Docker image.
- MIT license, CONTRIBUTING.md, issue and PR templates, `.env.example`.

### Changed
- Grader scores are clamped to 0.01..0.99 because the evaluator wants scores strictly between 0 and 1.
- Server port moved to 8000 to match OpenEnv's LocalDockerProvider.
- Client step payload built with `model_dump(exclude_none=True)`.
- README rewritten with a demo GIF and examples checked against a real run.

### Fixed
- Missing `await` on async client calls in `inference.py`.
- `server/app.py` can be run as a direct script for `openenv validate`.
- Docker build failures: pinned dependency versions and added `requests`.
