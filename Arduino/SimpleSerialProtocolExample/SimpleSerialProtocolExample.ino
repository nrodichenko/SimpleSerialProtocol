//***
//*** Arduino Serial Protocol Library
/*
    Copyright (C) 2014  Nikita Rodichenko
    E-mail: nikita.rodichenko <at> gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include "SimpleSerialProtocol.h"

//Uncomment below to enable Debug messages
//#define DEBUG 1


//Blinker
#define LED_PIN 13
bool blinkState = false;

//Update rates
static int CYCLE_HEARTBEAT = 5000; //0.2hz
static int CYCLE_SERIAL_READ = 1000; //20hz

byte count = 0;

//Update timers
long last_time_heartbeat;
long last_time_serial_read;
long current_time;

//*******Protocol Commands*******/
#define CMD_CUSTOM_MSG_1 0x02

//***end of Packet Commands****/

SimpleSerialProtocol p(Serial, evaluateMessage);

/************************************************************/
/*********************Initialization*************************/
/************************************************************/

void setup() {
    // Reset all timers
    current_time = millis();
    last_time_heartbeat = current_time;
    last_time_serial_read = current_time;
    
    pinMode(LED_PIN, OUTPUT); // Configure Arduino LED for
    Serial.begin(9600); // initialize serial communication
}



/************************************************************/
/*********************Main loop******************************/
/************************************************************/

void loop() {
  current_time = millis();
  
  /*** On timer: Blink the LED / Send Heartbeat ***/
    if (current_time - last_time_heartbeat > CYCLE_HEARTBEAT)
    {
      last_time_heartbeat = current_time;
      // blink LED to indicate activity
      blinkState = !blinkState;
      digitalWrite(LED_PIN, blinkState);
      
      p.sendMessage(p.CMD_HEARTBEAT, count);
      count += 1;
    }
  
  /*** On timer: Read remote control from serial ***/
    if (current_time - last_time_serial_read > CYCLE_SERIAL_READ)
    {
      last_time_serial_read = current_time;
      p.receiveNextMessage();
    }
  

}

/*** Parse the received message packet ***/
void evaluateMessage(byte CMD, byte value)
{
  p.sendMessage(p.CMD_ACK, CMD);
  return;
}
