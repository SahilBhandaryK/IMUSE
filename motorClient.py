import asyncio


class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost

    def connection_made(self, transport):
        self.transport = transport
        print("Motor Server Connected")
        # self.transport.write(self.message.encode())
        # print('Data sent: {!r}'.format(self.message))

    def send_data(self, message):
        self.transport.write(message.encode())

    def data_received(self, data):
        print('Data received: {!r}'.format(data.decode()))

    def connection_lost(self, exc):
        print('The server closed the connection')
        self.on_con_lost.set_result(True)


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    message = 'c1000'

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
