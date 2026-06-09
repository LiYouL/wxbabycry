# backend/scripts/download_data.py
"""Download donateacry-corpus dataset from public source."""
import os
import urllib.request
import zipfile
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cry_dataset")
DONATEACRY_URL = "https://raw.githubusercontent.com/gveres/donateacry-corpus/master/donateacry_corpus.zip"

def download():
    os.makedirs(DATA_DIR, exist_ok=True)
    zip_path = os.path.join(DATA_DIR, "donateacry.zip")

    print(f"Downloading donateacry-corpus from {DONATEACRY_URL}...")
    try:
        urllib.request.urlretrieve(DONATEACRY_URL, zip_path)
    except Exception:
        print("GitHub download failed. Trying alternative...")
        print("Please manually download from:")
        print("  https://github.com/gveres/donateacry-corpus")
        print(f"  and extract to {DATA_DIR}")
        print("Expected: data/cry_dataset/donateacry_corpus/<label_folders>/<audio_files>")
        sys.exit(1)

    print("Extracting...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(DATA_DIR)

    os.remove(zip_path)
    print(f"Dataset extracted to {DATA_DIR}")

if __name__ == "__main__":
    download()
