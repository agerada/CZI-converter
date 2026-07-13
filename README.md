# CZI Converter

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue.svg)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/your_username/CZI_Converter/CI)

This is a fork of [farbodkhoraminia/CZI-converter](https://github.com/farbodkhoraminia/CZI-converter).

## Fork-Specific Features

This fork adds cross-platform and workflow controls focused on macOS and large-output handling.

- macOS-compatible conversion backend using `openslide-python` with automatic fallback to `czifile`.
- Two output modes controlled by `INDIVIDUAL_TILES`:
	- `true`: save a folder of smaller tile TIFFs plus a `manifest.txt`.
	- `false`: save one large TIFF per input slide.
- Reprocessing control via `FORCE_RUN`:
	- `false`: skip files recorded in `PROCESSED_FILES_RECORD`.
	- `true`: always process files, even if already recorded.
- Single-pass or watch-loop execution via `RUN_ONCE`.
- Per-file progress indicator in console/logs: `Processing file X/Y: <name>.czi`.

Additional dev features that have been added are:

- `uv` for dependency management and running the converter.
- simple testing suite that downloads a sample slide and verifies conversion to TIFF.

## Quick Start

1. Sync dependencies:

```bash
uv sync
```

2. Configure behavior in `config.yaml`.

3. Run:

```bash
uv run main.py
```

## Configuration Reference

The following keys are supported in `config.yaml`:

- `INPUT_FOLDER`: Folder scanned for `.czi` files.
- `OUTPUT_FOLDER`: Destination for output TIFFs or tile folders.
- `PROCESSED_FILES_RECORD`: File that stores processed input paths.
- `LOG_FILE`: Log file path.
- `CHECK_INTERVAL_SECONDS`: Poll interval when `RUN_ONCE` is `false`.
- `RUN_ONCE`: If `true`, process one scan and exit.
- `FORCE_RUN`: If `true`, do not skip previously processed files.
- `INDIVIDUAL_TILES`: Output mode toggle (`true` tiles, `false` single TIFF).
- `OUTPUT_TILE_SIZE`: Tile edge size (pixels) when `INDIVIDUAL_TILES=true`.
- `OUTPUT_TILE_FORMAT`: Tile extension/format (for example `tif`).

## Output Behavior

When `INDIVIDUAL_TILES=true`, each slide is written as:

- `OUTPUT_FOLDER/<slide_name>/tile_yXXXXXX_xXXXXXX.<format>`
- `OUTPUT_FOLDER/<slide_name>/manifest.txt`

When `INDIVIDUAL_TILES=false`, each slide is written as:

- `OUTPUT_FOLDER/<slide_name>.tif`

## Development

To run tests:

```bash
uv run pytest
```
