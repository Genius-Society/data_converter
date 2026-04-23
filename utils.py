import os
import shutil

EN_US = os.getenv("LANG") != "zh_CN.UTF-8"
TMP_DIR = "./__pycache__"


def clean_dir(dir_path: str):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

    os.makedirs(dir_path)
