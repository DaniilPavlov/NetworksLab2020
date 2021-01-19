import os
import enum
import socket
import struct


class TftpProtocol(object):
    """
    получаем udp пакет
    отсылаем пакет, который нужно записать в сокет
    Вход и выход - ТОЛЬКО байтовые массивы.
    Выходные пакеты сохраняются в буфере  в этом классе,
    функция get_next_output_packet возвращает следующий пакет, который нужно отправить.
    Этот класс также отвечает за чтение/запись файлов на диск. Несоблюдение этих требований приведет к ошибке.
    """

    class TftpPacketType(enum.Enum):
        RRQ = 1
        WRQ = 2
        DATA = 3
        ACK = 4
        ERROR = 5

    def __init__(self):
        self.packetBuffer = []  # буфер для хранения пакетов
        self.blockNumber = 0  # номер блока

        self.isFinished = False  # старт/стоп протокола
        self.isReceiving = True  # старт/стоп получения пакетов
        self.isMismatch = False  # отправляем пакет еще раз в случае несовпадения

        self.errorCode = 0
        self.errorMessage = ""

    def process_udp_packet(self, packetData, packetSource):
        """
        packet data - данные в bytearray
        packet source - информация об адресе отправителя
        """
        print(f"Received packet from {packetSource}")
        receivedOpcode = self.parse_udp_packet(packetData)
        outputPacket = self.handle_received_opcode(receivedOpcode)
        self.packetBuffer.append(outputPacket)

    def parse_udp_packet(self, packetBytes):
        """
        получаем информацию о типе пакета и вытаскиваем данные
        """
        opcode = struct.unpack('!H', packetBytes[:2])[0]

        if opcode == self.TftpPacketType.DATA.value:
            self.blockNumber = struct.unpack('!H', packetBytes[2:4])[0]
            self.accessed_file.write(packetBytes[4:])
            if len(packetBytes) < (512 + 4):
                self.accessed_file.close()
                self.isFinished = True
                self.isReceiving = False

        elif opcode == self.TftpPacketType.ACK.value:
            block_number = struct.unpack('!H', packetBytes[2:4])[0]
            self.isMismatch = not (self.blockNumber == block_number)

        elif opcode == self.TftpPacketType.ERROR.value:
            _ = self.show_error(int(struct.unpack('!H', packetBytes[2:4])[0]))

        return opcode

    def handle_received_opcode(self, receivedOpcode):
        """
        создаем пакет который будет далее занесен в буфер
        """

        if receivedOpcode == self.TftpPacketType.ACK.value:
            data = self.accessed_file.read(512)
            # проверяем последний ли это пакет
            if len(data) < 512:
                self.isFinished = True

            # проверяем, есть ли несоответствие в пакете, чтобы запросить его снова
            if self.isMismatch:
                packet = struct.pack('!HH', self.TftpPacketType.DATA.value, self.blockNumber) + data

            # получаем следующий пакет
            else:
                self.blockNumber += 1
                packet = struct.pack('!HH', self.TftpPacketType.DATA.value, self.blockNumber) + data

        elif receivedOpcode == self.TftpPacketType.DATA.value:
            packet = struct.pack('!HH', self.TftpPacketType.ACK.value, self.blockNumber)

        # # при ошибке завершаем соединение
        # elif receivedOpcode == self.TftpPacketType.ERROR.value and self.errorCode != 6 and self.errorCode !=1:
        #     sys.exit()
        return packet

    def has_packets_to_send(self):
        return len(self.packetBuffer) != 0

    def get_next_packet(self):
        return self.packetBuffer.pop(0)

    def download_file(self, file_name):
        # перед отправкой запроса проверяем, существует ли уже файл
        exists = os.path.exists(file_name)
        if exists:
            return self.show_error(6)  # file already exists

        try:
            self.accessed_file = open(file_name, 'wb')
            mode = b'octet'
            opcode = self.TftpPacketType.RRQ.value
            file_name = file_name.encode('ascii')
            file = struct.pack('!H{}sB{}sB'.format(len(file_name), len(mode)), opcode, file_name,
                               0, mode, 0)
        except:  # если случилась ошибка доступа, отправляем соответствующее сообщение
            file = self.show_error(2)  # access violation

        return file

    def upload_file(self, file_name):
        try:
            self.accessed_file = open(file_name, 'rb')
            mode = b'octet'
            opcode = self.TftpPacketType.WRQ.value
            file_name = file_name.encode('ascii')
            file = struct.pack('!H{}sB{}sB'.format(len(file_name), len(mode)), opcode, file_name,
                               0, mode, 0)
        except:
            exists = os.path.exists(file_name)
            if not exists:  # если файл не существует
                file = self.show_error(1)  # file not found
            else:  # если случилась ошибка доступа, отправляем соответствующее сообщение
                file = self.show_error(2)  # access violation
        return file

    def show_error(self, errorCode):
        self.errorCode = errorCode
        self.isFinished = True
        self.isReceiving = False

        if errorCode == 0:
            self.errorMessage = b"Not defined, see error message (if any)"
        elif errorCode == 1:
            self.errorMessage = b"File not found"
        elif errorCode == 2:
            self.errorMessage = b"Access violation"
        elif errorCode == 3:
            self.errorMessage = b"Disk full or allocation exceeded"
        elif errorCode == 4:
            self.errorMessage = b"Illegal TFTP operation"
        elif errorCode == 5:
            self.errorMessage = b"Unknown transfer ID"
        elif errorCode == 6:
            self.errorMessage = b"File already exists"
        elif errorCode == 7:
            self.errorMessage = b"No such user"

        print("Error code:", self.errorCode, "-", self.errorMessage.decode('ascii'))

        packet = struct.pack('!HH{}sB'.format(len(self.errorMessage)), self.TftpPacketType.ERROR.value, self.errorCode,
                             self.errorMessage, 0)
        return packet


def setup_sockets(address):
    clientSocker = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverAddress = (address, 69)

    return clientSocker, serverAddress


def do_socket_logic(protocol, address, request_packet):
    socket, server = setup_sockets(address)

    if request_packet:
        socket.sendto(request_packet, server)
        if protocol.isReceiving:
            packet, rev_addr = socket.recvfrom((512 + 4))

    while not protocol.isFinished:
        protocol.process_udp_packet(packet, rev_addr)
        if protocol.has_packets_to_send():
            socket.sendto(protocol.get_next_packet(), rev_addr)
            if protocol.isReceiving:
                packet, rev_addr = socket.recvfrom((512 + 4))
    print('****FINISH****')


def parse_user_input(address, operation, file_name=None):
    protocol = TftpProtocol()

    if operation == "PUT":
        print(f"Uploading [{file_name}]...")
        requested_file = protocol.upload_file(file_name)

        do_socket_logic(protocol, address, requested_file)

    elif operation == "GET":
        print(f"Downloading [{file_name}]...")
        requested_file = protocol.download_file(file_name)
        do_socket_logic(protocol, address, requested_file)

    else:  # в случае некорректной tftp операции
        do_socket_logic(protocol, address, protocol.show_error(4))


def main():
    while True:
        try:
            (ip_address, operation, file_name) = input('Enter ip address, operation, filename: ').split(' ')
            parse_user_input(ip_address, operation, file_name)
        except Exception as e:
            print(f"[ERROR] ", e)
            print('*' * 50)


if __name__ == "__main__":
    main()
