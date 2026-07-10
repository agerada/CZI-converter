# converter/converter.py
import time
import logging
import numpy as np
import tifffile
from openslide import OpenSlide, OpenSlideError
import czifile

class SlideConverter:
    def __init__(self, config):
        self.config = config
        self.setup_logging()
        self.ensure_directories()

    def setup_logging(self):
        logging.basicConfig(
            filename=self.config.LOG_FILE,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info("Logging initialized.")

    def ensure_directories(self):
        """
        Ensures that the output directory exists.
        """
        self.config.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        self.config.INPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        self.config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        logging.info("Verified input and output directories.")

    def _normalize_image_array(self, arr):
        """Normalize CZI arrays to a 2D or RGB image."""
        arr = np.squeeze(arr)

        while arr.ndim > 3:
            arr = arr[0]

        if arr.ndim == 3:
            if arr.shape[-1] in (3, 4):
                arr = arr[..., :3]
            elif arr.shape[0] in (3, 4):
                arr = np.moveaxis(arr[:3], 0, -1)
            else:
                arr = arr[0]

        if arr.ndim not in (2, 3):
            raise ValueError(f"Unsupported CZI image shape after normalization: {arr.shape}")

        if arr.dtype != np.uint8:
            # Rescale to uint8 for broad TIFF compatibility.
            arr = arr.astype(np.float32)
            min_v = float(arr.min())
            max_v = float(arr.max())
            if max_v > min_v:
                arr = (arr - min_v) / (max_v - min_v)
            arr = (arr * 255.0).clip(0, 255).astype(np.uint8)

        return arr

    def _convert_with_openslide(self, inp, out):
        with OpenSlide(str(inp)) as slide:
            width, height = slide.dimensions
            if not self.config.INDIVIDUAL_TILES:
                image = slide.read_region((0, 0), 0, (width, height)).convert("RGB")
                tifffile.imwrite(str(out), np.asarray(image), photometric='rgb', compression='zlib')
                return

            tile_size = self.config.OUTPUT_TILE_SIZE
            out.mkdir(parents=True, exist_ok=True)
            tile_count = 0
            for y in range(0, height, tile_size):
                for x in range(0, width, tile_size):
                    w = min(tile_size, width - x)
                    h = min(tile_size, height - y)
                    tile = slide.read_region((x, y), 0, (w, h)).convert("RGB")
                    tile_array = np.asarray(tile)
                    tile_path = out / f"tile_y{y:06d}_x{x:06d}.{self.config.OUTPUT_TILE_FORMAT}"
                    tifffile.imwrite(str(tile_path), tile_array, photometric='rgb', compression='zlib')
                    tile_count += 1
                    if tile_count % 100 == 0:
                        logging.info(f"Wrote {tile_count} tiles for {inp}")

            manifest_path = out / "manifest.txt"
            with open(manifest_path, 'w') as f:
                f.write(f"source={inp}\n")
                f.write(f"width={width}\n")
                f.write(f"height={height}\n")
                f.write(f"tile_size={tile_size}\n")
                f.write(f"tile_count={tile_count}\n")

    def _convert_with_czifile(self, inp, out):
        with czifile.CziFile(str(inp)) as czi:
            arr = czi.asarray()
        normalized = self._normalize_image_array(arr)

        if not self.config.INDIVIDUAL_TILES:
            if normalized.ndim == 3:
                tifffile.imwrite(str(out), normalized, photometric='rgb', compression='zlib')
            else:
                tifffile.imwrite(str(out), normalized, photometric='minisblack', compression='zlib')
            return

        height, width = normalized.shape[:2]
        tile_size = self.config.OUTPUT_TILE_SIZE
        out.mkdir(parents=True, exist_ok=True)
        tile_count = 0
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                tile = normalized[y:y + tile_size, x:x + tile_size]
                tile_path = out / f"tile_y{y:06d}_x{x:06d}.{self.config.OUTPUT_TILE_FORMAT}"
                if tile.ndim == 3:
                    tifffile.imwrite(str(tile_path), tile, photometric='rgb', compression='zlib')
                else:
                    tifffile.imwrite(str(tile_path), tile, photometric='minisblack', compression='zlib')
                tile_count += 1
                if tile_count % 100 == 0:
                    logging.info(f"Wrote {tile_count} tiles for {inp}")

        manifest_path = out / "manifest.txt"
        with open(manifest_path, 'w') as f:
            f.write(f"source={inp}\n")
            f.write(f"width={width}\n")
            f.write(f"height={height}\n")
            f.write(f"tile_size={tile_size}\n")
            f.write(f"tile_count={tile_count}\n")

    def convert_slide(self, inp, out):
        try:
            try:
                self._convert_with_openslide(inp, out)
                logging.info(f"Converted {inp} to {out} using OpenSlide")
            except (OpenSlideError, OSError, RuntimeError) as openslide_error:
                logging.warning(
                    f"OpenSlide could not read {inp}; falling back to czifile. Error: {openslide_error}"
                )
                self._convert_with_czifile(inp, out)
            logging.info(f"Successfully converted {inp} to {out}")

        except Exception as e:
            logging.error(f"Failed to convert {inp}: {e}", exc_info=True)

    def load_processed_files(self):
        if not self.config.PROCESSED_FILES_RECORD.is_file():
            return set()
        with open(self.config.PROCESSED_FILES_RECORD, 'r') as f:
            return set(line.strip() for line in f)

    def save_processed_files(self, processed_files):
        with open(self.config.PROCESSED_FILES_RECORD, 'w') as f:
            for file in processed_files:
                f.write(f"{file}\n")

    def run(self):
        processed_files = self.load_processed_files()

        while True:
            try:
                czi_files = [f for f in self.config.INPUT_FOLDER.iterdir() if f.suffix.lower() == '.czi']
                for cf in czi_files:
                    cf_path = cf.resolve()
                    if (not self.config.FORCE_RUN) and (str(cf_path) in processed_files):
                        continue
                    if self.config.INDIVIDUAL_TILES:
                        out_path = self.config.OUTPUT_FOLDER / cf.stem
                    else:
                        out_path = self.config.OUTPUT_FOLDER / f"{cf.stem}.tif"
                    self.convert_slide(cf_path, out_path)
                    processed_files.add(str(cf_path))
                    self.save_processed_files(processed_files)
                if self.config.RUN_ONCE:
                    logging.info("RUN_ONCE enabled; exiting after single scan.")
                    break
                time.sleep(self.config.CHECK_INTERVAL_SECONDS)
            except KeyboardInterrupt:
                logging.info("Shutdown signal received. Exiting.")
                break
            except Exception as e:
                logging.error(f"Unexpected error: {e}", exc_info=True)
                time.sleep(self.config.CHECK_INTERVAL_SECONDS)
