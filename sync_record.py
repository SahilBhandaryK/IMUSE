import audioClient
import audioFile
import asyncio
import wave


class Mainthread():

    def __init__(self, audioprotocol, audiofile):
        self.audioprotocol = audioprotocol
        self.audiofile = audiofile

    def getAudio(self):
        self.audioprotocol.send_data(170)

    def play(self):
        self.audiofile.startplayback()

    def complete_callback(self):
        audio = []
        audio.append(self.audioprotocol.frames[0::8].tostring())
        wf = wave.open("data/mic1.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(audioClient.RESPEAKER_RATE)
        wf.writeframes(b''.join(audio))
        wf.close()

        audio = []
        audio.append(self.audioprotocol.frames[3::8].tostring())
        wf = wave.open("data/mic4.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(audioClient.RESPEAKER_RATE)
        wf.writeframes(b''.join(audio))
        wf.close()


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    message = 'IROS'

    audiofile = audioFile.audioFile("TTS_dataset\\TTS_norm_")

    audiotransport, audioprotocol = await loop.create_connection(
        lambda: audioClient.EchoClientProtocol(message, on_con_lost),
        '172.16.177.158', 8888)

    mainthread = Mainthread(audioprotocol, audiofile)
    audioprotocol.register_firstframecallback(mainthread.play)
    audioprotocol.register_callback(mainthread.complete_callback)

    try:
        mainthread.getAudio()
        await on_con_lost
    finally:
        audiotransport.close()
        audiofile.close()

asyncio.run(main())
