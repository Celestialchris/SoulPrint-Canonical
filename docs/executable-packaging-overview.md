# SoulPrint executable packaging overview

This document defines the shortest sane path from the current working Flask repo to a downloadable Windows build.

## Current truth

SoulPrint already works as software:
- the Flask app runs locally
- imports and continuity flows exist
- tests pass when the environment is correct

The gap is packaging and first-run ergonomics.

## Packaging goal

A user should be able to:
1. download SoulPrint for Windows
2. open `SoulPrint.exe`
3. have the local app start automatically
4. have the browser open automatically
5. import one conversation export
6. generate a continuation and copy it into a new AI chat

## Release strategy for v0.1

Use the existing local web app as the product surface and package it with PyInstaller.

Why this route:
- no full desktop rewrite is required
- no Electron or Tauri complexity yet
- it forces a real entrypoint and asset-bundling story
- it is the fastest route to a clickable build

## Files added for packaging

- `pyproject.toml` — makes the repo installable with `pip install -e .`
- `tests/conftest.py` — keeps local test imports stable from repo root
- `src/runtime.py` — centralizes resource paths and writable app-data paths
- `src/main.py` — the user-facing launcher entrypoint
- `SoulPrint.spec` — PyInstaller build recipe
- `requirements-build.txt` — build-only dependencies
- `scripts/build_windows.bat` — one-go Windows build command

## One-go Windows build

From the repo root on Windows:

```bat
scripts\build_windows.bat
```

That script is intended to:
1. create a virtual environment if missing
2. install runtime and build dependencies
3. install SoulPrint in editable mode
4. run the test suite
5. package the app with PyInstaller
6. zip the final `dist\SoulPrint` folder

## Expected output

After a successful build:

```text
 dist/
 ├── SoulPrint/
 │   ├── SoulPrint.exe
 │   └── ... bundled runtime files ...
 └── SoulPrint-windows.zip
```

## Runtime behavior

The packaged app should:
- write its SQLite database to a user-writable app-data folder
- keep templates and static assets bundled inside the executable output
- open the browser automatically on launch
- default to `http://127.0.0.1:5678`

## Next polish layer after first build

After the first executable exists and runs:
1. add icon and metadata to the build
2. refine the first-run screen around `Import -> Continue`
3. add a friendly release README inside the zip
4. publish the build through GitHub Releases and the landing page
5. gather user feedback before choosing a heavier desktop wrapper strategy

## Decision boundary

Do not build subscriptions, cloud sync, or a native desktop shell before the first executable build works and real users have tried the import-to-continuation flow.
