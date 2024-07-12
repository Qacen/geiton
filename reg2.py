import requests
import time
def registration():
    response = requests.put('https://games-test.datsteam.dev/play/zombidef/participate',headers=HEADERS)
    return(response)

while True:
    print(registration())
    time.sleep(10)