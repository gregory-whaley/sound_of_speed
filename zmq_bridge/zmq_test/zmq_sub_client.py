import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:5556")
socket.setsockopt(zmq.SUBSCRIBE, b"")   # this is required even if there is no filter string

while True:
    message = socket.recv()
    print("Len: ",len(message))
    print(f"Recv: {message.hex()}")

