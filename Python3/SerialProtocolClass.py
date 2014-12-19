import serial
import struct
import time
import array
import threading
from queue import Queue


# Ideas list
    # Idea - make a video about using the created library

# Main architecture:
    # - connection established upon object instantiation
    # - constructor receives baud/port and a set of possible commands in a tuple of Strings
    # - - numeric values for each command are assigned automatically
    # - communication is done in a separate thread
    # - callback functions can be defined for incoming messages of various types

# Callback architecture
    # callbacks are stored as a dictionary:
    # COMMAND_NAME_STRING -> LIST_OF_FCN_HANDLES.
    # Callback functions are expected to have format:
    # def proto_callback(connection, command, value), where
    # connection - is a SimpleProtocolConnection object
    # command - is a string with command name
    # value - is an integer from 0 to 255

class SimpleProtocolConnection:

    def __init__(self, port, baud, commands, debug = False):
        self.debug = debug
        if self.debug:
            print("__init__")

        # define constants
        self.S_IDLE = 0
        self.S_HEADER1 = 1
        self.S_HEADER2 = 2
        self.S_MSG_CMD = 3
        self.S_MSG_VAL = 4
        self.c_state = self.S_IDLE
        self.HEADER_BYTE_1 = 0xFF
        self.HEADER_BYTE_2 = 0XFE

        self.value = 0
        self.checksum = 0
        self.cmd = 0
        self.inBuf = []

        self.is_connected = False
        self.is_connecting = False

        self.port = port
        self.baud = baud
        
        #enum_commands = enumerate(commands)
        self.command_to_id = dict(commands)
        self.id_to_command = {idx:command for command, idx in self.command_to_id.items()}
        #self.id_to_command = dict(enum_commands)
        #self.command_to_id = {command:idx for idx, command in self.id_to_command.items()}

        # threading
        self.main_thread = None

        # init callback dictionary
        self.callbacks = dict((command, []) for command, idx in commands)

        # init ouput command queue
        self.output_commands = Queue(maxsize=0)

        # start a new thread for serial communications
        # store thread in a variable
        # thread can be manipulated to create new / delete callbacks

    # -------- With statement support --------

    def __enter__(self):
        if self.debug:
            print("__enter__")

        self.open()
        return self

    def __exit__(self, type, value, traceback):
        if self.debug:
            print("__exit__")

        self.close()

    # -------- End of with statement support --------


    # -------- Callback dispatching --------

    def add_callback(self, command, fcn):
        if command in self.callbacks.keys():
            # add a callback to the callback dict
            if fcn not in self.callbacks[command]:
                # prevent duplicate callbacks
                self.callbacks[command].append(fcn)
        else:
            # no such command => throw an exception
            raise Exception("No such command: %s" % command)

    def clear_callback(self, command):
        if command in self.callbacks.keys():
            self.callbacks[command] = []

    def fire_callbacks(self, command, value):
        if command in self.callbacks.keys():
            for fcn in self.callbacks[command]:
                fcn(self, command, value)

    # -------- End of callback dispatching --------

    # -------- Connection dispatching -------- 
    def open(self):

        # helper threading class
        class ConnectionThread(threading.Thread):
            def __init__(self, connection):
                threading.Thread.__init__(self)
                self.connection = connection

            def run(self):
                self.connection.main_loop()

        # clear the stop flag
        self.do_stop = False

        if self.debug:
            print('Connecting')

        # create and launch the connectiob thread
        self.main_thread = ConnectionThread(self)
        self.main_thread.start()


    def close(self):
        if self.debug:
            print('Disonnecting')

        # set the stop flag
        self.do_stop = True


    def main_loop(self):
        if self.debug:
            print('Entering main loop')

        self.is_connecting = True
        with serial.Serial(self.port, self.baud) as self.ser:
            self.is_connecting = False
            self.is_connected = True
        
            # sleep for serial initialisation to complete
            time.sleep(1.0)
         
            while not self.do_stop:
                #print('Main loop iteration')
                if (self.ser.inWaiting() > 0):
                    self.read_and_decode_message()
                if not self.output_commands.empty():
                    (out_cmd, out_val) = self.output_commands.get()
                    self.encode_and_send_message(out_cmd, out_val)
                    self.output_commands.task_done()
                time.sleep(0.05)

            if self.debug:
                print('Leaving main loop')

            self.is_connected = False

    def send_command(self, command, value):
        if self.is_connected or self.is_connecting:
            if command in self.callbacks.keys():
                
                if self.debug:
                    print("Queueing command", command, value)
                
                self.output_commands.put((command, value))
            else:
                # no such command => throw an exception
                raise Exception("No such command: %s" % command)
        else:
            # not connected => throw an exception
            raise Exception("Not connected")

        pass

    # -------- end of connection dispatching -------- 


    # -------- Protocol definition (decode/encode) -------- 
    def to8bit(self, x):
        return (x%(1<<8))

    def read_and_decode_message(self):
        c = self.ser.read(1)
        while not(type(c) == type(2)):
            c = bytearray(c)[0]
            if (self.c_state == self.S_IDLE):
                self.c_state =  self.S_HEADER1  if (c==self.HEADER_BYTE_1) else self.S_IDLE
            elif (self.c_state == self.S_HEADER1):
                self.c_state = self.S_HEADER2 if(c==self.HEADER_BYTE_2) else self.S_IDLE
            elif (self.c_state == self.S_HEADER2):
                self.cmd = c
                self.checksum = 0
                self.checksum = self.to8bit(self.checksum + c)
                self.c_state = self.S_MSG_CMD
            elif (self.c_state == self.S_MSG_CMD):
                self.value = c
                self.checksum = self.to8bit(self.checksum + c)
                self.c_state = self.S_MSG_VAL  # the command is to follow
            elif (self.c_state == self.S_MSG_VAL):
                if (self.to8bit(self.checksum) == self.to8bit(c)):  # compare calculated and transferred checksum
                    #print("good checksum")  # we got a valid packet, evaluate it
                    cmd_str = self.id_to_command.get(self.cmd, self.cmd)
                    
                    if self.debug:
                        self.echo_command_received(cmd_str, self.value)
                    
                    self.fire_callbacks(cmd_str, self.value)
                else :
                    a = 0
                    
                    if self.debug:
                        print ("wrong checksum: " , self.to8bit(self.checksum) , self.to8bit(c))

                self.c_state = self.S_IDLE
                return 
            c = self.ser.read()

    def encode_and_send_message(self, command, value):
        checksum = 0
        cmd_id = self.command_to_id[command]
        checksum = self.to8bit(checksum + cmd_id)
        checksum = self.to8bit(checksum + value)
        ar = array.array('B', [self.HEADER_BYTE_1, self.HEADER_BYTE_2, cmd_id, value, checksum]).tostring();
        #print(ar)
        
        if self.debug:
            self.echo_command_sent(command, value)

        self.ser.write(ar)

    def echo_command_sent(self, command, value):
        print("Sent", "\t", command, "\t", "with value", value)
    def echo_command_received(self, command, value):
        print("Received", "\t", command, "\t", "with value", value)

    # -------- end of protocol definition -------- 


# End of class SimpleProtocolConnection:










