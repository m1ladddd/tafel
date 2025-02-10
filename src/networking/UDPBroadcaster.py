##
# @file Broadcaster.py
#
# @brief Broadcast UDP messages at a certain interval over LAN.
#
# @section libraries Libraries/Modules
# - socket
# - threading
# - time
#
# @section todo TODO
# - None
#
# @section author Author(s)
# - Created by Jop Merz on 03/02/2023.
# - Modified by Jop Merz on 03/02/2023.
##

import socket
from threading import Thread
from time import sleep

class UDPBroadcaster:
    """! 
    Broadcast UDP messages at a certain interval over a local network.
    """

    def __init__(self):
        """!
        Constructor.
        """

        ## UDP network socket
        self.__socket = None

        ## Thread which send the breadcast messages at an inteval
        self.__broadcast_thread = None

        ## Network interface to send from
        self.__interface: str = ""

        ## IP address to send to (255.255.255.255 = broadcast)
        self.__ip: str = "255.255.255.255"

        ## Network port to send to
        self.__port: int = 5005

        ## Broadcast string message
        self.__message: str = ""

        ## Time between broadcast messags in seconds
        self.__interval: float = 1.0

        ## Broadcasting yes or no
        self.__enable: bool = False


    def __broadcast_thread_function(self):
        """!
        Send broadcast messages at a certain interval.
        Stops when self.__enable is False.
        """
        messags_send = 0
        while(self.__enable):
            self.broadcast_message(self.__message)
            sleep(self.__interval) 
            messags_send = messags_send+1


    def set_port(self, port: int):
        """!
        Set the network port for this Broadcaster instance.
        @param port int Network port
        """
        self.__port = port


    def set_message(self, message: str):
        """!
        Set the broadcast message for this Broadcaster instance.
        @param message str Broadcast message
        """
        self.__message = message


    def set_interval(self, interval: float):
        """!
        Set the inteval between messages for this Broadcaster instance.
        @param interval float Interval between messages in seconds
        """
        self.__interval = interval


    def start_broadcasting(self):
        """!
        Start broadcasting.
        """
        self.__enable = True

        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__socket.bind((self.__interface , 0))

        self.__broadcast_thread = Thread(target=self.__broadcast_thread_function)
        self.__broadcast_thread.start()


    def stop_broadcasting(self):
        """!
        Stop broadcasting.
        """
        self.__enable = False
        self.__broadcast_thread.join()


    def broadcast_message(self, message):
        """!
        Broadcast one message.
        @param message: String in UTF-8 format
        """
        self.__socket.sendto(message, (self.__ip, self.__port))