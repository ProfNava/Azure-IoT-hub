# MicroPython HTTPS example for Wokwi.com

import network
import urequests
import time

# Connect to WiFi
print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('RED WIFI', 'PASSWORD')
while not sta_if.isconnected():
  print(".", end="")
  time.sleep(0.25)
print("Connected!")
