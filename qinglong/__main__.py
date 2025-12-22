import logging
from qinglong.ui import MainPage

if __name__ in {"__main__", "__mp_main__"}:
    logging.basicConfig(level=logging.INFO)
    main_page = MainPage()
    main_page.start()
