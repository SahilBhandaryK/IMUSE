import pyaudio
import wave
import numpy as np
import threading


class audioFile:
    chunk = 1000
    chunks = 1200
    samples = chunk * chunks
    output_channels = 3

    def __init__(self, file, files=1):
        self.t = threading.Thread(target=self.playall)
        self.chunks = 1200
        self.samples = self.chunk * self.chunks

        """ Init audio stream """
        self.wf1 = wave.open(file + "1.wav", 'rb')
        self.wf2 = wave.open(file + "2.wav", 'rb')
        self.wf3 = wave.open(file + "3.wav", 'rb')
        self.p = pyaudio.PyAudio()
        print("Audio channels = " + str(self.wf1.getnchannels()))
        print("Frame rate = " + str(self.wf1.getframerate()))

        info = self.p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        print("Number of Devices = " + str(numdevices))
        for i in range(0, numdevices):
            print("Input Device id ", i, " - ",
                  self.p.get_device_info_by_host_api_device_index(0, i).
                  get('name'), ", channels = ",
                  self.p.get_device_info_by_host_api_device_index(0, i).
                  get('maxInputChannels'))

        samples_data = samples_c = np.zeros(
            self.samples * 3, dtype=np.int16)

        samples_l = np.fromstring(
            self.wf1.readframes(self.samples), dtype=np.int16)
        if(files > 1):
            samples_r = np.fromstring(
                self.wf2.readframes(self.samples), dtype=np.int16)
        else:
            samples_r = np.zeros(samples_l.shape, dtype=(np.int16))
        if(files > 2):
            samples_c = np.fromstring(
                self.wf3.readframes(self.samples), dtype=np.int16)
        else:
            samples_c = np.zeros(samples_l.shape, dtype=(np.int16))

        samples_data[0::3] = samples_l
        samples_data[1::3] = samples_r
        samples_data[2::3] = samples_c

        self.data = np.chararray.tostring(samples_data.astype(np.int16))

    def startplayback(self):
        self.t.start()

    def playall(self):
        self.stream = self.p.open(
            format=self.p.get_format_from_width(self.wf1.getsampwidth()),
            channels=self.output_channels,
            rate=self.wf1.getframerate(),
            output=True,
            output_device_index=6
        )
        self.stream.write(self.data)

    def play(self):
        self.stream = self.p.open(
            format=self.p.get_format_from_width(self.wf1.getsampwidth()),
            channels=1,
            rate=self.wf1.getframerate(),
            output=True,
            output_device_index=6
        )
        """ Play entire file """
        data = self.wf1.readframes(self.chunk)
        print("Length of data = " + str(len(data)))
        print("Type of data = " + str(type(data)))
        while data != '':
            self.stream.write(data)
            data = self.wf1.readframes(self.chunk)

    def close(self):
        """ Graceful shutdown """
        self.stream.close()
        self.p.terminate()
        self.wf1.close()
        self.wf2.close()
        self.wf3.close()


if __name__ == "__main__":

    # Usage example for pyaudio
    a = audioFile("TTS_dataset\\TTS_norm_")
    a.startplayback()
    a.t.join()
    #a.play()
    a.close()
