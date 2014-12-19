#ifndef SimpleSerialProtocol_h
#define SimpleSerialProtocol_h

#if defined(ARDUINO) && ARDUINO >= 100
  #include "Arduino.h"
#else
  #include "WProgram.h"
#endif

extern "C" {
  // callbacks have method signature: void cmd(byte, byte);
  typedef void (*cmdCallback)(byte, byte);
}

class SimpleSerialProtocol
{
public:
  SimpleSerialProtocol(Stream& s, cmdCallback fcn);
  
  /*** Encode and send a message packet ***/
  void sendMessage(byte CMD, byte value);
  
  /*** Receive and check the next message packet ***/
  void receiveNextMessage();
  
  const byte CMD_ACK = 0x01;
  const byte CMD_HEARTBEAT = 0x00;
    
private:
  const byte HEADER_BYTE_1 = 0xFF;
  const byte HEADER_BYTE_2 = 0xFE;
  Stream& serial;
  cmdCallback receive_callback;
};


#endif
