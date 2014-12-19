import serial
import struct
import time
import array

from SerialProtocolClass import SimpleProtocolConnection


def test_fcn1(con ,cmd, val):
    print('cb: Heartbeat1', con.port, con.baud, cmd, val)
def test_fcn3(con ,cmd, val):
    print('cb: Heartbeat3', con.port, con.baud, cmd, val)

def test_fcn2(con ,cmd, val):
    print('cb: ACK', con.port, con.baud, cmd, val)

# tests

commands = (
    ("CMD_HEARTBEAT", 0),
    ("CMD_ACK", 1),
    ("CMD_TEST1", 4)
)

with SimpleProtocolConnection('/dev/ptys6', '9600', commands, True) as con:

    #print(con.command_to_id)
    #print(con.id_to_command)

    con.add_callback('CMD_HEARTBEAT', test_fcn1)
    con.add_callback('CMD_HEARTBEAT', test_fcn3)
    #con.add_callback('CMD_ACK', test_fcn2)

    con.send_command("CMD_TEST1", 123)
    con.send_command("CMD_HEARTBEAT", 2)

    time.sleep(4)
    con.clear_callback("CMD_HEARTBEAT")
    con.add_callback('CMD_ACK', test_fcn2)

    con.send_command("CMD_TEST1", 123)
    con.send_command("CMD_HEARTBEAT", 2)



    time.sleep(100)