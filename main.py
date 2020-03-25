import sys
import storeS3
import surveillance
import piExecute
import multiprocessing as mp
import time


def call_pushData():
    time.sleep(0.1)
    storeS3.main()


def call_surveillance(maxVal):
    time.sleep(0.1)
    surveillance.main(maxVal)

def call_execute():
    time.sleep(0.1)
    piExecute.main()


if __name__ == '__main__':
    process1 = mp.Process(target=call_pushData)
    process1.start()

    process2 = mp.Process(target=call_surveillance, args=[int(sys.argv[1]), ])
    process2.start()

    process3 = mp.Process(target=call_execute)
    process3.start()

    process1.join()
    process2.join()
    process3.join()
