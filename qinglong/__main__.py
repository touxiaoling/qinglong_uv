import logging
import uvicorn


def main():
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("qinglong.web:app", host="0.0.0.0", port=80, workers=1)


if __name__ == "__main__":
    main()
