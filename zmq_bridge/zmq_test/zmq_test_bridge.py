# my version of a test bridge with ZMQ subscriber feeding websockets.
#
import tornado.ioloop
import tornado.websocket
import tornado.web
import asyncio
import zmq
import threading
import time

class BridgeWebSocketHandler(tornado.websocket.WebSocketHandler):
    instances = []    # class-wide attribute to store references to all instances
    
    def check_origin(self, origin):  # this is needed to allow localhost to serve local sockets
        return True

    def open(self):                    # constructor call upon opening ws
        print("WebSocket connection opened")
        BridgeWebSocketHandler.instances.append(self)    # store instance on stack
#        print(len(BridgeWebSocketHandler.instances)," websocket instances")

 
    def on_message(self, message):   # handle incoming ws messages
        print(f"Received message: {message}")
 
    def on_close(self):              # destruct zmq socket if ws is closed
        print("WebSocket connection closed")
        BridgeWebSocketHandler.instances.remove(self)    # removes this handler from list of open ws handlers
#        print(len(BridgeWebSocketHandler.instances)," websocket instances")

    def send_to_ws(self, message):
#        print(f"calling ws send method with messsage {message}")
        self.write_message(message)

def zmq_bridge_handler():
#  wait for a ZMQ message from the publisher and push it out to all open websockets
    asyncio.set_event_loop(asyncio.new_event_loop())  # needed to give thread access to event loop
    while True:
        message = bridge_zmq_socket.recv()
#        print(f"Rec ZMQ: {message}")
#        print(len(BridgeWebSocketHandler.instances)," websocket instances")
        for handler in BridgeWebSocketHandler.instances:  # send message to all open websockets
            handler.send_to_ws(message)


if __name__ == "__main__":
     # instantiate only one subscriber socket to listen to the publisher
    zmq_context = zmq.Context()    # this is global in scope
    bridge_zmq_socket = zmq_context.socket(zmq.SUB)  # instantiate socket object for this ws connection
    bridge_zmq_socket.connect("tcp://127.0.0.1:5556") # assign zmq socket to listen as a SUB to localhost port 5556
    bridge_zmq_socket.setsockopt(zmq.SUBSCRIBE, b"")  # subscribe to all feeds

    # Start the zmq handler in a separate thread
    zmq_thread = threading.Thread(target=zmq_bridge_handler, daemon=True)
    zmq_thread.start()
    
    # instantiate web app using websockethandler
    app = tornado.web.Application([(r"/ws", BridgeWebSocketHandler)])
    app.listen(8888)

    print("WebSocket server started on port 8888")
    tornado.ioloop.IOLoop.current().start()

