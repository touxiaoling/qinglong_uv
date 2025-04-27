import uvicorn
import os
from pathlib import Path
import shutil
import jurigged
import logging

if __name__ == "__main__":
    jurigged.watch("qinglong/*.py")
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(
        app="qinglong.main:app", host="0.0.0.0", port=8090, loop="uvloop", http="httptools",log_level="debug"
    )  # ,reload=True, reload_dirs=["phoneScanWeb"])
