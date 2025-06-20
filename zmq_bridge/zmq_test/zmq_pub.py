import zmq
import time

context = zmq.Context()
#socket = context.socket(zmq.PUSH)
socket = context.socket(zmq.PUB)
#socket.connect("tcp://127.0.0.1:5556")
socket.bind("tcp://127.0.0.1:5556")

i = 0
while True:
    message = "Hello from zmq publisher on port 5556 "+str(i)
    socket.send_string(message)
    print(f"Sent: {message}")
    i+=1
    time.sleep(1)        
