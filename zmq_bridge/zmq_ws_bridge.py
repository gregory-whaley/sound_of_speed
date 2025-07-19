#!/usr/bin/python3
# my version of a bridge with ZMQ subscriber feeding websockets.

#  Updated 19jul25 to implement zmq message handling inside the asyncio event loop,
#  so now both tornado websocket and zmq handling are managed by the one tornado (asyncio) event loop.
#
import tornado.websocket
import tornado.web
import asyncio
import zmq.eventloop.future
import sys
import array

zmq_pub_host = "tcp://localhost:5556"


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
            handler.write_message(message,binary=True)    
 


async def zmq_bridge_handler(bridge_zmq_socket):
#  wait for a ZMQ message from the publisher and push it out to all open websockets
 
    while True:
        message = await bridge_zmq_socket.recv_multipart()  # return type is list of bytes
        ws_frame = bytearray()      # empty bytearray
        for msg in message:
            ws_frame.extend(msg)     # concatinate bytearrays together into a single frame
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



async def main():
    
    # portion of main to set up zmq socket:
    # instantiate only one subscriber socket to listen to the publisher
    zmq_context = zmq.eventloop.future.Context()    # this is an awaitable future object
    bridge_zmq_socket = zmq_context.socket(zmq.SUB)  # instantiate socket object for this ws connection
    bridge_zmq_socket.connect(zmq_pub_host) # assign zmq socket to listen as a SUB to PUB server
    bridge_zmq_socket.setsockopt(zmq.SUBSCRIBE, b"")  # subscribe to all feeds

    
    # Add the zmq handler to the asyncio event queue
    asyncio.create_task(zmq_bridge_handler(bridge_zmq_socket))    
    
    # instantiate web app using websockethandler
    app = tornado.web.Application([(r"/ws", BridgeWebSocketHandler)])
    app.listen(8888)
    await asyncio.Event().wait()              # waits here forever as event loop proceeds.


print("WebSocket server started on port 8888")
if __name__ == "__main__":
    asyncio.run(main())

