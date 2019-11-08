#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  Automatic test of MilightWifiBridge library with fake socket (using a Mock) and
  getting stdout with a specific class.
"""

import unittest
from MilightWifiBridge import MilightWifiBridge
import logging
import time
import sys

# Python 2.7/3  (Mock)
if sys.version_info >= (3, 3):
  from unittest.mock import patch
else:
  from mock import patch

# Python 2.7/3 compatibility (StringIO)
try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO

class CapturingStdOut(list):
  """
  Capture stdout and give it back into a variable.

  Example:
  with CapturingStdOut() as std_output:
    anyFunctionHere()
  print(std_output)
  """
  def __enter__(self):
    self._stdout = sys.stdout
    sys.stdout = self._stringio = StringIO()
    return self
  def __exit__(self, *args):
    self.extend(self._stringio.getvalue().splitlines())
    del self._stringio    # free up some memory
    sys.stdout = self._stdout

class MockSocket:
  __read_write = []

  @staticmethod
  def initializeMock(read_write):
    MockSocket.__read_write = read_write

  @staticmethod
  def initializeMilight(ip = "127.0.0.1", port = 100):
    milight = MilightWifiBridge.MilightWifiBridge()
    milight.setup(ip, port)

    return milight

  @staticmethod
  def initializeMockAndMilight(command, zoneId, milight_response):
    def calculateCheckSum(command, zoneId):
      checkSum = 0
      for byteCommand in command:
        checkSum += byteCommand
      checkSum += zoneId

      return (checkSum & 0xFF)

    bytesToSend = bytearray([0x80, 0x00, 0x00, 0x00, 0x11, 0x20, 0x21, 0x00, 0x01, 0x00])
    bytesToSend += bytearray(command)
    bytesToSend += bytearray([int(zoneId), 0x00])
    bytesToSend += bytearray([int(calculateCheckSum(bytearray(command), int(zoneId)))])

    read_write = [
      # Start session request
      {'IN': bytearray([0x20,0x00,0x00,0x00,0x16,0x02,0x62,0x3a,0xd5,0xed,0xa3,0x01,0xae,
                        0x08,0x2d,0x46,0x61,0x41,0xa7,0xf6,0xdc,0xaf,0xd3,0xe6,0x00,0x00,0x1e])},
      # Start session response
      {'OUT': bytearray([0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x10,0x11,0x12,0x13,0x14,
                         0x15,0x16,0x17,0x18,0x19,0x20,0x21,0x22])},
      # Request
      {'IN': bytesToSend}
    ]

    if milight_response:
      read_write.append({'OUT': bytearray([0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x00])})

    MockSocket.initializeMock(read_write)

    return MockSocket.initializeMilight()

  def __init__(self, family = None, type = None):
    return

  def shutdown(self, how):
    return

  def close(self):
    return

  def connect(self, addr):
    return

  def settimeout(self, timeout_sec):
    return

  def sendto(self, data, addr):
    if len(MockSocket.__read_write) > 0:
      if 'IN' in MockSocket.__read_write[0]:
        check_val = MockSocket.__read_write[0]['IN']
        if bytearray(data) != bytearray(check_val):
          raise AssertionError('Mock Socket: Should write "' + str(check_val) + '" but "'+str(data)+'" requested')

        MockSocket.__read_write.pop(0)
        return len(data)

    return 0

  def recvfrom(self, bufsize):
    if len(MockSocket.__read_write) > 0:
      if 'OUT' in MockSocket.__read_write[0]:
        if len(MockSocket.__read_write[0]) <= bufsize:
          val = MockSocket.__read_write[0]['OUT']
          MockSocket.__read_write.pop(0)
          return (val, None)
        else:
          val = MockSocket.__read_write[0]['OUT'][:bufsize]
          MockSocket.__read_write[0]['OUT'] = MockSocket.__read_write[0]['OUT'][bufsize:]
          return (val, None)
    return ("", None)

class TestMilightWifiBridge(unittest.TestCase):
  """
  Test all the MilightWifiBridge class using fake socket (MockSocket) and getting the std output (CapturingStdOut)
  """
  def setUp(self):
    """
    Get test begining timestamp (used to show time to execute test at the end)
    """
    self.startTime = time.time()

    # Show full difference between 2 values that we wanted to be equal
    self.maxDiff = None

  def tearDown(self):
    """
    Show the execution time of the test
    """
    t = time.time() - self.startTime
    print(str(self.id())+": "+str(round(t, 2))+ " seconds")

  def test_instance(self):
    logging.debug("test_instance")
    milight = MilightWifiBridge.MilightWifiBridge()
    self.assertNotEqual(milight, None)

  @patch('socket.socket', new=MockSocket)
  def test_close(self, new=MockSocket):
    logging.debug("test_close")
    milight = MilightWifiBridge.MilightWifiBridge()
    self.assertTrue(milight.setup("127.0.0.1", 100))
    self.assertEqual(milight.close(), None)

  @patch('socket.socket', new=MockSocket)
  def test_setup(self, new=MockSocket):
    logging.debug("test_instance")
    milight = MilightWifiBridge.MilightWifiBridge()
    self.assertTrue(milight.setup("127.0.0.1", 100))

  @patch('socket.socket', new=MockSocket)
  def test_get_mac_address(self, new=MockSocket):
    logging.debug("test_get_mac_address")

    MockSocket.initializeMock([
      {'IN': bytearray([0x20,0x00,0x00,0x00,0x16,0x02,0x62,0x3a,0xd5,0xed,0xa3,0x01,0xae,
                        0x08,0x2d,0x46,0x61,0x41,0xa7,0xf6,0xdc,0xaf,0xd3,0xe6,0x00,0x00,0x1e])},
      {'OUT': bytearray([0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x10,0x11,0x12,0x13,0x14,
                         0x15,0x16,0x17,0x18,0x19,0x20,0x21,0x22])},
      {'IN': bytearray([0x20,0x00,0x00,0x00,0x16,0x02,0x62,0x3a,0xd5,0xed,0xa3,0x01,0xae,
                        0x08,0x2d,0x46,0x61,0x41,0xa7,0xf6,0xdc,0xaf,0xd3,0xe6,0x00,0x00,0x1e])},
      {'OUT': bytearray([0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x10,0x11,0x12,0x13,0x14,
                         0x15,0x16,0x17,0x18,0x19,0x20,0x21,0x22])}
    ])
    milight = MockSocket.initializeMilight()
    self.assertEqual(milight.getMacAddress(), "8:9:10:11:12:13")

    MockSocket.initializeMock([
      {'IN': bytearray([0x20,0x00,0x00,0x00,0x16,0x02,0x62,0x3a,0xd5,0xed,0xa3,0x01,0xae,
                        0x08,0x2d,0x46,0x61,0x41,0xa7,0xf6,0xdc,0xaf,0xd3,0xe6,0x00,0x00,0x1e])},
      {'OUT': bytearray([0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x10,0xFF,0x12,0xF0,0xFF,0xDE,0x14,
                         0x15,0x16,0x17,0x18,0x19,0x20,0x21,0x22])},
      {'IN': bytearray([0x20,0x00,0x00,0x00,0x16,0x02,0x62,0x3a,0xd5,0xed,0xa3,0x01,0xae,
                        0x08,0x2d,0x46,0x61,0x41,0xa7,0xf6,0xdc,0xaf,0xd3,0xe6,0x00,0x00,0x1e])},
      {'OUT': bytearray([0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x10,0x11,0x12,0x13,0x14,
                         0x15,0x16,0x17,0x18,0x19,0x20,0x21,0x22])}
    ])
    milight = MockSocket.initializeMilight()
    self.assertEqual(milight.getMacAddress(), "10:ff:12:f0:ff:de")

  @patch('socket.socket', new=MockSocket)
  def test_turn_on(self, new=MockSocket):
    logging.debug("test_turn_on")
    ON_CMD = bytearray([0x31,0x00,0x00,0x08,0x04,0x01,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(ON_CMD, 2, True).turnOn(2))
    self.assertFalse(MockSocket.initializeMockAndMilight(ON_CMD, 2, False).turnOn(2))

  @patch('socket.socket', new=MockSocket)
  def test_turn_off(self, new=MockSocket):
    logging.debug("test_turn_off")
    OFF_CMD = bytearray([0x31,0x00,0x00,0x08,0x04,0x02,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(OFF_CMD, 3, True).turnOff(3))
    self.assertFalse(MockSocket.initializeMockAndMilight(OFF_CMD, 3, False).turnOff(3))

  @patch('socket.socket', new=MockSocket)
  def test_turn_on_wifi_bridge(self, new=MockSocket):
    logging.debug("test_turn_on_wifi_bridge")
    WIFI_BRIDGE_LAMP_ON_CMD = bytearray([0x31,0x00,0x00,0x00,0x03,0x03,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(WIFI_BRIDGE_LAMP_ON_CMD, 1, True).turnOnWifiBridgeLamp())
    self.assertFalse(MockSocket.initializeMockAndMilight(WIFI_BRIDGE_LAMP_ON_CMD, 1, False).turnOnWifiBridgeLamp())

  @patch('socket.socket', new=MockSocket)
  def test_turn_off_wifi_bridge(self, new=MockSocket):
    logging.debug("test_turn_off_wifi_bridge")
    WIFI_BRIDGE_LAMP_OFF_CMD = bytearray([0x31,0x00,0x00,0x00,0x03,0x04,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(WIFI_BRIDGE_LAMP_OFF_CMD, 1, True).turnOffWifiBridgeLamp())
    self.assertFalse(MockSocket.initializeMockAndMilight(WIFI_BRIDGE_LAMP_OFF_CMD, 1, False).turnOffWifiBridgeLamp())

  @patch('socket.socket', new=MockSocket)
  def test_set_night_mode(self, new=MockSocket):
    logging.debug("test_set_night_mode")
    NIGHT_MODE_CMD = bytearray([0x31,0x00,0x00,0x08,0x04,0x05,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(NIGHT_MODE_CMD, 4, True).setNightMode(4))
    self.assertFalse(MockSocket.initializeMockAndMilight(NIGHT_MODE_CMD, 4, False).setNightMode(4))

  @patch('socket.socket', new=MockSocket)
  def test_set_white_mode(self, new=MockSocket):
    logging.debug("test_set_white_mode")
    WHITE_MODE_CMD = bytearray([0x31,0x00,0x00,0x08,0x05,0x64,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(WHITE_MODE_CMD, 4, True).setWhiteMode(4))
    self.assertFalse(MockSocket.initializeMockAndMilight(WHITE_MODE_CMD, 4, False).setWhiteMode(4))

  @patch('socket.socket', new=MockSocket)
  def test_set_white_mode_bridge(self, new=MockSocket):
    logging.debug("test_set_white_mode_bridge")
    WIFI_BRIDGE_LAMP_WHITE_MODE_CMD = bytearray([0x31,0x00,0x00,0x00,0x03,0x05,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(WIFI_BRIDGE_LAMP_WHITE_MODE_CMD, 1, True).setWhiteModeBridgeLamp())
    self.assertFalse(MockSocket.initializeMockAndMilight(WIFI_BRIDGE_LAMP_WHITE_MODE_CMD, 1, False).setWhiteModeBridgeLamp())

  @patch('socket.socket', new=MockSocket)
  def test_speed_up_disco_mode(self, new=MockSocket):
    logging.debug("test_speed_up_disco_mode")
    DISCO_MODE_SPEED_UP_CMD = bytearray([0x31,0x00,0x00,0x08,0x04,0x03,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(DISCO_MODE_SPEED_UP_CMD, 4, True).speedUpDiscoMode(4))
    self.assertFalse(MockSocket.initializeMockAndMilight(DISCO_MODE_SPEED_UP_CMD, 4, False).speedUpDiscoMode(4))

  @patch('socket.socket', new=MockSocket)
  def test_speed_up_disco_mode_bridge(self, new=MockSocket):
    logging.debug("test_speed_up_disco_mode_bridge")
    WIFI_BRIDGE_LAMP_DISCO_MODE_SPEED_UP_CMD = bytearray([0x31,0x00,0x00,0x00,0x03,0x02,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(WIFI_BRIDGE_LAMP_DISCO_MODE_SPEED_UP_CMD, 1, True).speedUpDiscoModeBridgeLamp())
    self.assertFalse(MockSocket.initializeMockAndMilight(WIFI_BRIDGE_LAMP_DISCO_MODE_SPEED_UP_CMD, 1, False).speedUpDiscoModeBridgeLamp())

  @patch('socket.socket', new=MockSocket)
  def test_slow_down_disco_mode(self, new=MockSocket):
    logging.debug("test_slow_down_disco_mode")
    DISCO_MODE_SLOW_DOWN_CMD = bytearray([0x31,0x00,0x00,0x08,0x04,0x04,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(DISCO_MODE_SLOW_DOWN_CMD, 4, True).slowDownDiscoMode(4))
    self.assertFalse(MockSocket.initializeMockAndMilight(DISCO_MODE_SLOW_DOWN_CMD, 4, False).slowDownDiscoMode(4))

  @patch('socket.socket', new=MockSocket)
  def test_slow_down_disco_mode_bridge(self, new=MockSocket):
    logging.debug("test_slow_down_disco_mode_bridge")
    WIFI_BRIDGE_LAMP_DISCO_MODE_SLOW_DOWN_CMD = bytearray([0x31,0x00,0x00,0x00,0x03,0x01,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(WIFI_BRIDGE_LAMP_DISCO_MODE_SLOW_DOWN_CMD, 1, True).slowDownDiscoModeBridgeLamp())
    self.assertFalse(MockSocket.initializeMockAndMilight(WIFI_BRIDGE_LAMP_DISCO_MODE_SLOW_DOWN_CMD, 1, False).slowDownDiscoModeBridgeLamp())

  @patch('socket.socket', new=MockSocket)
  def test_link(self, new=MockSocket):
    logging.debug("test_link")
    LINK_CMD = bytearray([0x3d,0x00,0x00,0x08,0x00,0x00,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(LINK_CMD, 2, True).link(2))
    self.assertFalse(MockSocket.initializeMockAndMilight(LINK_CMD, 3, False).link(3))

  @patch('socket.socket', new=MockSocket)
  def test_unlink(self, new=MockSocket):
    logging.debug("test_unlink")
    UNLINK_CMD = bytearray([0x3e,0x00,0x00,0x08,0x00,0x00,0x00,0x00,0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(UNLINK_CMD, 2, True).unlink(2))
    self.assertFalse(MockSocket.initializeMockAndMilight(UNLINK_CMD, 3, False).unlink(3))

  @patch('socket.socket', new=MockSocket)
  def test_set_disco_mode(self, new=MockSocket):
    logging.debug("test_set_disco_mode")
    def getDiscoModeCmd(mode):
      return bytearray([0x31, 0x00, 0x00, 0x08, 0x06, mode, 0x00, 0x00, 0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(getDiscoModeCmd(1), 2, True).setDiscoMode(1, 2))
    self.assertTrue(MockSocket.initializeMockAndMilight(getDiscoModeCmd(9), 3, True).setDiscoMode(9, 3))
    self.assertTrue(MockSocket.initializeMockAndMilight(getDiscoModeCmd(9), 3, True).setDiscoMode(50, 3))
    self.assertTrue(MockSocket.initializeMockAndMilight(getDiscoModeCmd(9), 3, True).setDiscoMode(9999, 3))
    self.assertTrue(MockSocket.initializeMockAndMilight(getDiscoModeCmd(1), 3, True).setDiscoMode(-454, 3))
    self.assertFalse(MockSocket.initializeMockAndMilight(getDiscoModeCmd(1), 2, False).setDiscoMode(1, 2))

  @patch('socket.socket', new=MockSocket)
  def test_set_disco_mode_bridge(self, new=MockSocket):
    logging.debug("test_set_disco_mode_bridge")
    def getDiscoModeBridgeCmd(mode):
      return bytearray([0x31, 0x00, 0x00, 0x00, 0x04, mode, 0x00, 0x00, 0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(getDiscoModeBridgeCmd(1), 1, True).setDiscoModeBridgeLamp(1))
    self.assertTrue(MockSocket.initializeMockAndMilight(getDiscoModeBridgeCmd(9), 1, True).setDiscoModeBridgeLamp(9))
    self.assertTrue(MockSocket.initializeMockAndMilight(getDiscoModeBridgeCmd(9), 1, True).setDiscoModeBridgeLamp(50))
    self.assertTrue(MockSocket.initializeMockAndMilight(getDiscoModeBridgeCmd(9), 1, True).setDiscoModeBridgeLamp(9999))
    self.assertTrue(MockSocket.initializeMockAndMilight(getDiscoModeBridgeCmd(1), 1, True).setDiscoModeBridgeLamp(-19))
    self.assertFalse(MockSocket.initializeMockAndMilight(getDiscoModeBridgeCmd(1), 1, False).setDiscoModeBridgeLamp(1))

  @patch('socket.socket', new=MockSocket)
  def test_set_color(self, new=MockSocket):
    logging.debug("test_set_color")
    def getColorCmd(color):
      return bytearray([0x31, 0x00, 0x00, 0x08, 0x01, color, color, color, color])
    self.assertTrue(MockSocket.initializeMockAndMilight(getColorCmd(1), 0, True).setColor(1, 0))
    self.assertTrue(MockSocket.initializeMockAndMilight(getColorCmd(50), 3, True).setColor(50, 3))
    self.assertTrue(MockSocket.initializeMockAndMilight(getColorCmd(255), 2, True).setColor(9999, 2))
    self.assertTrue(MockSocket.initializeMockAndMilight(getColorCmd(0), 2, True).setColor(-785, 2))
    self.assertFalse(MockSocket.initializeMockAndMilight(getColorCmd(1), 2, False).setColor(1, 2))

  @patch('socket.socket', new=MockSocket)
  def test_set_color_bridge(self, new=MockSocket):
    logging.debug("test_set_color_bridge")
    def getColorBridgeCmd(color):
      return bytearray([0x31, 0x00, 0x00, 0x00, 0x01, color, color, color, color])
    self.assertTrue(MockSocket.initializeMockAndMilight(getColorBridgeCmd(1), 1, True).setColorBridgeLamp(1))
    self.assertTrue(MockSocket.initializeMockAndMilight(getColorBridgeCmd(50), 1, True).setColorBridgeLamp(50))
    self.assertTrue(MockSocket.initializeMockAndMilight(getColorBridgeCmd(255), 1, True).setColorBridgeLamp(9999))
    self.assertTrue(MockSocket.initializeMockAndMilight(getColorBridgeCmd(0), 1, True).setColorBridgeLamp(-785))
    self.assertFalse(MockSocket.initializeMockAndMilight(getColorBridgeCmd(1), 1, False).setColorBridgeLamp(1))

  @patch('socket.socket', new=MockSocket)
  def test_brightness(self, new=MockSocket):
    logging.debug("test_brightness")
    def getBrightnessCmd(brightness):
      return bytearray([0x31, 0x00, 0x00, 0x08, 0x03, brightness, 0x00, 0x00, 0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(getBrightnessCmd(1), 0, True).setBrightness(1, 0))
    self.assertTrue(MockSocket.initializeMockAndMilight(getBrightnessCmd(50), 3, True).setBrightness(50, 3))
    self.assertTrue(MockSocket.initializeMockAndMilight(getBrightnessCmd(100), 2, True).setBrightness(15522, 2))
    self.assertTrue(MockSocket.initializeMockAndMilight(getBrightnessCmd(0), 2, True).setBrightness(-785, 2))
    self.assertFalse(MockSocket.initializeMockAndMilight(getBrightnessCmd(0), 2, False).setBrightness(0, 2))

  @patch('socket.socket', new=MockSocket)
  def test_brightness_bridge(self, new=MockSocket):
    logging.debug("test_brightness_bridge")
    def getBrightnessBridgeCmd(brightness):
      return bytearray([0x31, 0x00, 0x00, 0x00, 0x02, brightness, 0x00, 0x00, 0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(getBrightnessBridgeCmd(1), 1, True).setBrightnessBridgeLamp(1))
    self.assertTrue(MockSocket.initializeMockAndMilight(getBrightnessBridgeCmd(50), 1, True).setBrightnessBridgeLamp(50))
    self.assertTrue(MockSocket.initializeMockAndMilight(getBrightnessBridgeCmd(100), 1, True).setBrightnessBridgeLamp(15522))
    self.assertTrue(MockSocket.initializeMockAndMilight(getBrightnessBridgeCmd(0), 1, True).setBrightnessBridgeLamp(-785))
    self.assertFalse(MockSocket.initializeMockAndMilight(getBrightnessBridgeCmd(10), 1, False).setBrightnessBridgeLamp(10))

  @patch('socket.socket', new=MockSocket)
  def test_saturation(self, new=MockSocket):
    logging.debug("test_saturation")
    def getSaturationCmd(saturation):
      return bytearray([0x31, 0x00, 0x00, 0x08, 0x02, saturation, 0x00, 0x00, 0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(getSaturationCmd(1), 0, True).setSaturation(1, 0))
    self.assertTrue(MockSocket.initializeMockAndMilight(getSaturationCmd(50), 3, True).setSaturation(50, 3))
    self.assertTrue(MockSocket.initializeMockAndMilight(getSaturationCmd(100), 2, True).setSaturation(15522, 2))
    self.assertTrue(MockSocket.initializeMockAndMilight(getSaturationCmd(0), 2, True).setSaturation(-785, 2))
    self.assertFalse(MockSocket.initializeMockAndMilight(getSaturationCmd(0), 2, False).setSaturation(0, 2))

  @patch('socket.socket', new=MockSocket)
  def test_temperature(self, new=MockSocket):
    logging.debug("test_temperature")
    def getTemperatureCmd(temperature):
      return bytearray([0x31, 0x00, 0x00, 0x08, 0x05, temperature, 0x00, 0x00, 0x00])
    self.assertTrue(MockSocket.initializeMockAndMilight(getTemperatureCmd(1), 0, True).setTemperature(1, 0))
    self.assertTrue(MockSocket.initializeMockAndMilight(getTemperatureCmd(50), 3, True).setTemperature(50, 3))
    self.assertTrue(MockSocket.initializeMockAndMilight(getTemperatureCmd(100), 2, True).setTemperature(15522, 2))
    self.assertTrue(MockSocket.initializeMockAndMilight(getTemperatureCmd(0), 2, True).setTemperature(-785, 2))
    self.assertFalse(MockSocket.initializeMockAndMilight(getTemperatureCmd(0), 2, False).setTemperature(0, 2))

  @patch('socket.socket', new=MockSocket)
  def test_all_cmd_request_except_help_cmd(self):
    logging.debug("test_all_cmd_request_except_help_cmd")

    # Request failed because nothing requested
    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((['--ip', '127.0.0.1', '--port', '1234', '--timeout', '5', '--zone', '0', '--nodebug', '--debug']))
    self.assertNotEqual(cm.exception.code, 0)
    self.assertTrue("Debugging..." in std_output)
    self.assertTrue("Ip: 127.0.0.1" in std_output)
    self.assertTrue("Zone: 0" in std_output)
    self.assertTrue("Timeout: 5" in std_output)
    self.assertTrue("Port: 1234" in std_output)
    self.assertTrue("[ERROR] You must call one action, use '-h' to get more information." in std_output)

    # Invalid parameters
    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main(([]))
    self.assertNotEqual(cm.exception.code, 0)
    self.assertTrue("[ERROR] You need to specify the ip..." in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main(('--ip', '127.0.0.1', '--port', '-4'))
    self.assertNotEqual(cm.exception.code, 0)
    self.assertTrue("[ERROR] You need to specify a valid port (more than 0)" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main(('--ip', '127.0.0.1', '--timeout', '-4'))
    self.assertNotEqual(cm.exception.code, 0)
    self.assertTrue("[ERROR] You need to specify a valid timeout (more than 0sec)" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main(('--ip', '127.0.0.1', '--zone', '-7'))
    self.assertNotEqual(cm.exception.code, 0)
    self.assertTrue("[ERROR] You need to specify a valid zone ID (between 0 and 4)" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main(('--ip', '127.0.0.1', '--zone', '7'))
    self.assertNotEqual(cm.exception.code, 0)
    self.assertTrue("[ERROR] You need to specify a valid zone ID (between 0 and 4)" in std_output)

    # Show help
    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("LINK (-l, --link): Link lights to a specific zone" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "help"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "ip"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "port"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "timeout"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "zone"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "getmacaddress"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "link"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "unlink"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "turnon"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "turnoff"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "turnonwifibridgelamp"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "turnoffwifibridgelamp"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "setnightmode"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "setwhitemode"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "setwhitemodebridgelamp"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "speedupdiscomodebridgelamp"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "slowdowndiscomodebridgelamp"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "speedupdiscomode"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "slowdowndiscomode"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "setcolor"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "setbrightness"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "setcolorbridgelamp"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "setbrightnessbridgelamp"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "setsaturation"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "settemperature"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "setdiscomode"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

    with self.assertRaises(SystemExit) as cm:
      with CapturingStdOut() as std_output:
        MilightWifiBridge.main((["--help", "setdiscomodebridgelamp"]))
    self.assertEqual(cm.exception.code, 0)
    self.assertTrue("Usage:" in std_output)

if __name__ == '__main__':
  logger = logging.getLogger()
  logger.setLevel(logging.DEBUG)
  unittest.main()
