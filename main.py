import threading
import sys
import storeS3
import surveillance
import piExecute


def call_pushData():
    storeS3.main()


def call_surveillance(maxVal):
    surveillance.main(maxVal)

def call_execute():
    piExecute.main()


if __name__ == '__main__':
    thread1 = threading.Thread(target=call_pushData)
    thread1.start()

    thread2 = threading.Thread(target=call_surveillance, args=[int(sys.argv[1]), ])
    thread2.start()

    thread3 = threading.Thread(target=call_pushData)
    thread3.start()

    thread1.join()
    thread2.join()
    thread3.join()
