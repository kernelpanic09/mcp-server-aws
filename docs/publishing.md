# Publishing to PyPI

## How to bump the version

Version lives in `pyproject.toml` under `[project]`:

```toml
version = "1.0.0"
```

Change it there. That's the only place - hatchling reads it directly from `pyproject.toml`, so there's no `__version__` in source to keep in sync.

Follow [semver](https://semver.org/):

- Patch bump (`1.0.0` → `1.0.1`): bug fixes, no API changes
- Minor bump (`1.0.0` → `1.1.0`): new tools or resources, backward compatible
- Major bump (`1.0.0` → `2.0.0`): breaking changes to existing tool signatures or behavior

## How to tag and push

After committing the version bump:

```bash
git tag v1.0.1
git push origin v1.0.1
```

That tag push triggers the publish workflow.

## What the publish workflow does

The workflow (`.github/workflows/publish.yml`) runs on any tag matching `v*`:

1. Checks out the repo
2. Sets up Python and `uv`
3. Runs `uv build` to produce a `.whl` and `.tar.gz` in `dist/`
4. Uses `pypa/gh-action-pypi-publish` with OIDC Trusted Publishing to upload to PyPI - no API token needed

The workflow runs in the `pypi` GitHub environment, which you can protect with required reviewers if you want a manual gate before publishing.

## Setting up Trusted Publishing on PyPI

Trusted Publishing lets GitHub Actions publish to PyPI without storing an API token anywhere. PyPI verifies the OIDC token that GitHub issues for the workflow run.

1. Go to https://pypi.org/manage/account/publishing/ (you need a PyPI account with the `mcp-server-aws` project claimed, or create it on the first publish via `twine upload` with an API token)
2. Under "Add a new pending publisher", fill in:
   - **PyPI Project Name**: `mcp-server-aws`
   - **Owner**: `kernelpanic09`
   - **Repository name**: `mcp-server-aws`
   - **Workflow filename**: `publish.yml`
   - **Environment name**: `pypi`
3. Save. From then on, the workflow can publish without any stored secrets.

For the very first publish (before the project exists on PyPI), you have two options:

- Use Trusted Publishing with a "pending publisher" - PyPI supports this, the project gets created on first push
- Or do one manual upload with `twine` using an API token, then switch to Trusted Publishing for all future releases

The pending publisher approach is cleaner. Set it up before pushing the first tag.
