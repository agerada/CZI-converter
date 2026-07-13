from pathlib import Path
import shutil
import sys
import urllib.request

import tifffile
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from converter.config import Config
from converter.converter import SlideConverter

CZI_URL = "https://zenodo.org/records/8305531/files/Image_1_2023_08_18__14_32_31_964(1).czi?download=1"


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as response, destination.open("wb") as out_file:
        shutil.copyfileobj(response, out_file)


def test_download_and_convert_creates_tiff(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    logs_dir = tmp_path / "logs"
    processed_record = tmp_path / "processed_files.txt"
    config_path = tmp_path / "config.yaml"

    czi_path = input_dir / "sample.czi"
    _download_file(CZI_URL, czi_path)

    config_data = {
        "INPUT_FOLDER": str(input_dir),
        "OUTPUT_FOLDER": str(output_dir),
        "PROCESSED_FILES_RECORD": str(processed_record),
        "LOG_FILE": str(logs_dir / "conversion_test.log"),
        "CHECK_INTERVAL_SECONDS": 1,
        "RUN_ONCE": True,
        "FORCE_RUN": True,
        "INDIVIDUAL_TILES": False,
        "OUTPUT_TILE_SIZE": 2048,
        "OUTPUT_TILE_FORMAT": "tif",
    }
    with config_path.open("w", encoding="utf-8") as cfg:
        yaml.safe_dump(config_data, cfg, sort_keys=False)

    converter = SlideConverter(Config(config_path))
    converter.run()

    output_tiff = output_dir / f"{czi_path.stem}.tif"
    assert output_tiff.is_file(), f"Expected output TIFF was not created: {output_tiff}"
    assert output_tiff.stat().st_size > 0, "Output TIFF was created but is empty"

    image_data = tifffile.imread(str(output_tiff))
    assert image_data.size > 0, "Output TIFF could not be read as image data"
