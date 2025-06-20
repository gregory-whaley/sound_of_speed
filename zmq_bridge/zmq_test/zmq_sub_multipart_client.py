import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://10.0.0.201:5556")
socket.setsockopt(zmq.SUBSCRIBE, b"")   # this is required even if there is no filter string

for i in range(1):
    message = socket.recv_multipart()
    print(f"Recv: {len(message)} messages")
    for msg in message:
        print("LEN: ",len(msg))
        print("MSG: ",msg.hex(),"\n")
