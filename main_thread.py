import asyncio
import numpy as np
import DUET_AOA_HS as AOA_DUET
import functions as lib_HS
import audioClient
import motorClient
import time


class Mainthread():
    """docstring for ."""

    def __init__(self, audioprotocol, motorprotocol=None, dtheta_step=17, micmode=0):
        self.audioprotocol = audioprotocol
        self.motorprotocol = motorprotocol
        self.micmode = micmode
        self.AoA_D_save = []
        self.dtheta_step = dtheta_step
        self.count = 0
        self.final_pos_flag = False

    def reset(self):
        self.motorprotocol.reset()

    def getAudio(self):
        self.audioprotocol.send_data(64)

    def rotate(self, theta):
        self.motorprotocol.rotate(theta)

    def start_routine(self):
        self.motorprotocol.rotate(0)

    def calc_AoA(self):
        if(self.micmode == 0):
            mic1 = self.audioprotocol.frames[1::8].astype(np.float32)
            mic4 = self.audioprotocol.frames[2::8].astype(np.float32)
            d = 0.05
        else:
            mic1 = self.audioprotocol.frames[0::8].astype(np.float32)
            mic4 = self.audioprotocol.frames[3::8].astype(np.float32)
            d = 0.1

        X = np.zeros((2, mic1.shape[0]), dtype=np.float32)
        X[0, :] = mic1
        X[1, :] = mic4

        start = time.time()

        # Apply DUET after rotation
        fs_MIC = 16000
        vp = 343
        N_fft = 1024    # L_frame : Lengt of frame
        N_hop = int(N_fft*0.25)  # Frame_shift

        ## apply lowpass filter
        fmax = 2e3
        for i in range(2):
            X[i, :] = lib_HS.butter_lowpass_filter(X[i, :], fmax, fs_MIC)

        p, q = 1, 0  # speech case
        peakdelta = AOA_DUET.DUET(
            X, fs_MIC, N_fft, N_hop, p, q, 0.2, 0.3, 0, 1)
        AoA_D = np.arccos(-1*(vp/d)
                          * lib_HS.val_clip(peakdelta/fs_MIC, d, vp))*180/np.pi
        print('AoA_est = ', AoA_D)

        print("Time = " + str((time.time() - start) * 1000))

    def calc_AoA_full(self):
        if(self.micmode == 0):
            mic1 = self.audioprotocol.frames[1::8].astype(np.float32)
            mic4 = self.audioprotocol.frames[2::8].astype(np.float32)
            d = 0.05
        else:
            mic1 = self.audioprotocol.frames[0::8].astype(np.float32)
            mic4 = self.audioprotocol.frames[3::8].astype(np.float32)
            d = 0.1
        X = np.zeros((2, mic1.shape[0]), dtype=np.float32)
        X[0, :] = mic1
        X[1, :] = mic4

        # Apply DUET after rotation
        fs_MIC = 16000
        vp = 343
        N_fft = 1024    # L_frame : Lengt of frame
        N_hop = int(N_fft*0.25)  # Frame_shift

        ## apply lowpass filter
        fmax = 3e3
        for i in range(2):
            X[i, :] = lib_HS.butter_lowpass_filter(X[i, :], fmax, fs_MIC)

        p, q = 1, 0  # speech case
        peakdelta = AOA_DUET.DUET(
            X, fs_MIC, N_fft, N_hop, p, q, 0.1, 0.3, 0, 0, "graphs\\"+str(self.count)+"_")
        AoA_D = np.arccos(-1*(vp/d)
                          * lib_HS.val_clip(peakdelta/fs_MIC, d, vp))*180/np.pi
        print('Local AoA_est = ', AoA_D)

        curr_angle = self.motorprotocol.position * 360.0 / 3200.0
        AoA_cand_p = -curr_angle + AoA_D  # AoA_global x rot_ang
        AoA_cand_n = -curr_angle - AoA_D  # AoA_global x rot_ang
        AoA_cand = lib_HS.AoA_clip(np.concatenate((AoA_cand_p, AoA_cand_n)))
        self.AoA_D_save.append(AoA_cand)

        Angle_est, peak_prom = lib_HS.getAoA(self.AoA_D_save, self.count)

        if np.average(peak_prom) > 2.5:
            self.final_pos_flag = True
            print("Final angle = " + str(Angle_est))
            #if(Angle_est < 0):
            #    Angle_est = 360.0 + Angle_est
            #self.rotate(Angle_est)
        else:
            self.count += 1
            self.rotate(self.dtheta_step + curr_angle)

    def rotate_callback(self):
        if(self.final_pos_flag):
            print("Complete, final alignment")
            return
        else:
            if(self.count < 10):
                self.getAudio()
            else:
                print("Maximum attempts reached")
                return


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    motorized = 0

    on_con_lost = loop.create_future()
    message = 'IROS'

    if(motorized == 0):
        audiotransport, audioprotocol = await loop.create_connection(
            lambda: audioClient.EchoClientProtocol(message, on_con_lost),
            '172.16.177.158', 8888)
        mainthread = Mainthread(audioprotocol, micmode=0)
        audioprotocol.register_callback(mainthread.calc_AoA)
    else:
        motortransport, motorprotocol = await loop.create_connection(
            lambda: motorClient.EchoClientProtocol(message, on_con_lost),
            '172.16.177.158', 8889)
        audiotransport, audioprotocol = await loop.create_connection(
            lambda: audioClient.EchoClientProtocol(message, on_con_lost),
            '172.16.177.158', 8888)
        mainthread = Mainthread(audioprotocol, motorprotocol, micmode=0)
        motorprotocol.register_completecallback(mainthread.rotate_callback)
        motorprotocol.register_resetcallback(mainthread.getAudio)
        audioprotocol.register_callback(mainthread.calc_AoA_full)

    try:
        if(motorized == 0):
            mainthread.getAudio()
        else:
            mainthread.reset()
        await on_con_lost
    finally:
        audiotransport.close()

asyncio.run(main())
