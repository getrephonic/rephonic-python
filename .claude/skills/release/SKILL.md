---
description: Cut a new release of the `rephonic` Python package locally — bump version, commit, tag, build, upload to PyPI, push. Use when the user asks to "release", "cut a release", "publish a new version", or "bump version". Accepts an optional semver bump argument (patch / minor / major / explicit version).
user-invocable: true
disable-model-invocation: true
---

# /release

Cut a new release from the local machine. Releases are rare here, so this skill doubles as a how-did-I-do-this-last-time memo.

## Arguments

- `/release` — prompt for the bump type (default: `patch`).
- `/release patch|minor|major` — semver bump.
- `/release 1.2.3` — explicit version.

## Pre-flight

Stop and ask the user if any of these fail:

1. `git status --porcelain` is empty.
2. On `main`, up to date with `origin/main` (`git fetch` first).
3. `uv run pytest --no-cov -q` is green.
4. PyPI credentials exist — check for `~/.pypirc` or `TWINE_PASSWORD` env var. If missing, stop and tell the user to create a [PyPI API token](https://pypi.org/manage/account/token/) and put it in `~/.pypirc`:
   ```
   [pypi]
   username = __token__
   password = pypi-AgE...
   ```

## Run

```bash
# 1. Bump version (edit src/rephonic/_version.py)
# 2. Commit + tag locally
git add src/rephonic/_version.py
git commit -m "Release v<NEW>"
git tag -a "v<NEW>" -m "Release v<NEW>"

# 3. Build
rm -rf dist/ build/
uv build
uv run twine check dist/*

# 4. Upload to PyPI
uv run twine upload dist/*

# 5. Push (only after upload succeeds)
git push origin main
git push origin "v<NEW>"

# 6. GitHub release
gh release create "v<NEW>" --title "v<NEW>" --generate-notes
```

## If upload fails partway

PyPI rejects re-uploads of a version. Unwind locally and bump patch:

```bash
git tag -d "v<NEW>"
git reset --hard HEAD^
# then bump to the next patch and retry
```

## Verify

```bash
curl -s https://pypi.org/pypi/rephonic/json \
  | python3 -c "import json,sys; print(sorted(json.load(sys.stdin)['releases'])[-3:])"
```

Report `https://pypi.org/project/rephonic/<NEW>/` and the GitHub release URL.

## Never

- Force-push to `main`.
- Delete or move a published tag — PyPI versions are immutable.
- Re-upload the same version.
