import asyncio
import numpy as np
import DUET_AOA_HS as AOA_DUET
import functions as lib_HS
import audioClient
import motorClient


class Mainthread():
    """docstring for ."""

    def __init__(self, audioprotocol, motorprotocol=None):
        self.audioprotocol = audioprotocol
        self.motorprotocol = motorprotocol

    def getAudio(self):
        self.audioprotocol.send_data(64)

    def rotate(self):
        self.motorprotocol.send_data('o3000')

    def calc_AoA(self):
        mic1 = self.audioprotocol.frames[0::8].astype(np.float32)
        mic4 = self.audioprotocol.frames[3::8].astype(np.float32)
        X = np.zeros((2, mic1.shape[0]), dtype=np.float32)
        X[0, :] = mic1
        X[1, :] = mic4

        # Apply DUET after rotation
        fs_MIC = 16000
        d = 0.1  # 10 cm
        vp = 343
        N_fft = 1024    # L_frame : Lengt of frame
        N_hop = int(N_fft*0.25)  # Frame_shift

        ## apply lowpass filter
        fmax = 3e3
        for i in range(2):
            X[i, :] = lib_HS.butter_lowpass_filter(X[i, :], fmax, fs_MIC)

        p, q = 1, 0  # speech case
        peakdelta = AOA_DUET.DUET(
            X, fs_MIC, N_fft, N_hop, p, q, 0.5, 0.3, 0, 0)
        AoA_D = np.arccos(-1*(vp/d)
                          * lib_HS.val_clip(peakdelta/fs_MIC, d, vp))*180/np.pi
        print('AoA_est = ', AoA_D)
        #self.rotate()


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    message = 'Send 32'

    audiotransport, audioprotocol = await loop.create_connection(
        lambda: audioClient.EchoClientProtocol(message, on_con_lost),
        '172.16.177.158', 8888)
    mainthread = Mainthread(audioprotocol)

    """motortransport, motorprotocol = await loop.create_connection(
        lambda: motorClient.EchoClientProtocol(message, on_con_lost),
        '172.16.177.158', 8889)
    mainthread = Mainthread(audioprotocol, motorprotocol)"""

    # Wait until the protocol signals that the connection
    # is lost and close the transport.
    audioprotocol.register_callback(mainthread.calc_AoA)

    try:
        mainthread.getAudio()
        await on_con_lost
    finally:
        audiotransport.close()

asyncio.run(main())
