import asyncio
import numpy as np
import types

RESPEAKER_RATE = 16000
RESPEAKER_WIDTH = 2
chunk = 1024


class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.frames = np.array(0, dtype=np.int16)
        self.chunks = 0
        self.callbacks = list()
        self.first_frame_callback = None

    def connection_made(self, transport):
        self.transport = transport
        print("Audio Server Connected")

    def send_data(self, chunks):
        self.chunks = chunks
        self.frames = np.empty(1, dtype=np.int16)
        message = "Send " + str(chunks)
        self.transport.write(message.encode())
        print('Data sent: {!r}'.format(message))

    def data_received(self, data):
        a = np.fromstring(data, dtype=np.int16)

        if(len(self.frames) < chunk):
            if(self.first_frame_callback is not None):
                self.first_frame_callback()

        self.frames = np.concatenate((self.frames, a), axis=0)
        if(len(self.frames) > self.chunks * 8 * chunk):
            self.transaction_end()

    def transaction_end(self):
        self.frames = self.frames[1:]
        print("Samples = " + str(len(self.frames)))

        for callback in self.callbacks:
            callback()

    def register_callback(self, callback: types.FunctionType):
        self.callbacks.append(callback)

    def register_firstframecallback(self, callback: types.FunctionType):
        self.first_frame_callback = callback

    def connection_lost(self, exc):
        print('The server closed the connection')

        self.on_con_lost.set_result(True)
