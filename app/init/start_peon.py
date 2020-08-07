import time
import traceback

from peon.app import Peon


def start():
    try:
        print("Starting peon...")
        Peon().run()
    except:
        print("Exception occured!")
        traceback.print_exc()
    finally:
        time.sleep(5)
        start()


if __name__ == "__main__":
    start()
