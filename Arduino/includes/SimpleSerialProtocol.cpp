
#include "Arduino.h"
#include "SimpleSerialProtocol.h"

SimpleSerialProtocol::SimpleSerialProtocol(Stream& s, cmdCallback fcn):serial(s)
{
  receive_callback = fcn;
}


void SimpleSerialProtocol::sendMessage(byte CMD, byte value)
{
  serial.write(HEADER_BYTE_1); 
  serial.write(HEADER_BYTE_2);
  
  uint8_t checksum = 0;
  serial.write(CMD);
  checksum += CMD;
  serial.write(value);
  checksum += value;
  serial.write(checksum);
}


void SimpleSerialProtocol::receiveNextMessage()
{
  static enum _serial_state {
    IDLE,
    HEADER1,
    HEADER2,
    MSG_CMD,
    MSG_VAL
  } 
  c_state;

  static uint8_t checksum, cmd, value;

  uint8_t c;
  while (serial.available()){
    c = serial.read();
    
    if (c_state == IDLE) {
      c_state = (c==HEADER_BYTE_1) ? HEADER1 : IDLE;
    } 
    else if (c_state == HEADER1) {
      c_state = (c==HEADER_BYTE_2) ? HEADER2 : IDLE;
    } 
    else if (c_state == HEADER2) {
      cmd = c;
      c_state = MSG_CMD;
      checksum = cmd;
    }
    else if (c_state == MSG_CMD) {
      value = c;
      checksum = checksum + value;
      c_state = MSG_VAL;
    } 
    else if (c_state == MSG_VAL) { //now expecting checksum
      if (checksum == c) {  // compare calculated and transferred checksum
        (*receive_callback)(cmd, value);  // we got a valid packet, evaluate it
      }
      c_state = IDLE;
      return;
    }
  }
}
