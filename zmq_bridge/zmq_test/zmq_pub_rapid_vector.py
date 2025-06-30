# test zmq bridge server by sending fixed size, multipart zmq packets in rapid order.

import zmq
import time
import numpy as np
import sys

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:5556")

buf_size = 1024*8				# size of data buffer in float32 samples
num_speeds = 50
center = int(buf_size/2)      # pointer to center of buffer
span = 100                  # how many samples to include in  zmq packet

buffer = np.zeros(buf_size,dtype=np.float32)  # create buffer, fill with zero
p_sum=np.zeros(num_speeds,dtype=np.float32)                # allocate memory positive values
n_sum=np.zeros(num_speeds,dtype=np.float32)                # allocate memory negative values

i = 0
#while (i < 100000):
while True:
    socket.send_multipart([buffer[center-2*span:center+2*span],p_sum,n_sum])
    i+=1
    if (i % 100) == 0: print(i, end=' ')
    if (i % 1000) == 0: print()
    time.sleep(1)        
