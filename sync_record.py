import audioClient
import audioFile
import asyncio


class Mainthread():

    def __init__(self, audioprotocol, audiofile):
        self.audioprotocol = audioprotocol
        self.audiofile = audiofile

    def getAudio(self):
        self.audioprotocol.send_data(13)

    def play(self):
        self.audiofile.playall()


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    message = 'IROS'

    audiofile = audioFile("TTS_dataset\\TTS_norm_")

    audiotransport, audioprotocol = await loop.create_connection(
        lambda: audioClient.EchoClientProtocol(message, on_con_lost),
        '172.16.177.158', 8888)

    mainthread = Mainthread(audioprotocol, audiofile)
    audioprotocol.register_firstframecallback(mainthread.play)

    try:
        mainthread.getAudio()
        await on_con_lost
    finally:
        audiotransport.close()
        audiofile.close()

asyncio.run(main())
