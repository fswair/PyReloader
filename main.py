from triggers import send_to_discord, send_to_telegram
from worker.utils import Priotries
from worker import worker
import sys

MAINFILE = worker.main_file(__file__)

worker.set_trigger(target=send_to_discord)
worker.set_trigger(target=send_to_telegram, priotry=Priotries.HIGH)
if __name__ == "__main__":
    argv = sys.argv
    """
    -e arg1 arg2 arg3 'exclude file(s)'
    -wf file.py 'just watch a file' [future release]
    
    example command: "python3 main.py -e test.py triggers.py"
    """
    excluded_files = argv[argv.index("-e") + 1:]
    excluded_files.append(MAINFILE)
    worker.set_files(excluded_files=excluded_files)
    worker.run()