import zmq
import time
import numpy as np

context = zmq.Context()
#socket = context.socket(zmq.PUSH)
socket = context.socket(zmq.PUB)
#socket.connect("tcp://127.0.0.1:5556")
socket.bind("tcp://127.0.0.1:5556")


data = np.zeros(4,dtype=np.float32)
i = 0
while True:
    data[0] = 3.14
    data[1] = 2.5
    data[2] = 1 /3.0
    socket.send(data)   # array in float32 little endian
    print(f"Sent: {data}")
    i+=1
    time.sleep(1)        
