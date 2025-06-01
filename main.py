import logging
from qinglong import MainPage

if __name__ in {"__main__", "__mp_main__"}:
    logging.basicConfig(level=logging.DEBUG)
    main_page = MainPage()
    main_page.start(debug=True, host="localhost", port=8080)
