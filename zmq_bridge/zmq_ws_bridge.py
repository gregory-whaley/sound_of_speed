#!/usr/bin/python3
# my version of a bridge with ZMQ subscriber feeding websockets.
#
import tornado.ioloop
import tornado.websocket
import tornado.web
import asyncio
import zmq
import threading
import time
import sys
import array

zmq_pub_host = "tcp://127.0.0.1:5556"


class BridgeWebSocketHandler(tornado.websocket.WebSocketHandler):
    instances = []    # class-wide attribute to store references to all handler instances
    
    def check_origin(self, origin):  # this is needed to allow localhost to serve local sockets
        return True

    def open(self):                    # constructor call upon opening ws
        print("WebSocket connection opened")
        BridgeWebSocketHandler.instances.append(self)    # store instance on stack
        print("Num open handlers: ",len(BridgeWebSocketHandler.instances))
 
    def on_message(self, message):   # handle incoming ws messages - should be none
        print(f"Received message: {message}")
 
    def on_close(self):              # destruct zmq socket if ws is closed
        print("WebSocket connection closed")
        BridgeWebSocketHandler.instances.remove(self)    # removes this handler from list of open ws handlers
        print("Num open handlers: ",len(BridgeWebSocketHandler.instances))
        
    @classmethod
    def send_to_ws(cls, message):
        for handler in cls.instances:
            handler.write_message(message,binary=True)    # this seems to have a memory leak
 #           print("frame length = ",len(message))

def zmq_bridge_handler():
#  wait for a ZMQ message from the publisher and push it out to all open websockets
    asyncio.set_event_loop(asyncio.new_event_loop())  # needed to give thread access to event loop

    while True:
        message = bridge_zmq_socket.recv_multipart()  # type is list of bytes
        ws_frame = bytearray()      # empty bytearray
        for msg in message:
            ws_frame.extend(msg)     # concatinate bytearrays together into a single frame
#        print("Frame length = ",len(ws_frame))
#        print("Message: ",message[0].hex())
#        print("Frame: ",ws_frame.hex())
        if sys.byteorder == 'little':         # need to convert to big endian to send to ws
            big_endian_array = array.array('f')   # start with empty array of floats in little byte order
            big_endian_array.frombytes(ws_frame)   # load frame in little byte order format
            big_endian_array.byteswap()            # convert to big endian
            ws_frame = big_endian_array.tobytes()   # convert big endian float array to bytes

        ws_frame = int(len(message[0])).to_bytes(2,'big') + ws_frame  # prepend the size int as two byte BE
        BridgeWebSocketHandler.send_to_ws(ws_frame)


#    a single frame is built of the following:
#    two byte int of the number of samples in the array, each float32 sample is 4 bytes
#    the array of floats
#    the positive overlap array of floats
#    the negative overlap array of floats
#    The overlap array size is calculated by the ws javascript from the frame total minus the delay and int value lengths.

if __name__ == "__main__":
     # instantiate only one subscriber socket to listen to the publisher
    zmq_context = zmq.Context()    # this is global in scope
    bridge_zmq_socket = zmq_context.socket(zmq.SUB)  # instantiate socket object for this ws connection
    bridge_zmq_socket.connect(zmq_pub_host) # assign zmq socket to listen as a SUB to PUB server
#    connection_closed = bridge_zmq_socket.closed
#    print(connection_closed)
#    assert (not connection_closed),"Error...No Publisher Found at "+zmq_pub_host
    bridge_zmq_socket.setsockopt(zmq.SUBSCRIBE, b"")  # subscribe to all feeds

    # Start the zmq handler in a separate thread
    zmq_thread = threading.Thread(target=zmq_bridge_handler, daemon=True)
    zmq_thread.start()
    
    # instantiate web app using websockethandler
    app = tornado.web.Application([(r"/ws", BridgeWebSocketHandler)])
    app.listen(8888)

    print("WebSocket server started on port 8888")
    tornado.ioloop.IOLoop.current().start()

