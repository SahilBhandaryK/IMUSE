import asyncio
import types


class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.position = 0
        self.run_flag = False
        self.count = 0
        self.completeCallback = None

    def connection_made(self, transport):
        self.transport = transport
        print("Motor Server Connected")
        # self.transport.write(self.message.encode())
        # print('Data sent: {!r}'.format(self.message))

    def send_data(self, message):
        self.transport.write(message.encode())

    def rotate(self, dtheta):
        count = int(dtheta * 3200 / 180.0)
        self.run_flag = True
        self.count = count
        self.send_data("o" + str(count))

    def data_received(self, data):
        message = data.decode()
        if(message[0] == 'p'):
            self.position = int(message[1:])
            if(self.run_flag and self.position == self.count):
                self.run_flag = False
                self.completeCallback()
        else:
            print('Data received: {!r}'.format(data.decode()))

    def register_completecallback(self, callback: types.FunctionType):
        self.completeCallback = callback

    def connection_lost(self, exc):
        print('The server closed the connection')
        self.on_con_lost.set_result(True)


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    message = 'pi'

    transport, protocol = await loop.create_connection(
        lambda: EchoClientProtocol(message, on_con_lost),
        '172.16.177.158', 8889)

    # Wait until the protocol signals that the connection
    # is lost and close the transport.

    try:
        await on_con_lost
    finally:
        transport.close()


# asyncio.run(main())
