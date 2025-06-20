#!/usr/bin/python3
# -*- coding: utf-8 -*-

# zmq_SUB_proc.py
# Author: Marc Lichtman

import zmq
import numpy as np
import time
import matplotlib.pyplot as plt

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:5556") # connect, not bind, the PUB will bind, only 1 can bind
socket.setsockopt(zmq.SUBSCRIBE, b'') # subscribe to topic of all (needed or else it won't work)

while True:
    if socket.poll(10) != 0: # check if there is a message on the socket
#        msg = socket.recv() # grab the message
        msg = socket.recv_multipart() # grab the message
        buf_len = len(msg)   # size in bytes
        #print(buf_len) # size of msg
        print(buf_len,' ',end='')
        
#         for i in range(16):
#             print(msg[i],' ',end='')
#         print()
        
#         data = np.frombuffer(msg, dtype=float,count = -1)
#         for i in range(10):
#             print(data[i],' ',end='')
#         print()

#        plt.plot(data)
#        plt.show()


#         for i in range(buf_len // 32768):   # process in 8k blocks of 4 bytes
#         
#             data = np.frombuffer(msg, dtype=np.float32, offset = i*32768, count=8192) # make sure to use correct data type (complex64 or float32)
#             print(data[0:10])
#             
#             plt.plot(np.real(data))
#             plt.plot(np.imag(data))
#             plt.show()
    else:
        time.sleep(0.01) # wait 100ms and try again


