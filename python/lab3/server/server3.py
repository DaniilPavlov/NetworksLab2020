import os
import enum
import socket
import struct
import time


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
        self.client_port = 0
        self.file_path = ''
        self.client_address = None
        self.file_block_count = 0

        self.fail = False
        self.sent_last = False
        self.ignore_current_packet = False  # игнорируем пакет если у него другой порт
        self.tftp_mode = 'octet'  # default mode
        self.request_mode = None  # 'RRQ' или 'WRQ'
        self.fileBytes = []
        self.reached_end = False
        self.packet_buffer = []
        self.err = 0

    def process_udp_packet(self, packetData, packetSource):
        """
        packet data - данные в bytearray
        packet source - информация об адресе отправителя
        """
        print(f"Received packet from {packetSource}")
        print('packet data:', packetData)
        self.ignore_current_packet = False
        if self.ignore_current_packet:  # не добавляем текущий пакет в буффер
            return
        outputPacket = self.handle_received_packet(packetData)
        if outputPacket == []:  # последний пакет в файле ACK
            return
        self.packet_buffer.append(outputPacket)

    def generate_error_packet(self, error_code, error_message=''):
        # пакет ошибки в формате 2 байт, opcode 5. 2 байта под error code, error_msg
        error_packet = struct.pack('!HH', TftpProtocol.TftpPacketType.ERROR.value, error_code)
        error_packet += struct.pack('!{}sB'.format(len(error_message)), error_message.encode(), 0)

        return error_packet

    def handle_received_packet(self, inputPacket):
        """
        создаем пакет который будет далее занесен в буфер
        """
        opcode = struct.unpack('!H', inputPacket[0:2])[0]
        packetTypes = {1: 'RRQ', 2: 'WRQ', 3: 'DATA', 4: 'ACK', 5: 'ERROR'}
        try:
            packetType = TftpProtocol.TftpPacketType(opcode)
        except ValueError:  # несуществующий opcode
            self.reached_end = True
            err_msg = 'Illegal TFTP Opcode'
            print(err_msg)
            # возвращаем пакет с opcode = 5, error code = 4, сообщением ошибки
            return self.generate_error_packet(error_code=4, error_message=err_msg)

        if packetType == TftpProtocol.TftpPacketType.RRQ or packetType == TftpProtocol.TftpPacketType.WRQ:
            self.fileBytes = []
            self.request_mode = packetTypes[opcode]
            separatorId = 2 + inputPacket[2:].find(0)
            # получаем id конца поля имени файла
            # + 2 поскольку индекс, возвращаемый поиском, относится к подсписку, начальный индекс 2:
            filenameBytes = inputPacket[2:separatorId]

            fmt_str = '!{}s'.format(len(filenameBytes))
            # распаковываем байты и получаем путь к файлу из кортежа
            self.file_path = struct.unpack(fmt_str, filenameBytes)[0]
            # если доступ к файлу сервера запрещен
            if str(self.file_path, encoding='ascii') == os.path.basename(__file__):
                self.reached_end = True
                self.fail = True
                return self.generate_error_packet(error_code=0, error_message="Access Forbidden")

            self.tftp = str(inputPacket[separatorId + 1:-1], 'ascii').lower()

        if packetType == TftpProtocol.TftpPacketType.ACK and self.sent_last:  # последний пакет acknowledged

            self.sent_last = False
            # конец передачи
            self.reached_end = True
            return []

        if packetType == TftpProtocol.TftpPacketType.RRQ:  # RRQ
            err = self.read_file()
            # проверяем существует ли файл на сервере
            if err:
                # error code =1, opcode for error = 5
                # формируем пакет ошибки
                error_code = 1
                self.err = 1
                err_msg = 'File not found.'
                self.reached_end = True
                print(err_msg)
                return self.generate_error_packet(error_code=error_code, error_message=err_msg)

        if packetType == TftpProtocol.TftpPacketType.WRQ:  # WRQ
            # если файл не существует возвращаем ACK с блоком под номером 0
            if os.path.exists(self.file_path):  # проверяем существует ли файл на сервере
                error_code = 6
                self.err = 6
                err_msg = 'File already exists'
                self.reached_end = True
                print(err_msg)
                return self.generate_error_packet(error_code=error_code, error_message=err_msg)

            outputPacket = struct.pack('!HH', TftpProtocol.TftpPacketType.ACK.value, 0)
        elif packetType == TftpProtocol.TftpPacketType.DATA:  # Data
            block_num = struct.unpack('!H', inputPacket[2:4])[0]

            if len(inputPacket) > 4:  # последней пакет может иметь 0 байт
                len_data = len(inputPacket[4:])
                if len_data != 512:
                    self.sent_last = True
                    self.reached_end = True
                if self.tftp_mode == 'octet':
                    fmt_str = '!{}B'.format(len_data)
                else:  # netascii
                    fmt_str = '!{}s'.format(len_data)
                unpacked_data_bytes = struct.unpack(fmt_str, inputPacket[4:])
                # вставляем байты полученного блока в файл чтобы далее записать
                self.fileBytes.extend(unpacked_data_bytes)
            else:  # конец передачи
                self.reached_end = True

            outputPacket = struct.pack('!HH', TftpProtocol.TftpPacketType.ACK.value, block_num)

        elif packetType == TftpProtocol.TftpPacketType.ERROR:
            self.reached_end = True
            err_msg = 'Not defined :' + str(inputPacket[4:-1], encoding='ascii')
            print(err_msg)
            # возвращаем ERROR пакет с opcode = 5, error code = 0, error message
            return self.generate_error_packet(error_code=0, error_message=err_msg)

        if packetType == TftpProtocol.TftpPacketType.ACK or packetType == TftpProtocol.TftpPacketType.RRQ:
            # ответить на RRQ с первым блоком и ACK с другими блоками
            if packetType == TftpProtocol.TftpPacketType.RRQ:
                block_num = 1
            else:
                block_num = struct.unpack('!H', inputPacket[2:4])[0] + 1
            # получаем блок данных после ack пакета, или первый если это rrq
            data_blocks = self.get_next_data_block(block_num)

            len_data = len(data_blocks)
            if len_data > 0:  # проверяем есть ли еще блоки для отправки
                format_char = ''
                if self.tftp_mode == 'octet':
                    format_char = '!B'
                elif self.tftp_mode == 'netascii':
                    format_char = '!s'
                # блоки данных конвертируются в требующийся тип
                outputPacket = struct.pack('!HH', TftpProtocol.TftpPacketType.DATA.value, block_num)
                for byte in list(data_blocks):
                    outputPacket += struct.pack(format_char, byte)
            else:  # если размер файла кратен 512, то последний пакет не будет иметь данных
                outputPacket = struct.pack('!HH', TftpProtocol.TftpPacketType.DATA.value, block_num)
        return outputPacket

    def get_next_data_block(self, block_num):
        # индексируем блоки
        startId = (block_num - 1) * 512
        endId = startId + 512

        if endId > (self.file_block_count):  # если размер последнего блока меньше 512
            # конец передачи
            self.sent_last = True
            return self.fileBytes[startId:]
        elif endId == self.file_block_count:  # отправляем пустой блок в конце передачи, если размер кратен 512
            self.sent_last = True
            return []
        return self.fileBytes[startId: endId]

    def get_next_packet(self):
        return self.packet_buffer.pop(0)

    def has_packets_to_send(self):
        return len(self.packet_buffer) != 0

    def save_file(self):
        if not self.fail:
            with open(self.file_path, 'wb') as uploadFile:
                uploadFile.write(bytes(self.fileBytes))

    def read_file(self):
        try:
            with open(self.file_path, 'rb') as f:
                self.fileBytes = list(f.read())
                self.file_block_count = len(self.fileBytes)
            return False
        except FileNotFoundError:  # если файл не существует
            return True

    def set_client_address(self, client_address):
        self.client_address = client_address
        self.client_port = client_address[1]

    def get_file_path(self):
        return str(self.file_path, encoding='ascii')

    def get_file_size(self):
        return len(self.fileBytes)


def setup_sockets(address):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSocket.bind(address)
    return serverSocket


def main():
    server_address = ("127.0.0.1", 69)
    server_socket = setup_sockets(server_address)

    print('Server started at', server_address)
    while True:
        print('Waiting for connection...')
        protocol = TftpProtocol()
        # получаем пакет, содержащий строку запроса (RRQ или WRQ)
        request_packet, clientAddress = server_socket.recvfrom(2048)
        # путь к файлу может быть самым большим блоком в пакете, поэтому размер пакета не может превышать 2048 байт.
        protocol.set_client_address(clientAddress)
        print('Connected to ', clientAddress)
        protocol.process_udp_packet(request_packet, clientAddress)
        request_mode = protocol.request_mode

        if request_mode == 'RRQ' or request_mode == 'WRQ':

            while protocol.has_packets_to_send():
                nextPacket = protocol.get_next_packet()
                server_socket.sendto(nextPacket, clientAddress)

                if not protocol.reached_end:  # получаем новый пакет, если не достигли конца передачи
                    received_packet, received_client = server_socket.recvfrom(2048)
                    protocol.process_udp_packet(received_packet, received_client)
                else:
                    print('TRANSMISSION ENDED')
                while protocol.ignore_current_packet:
                    # если получен случайный пакет, игнорировать его получить другой пакет
                    received_packet, received_client = server_socket.recvfrom(2048)
                    protocol.process_udp_packet(received_packet, received_client)
            print('file path on server:', protocol.get_file_path())
            print(protocol.get_file_size(), ' bytes transmitted ')

            if request_mode == 'WRQ' and protocol.err != 6 and protocol.err != 1:
                # сохраняем файл после получения
                protocol.save_file()
        else:
            print('ERROR!')
        time.sleep(1)


if __name__ == "__main__":
    main()
