import logging
import uvicorn

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run("qinglong.web:app", host="127.0.0.1", port=8080, workers=1, reload=True, reload_dirs=["qinglong"])
