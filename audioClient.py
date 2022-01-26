import asyncio
import numpy as np
import wave
import DUET_AOA_HS as AOA_DUET
import functions as lib_HS
import types

RESPEAKER_RATE = 16000
RESPEAKER_WIDTH = 2


class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.frames = np.array(0, dtype=np.int16)
        self.chunks = 0
        self.callbacks = list()

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
        self.frames = np.concatenate((self.frames, a), axis=0)
        if(len(self.frames) > self.chunks * 8 * 1024):
            self.transaction_end()

    def transaction_end(self):
        self.frames = self.frames[1:]
        print("Samples = " + str(len(self.frames)))

        for callback in self.callbacks:
            callback()

        audio = []
        audio.append(self.frames[0::8].tostring())
        wf = wave.open("data/mic1.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RESPEAKER_RATE)
        wf.writeframes(b''.join(audio))
        wf.close()

    def register_callback(self, callback: types.FunctionType):
        self.callbacks.append(callback)

    def connection_lost(self, exc):
        print('The server closed the connection')

        self.transaction_end()

        self.on_con_lost.set_result(True)
