from __future__ import annotations

import socket
import struct
from dataclasses import dataclass


class ModbusTransportError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModbusTcpTarget:
    host: str
    port: int
    unit_id: int
    timeout_ms: int = 1000


class ModbusTcpClient:
    """Cliente Modbus TCP mínimo e síncrono para FC03 e FC16."""

    def __init__(self, target: ModbusTcpTarget) -> None:
        if not target.host.strip():
            raise ValueError("host Modbus obrigatório")
        if not 1 <= target.port <= 65535:
            raise ValueError("porta Modbus inválida")
        if not 0 <= target.unit_id <= 247:
            raise ValueError("Unit ID Modbus inválido")
        if target.timeout_ms < 1:
            raise ValueError("timeout Modbus deve ser positivo")
        self.target = target
        self._transaction_id = 0

    def _exchange(self, function: int, payload: bytes) -> bytes:
        self._transaction_id = (self._transaction_id % 0xFFFF) + 1
        pdu = bytes([function]) + payload
        request = struct.pack(">HHHB", self._transaction_id, 0, len(pdu) + 1, self.target.unit_id) + pdu
        try:
            with socket.create_connection((self.target.host, self.target.port), timeout=self.target.timeout_ms / 1000) as connection:
                connection.settimeout(self.target.timeout_ms / 1000)
                connection.sendall(request)
                header = self._receive_exact(connection, 7)
                transaction_id, protocol_id, length, unit_id = struct.unpack(">HHHB", header)
                if transaction_id != self._transaction_id or protocol_id != 0 or unit_id != self.target.unit_id:
                    raise ModbusTransportError("resposta Modbus TCP não corresponde à requisição")
                if length < 2 or length > 254:
                    raise ModbusTransportError("comprimento MBAP inválido")
                response = self._receive_exact(connection, length - 1)
        except ModbusTransportError:
            raise
        except (OSError, TimeoutError) as exc:
            raise ModbusTransportError(f"falha de transporte Modbus TCP: {exc}") from exc
        if response[0] == (function | 0x80):
            code = response[1] if len(response) > 1 else -1
            raise ModbusTransportError(f"exceção Modbus {code}")
        if response[0] != function:
            raise ModbusTransportError("função inesperada na resposta Modbus")
        return response[1:]

    @staticmethod
    def _receive_exact(connection: socket.socket, size: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < size:
            chunk = connection.recv(size - len(chunks))
            if not chunk:
                raise ModbusTransportError("conexão encerrada durante a resposta Modbus")
            chunks.extend(chunk)
        return bytes(chunks)

    def read_holding_registers(self, address: int, count: int) -> list[int]:
        if not 0 <= address <= 0xFFFF or not 1 <= count <= 125 or address + count > 0x10000:
            raise ValueError("faixa de leitura Modbus inválida")
        response = self._exchange(3, struct.pack(">HH", address, count))
        expected_bytes = count * 2
        if len(response) != expected_bytes + 1 or response[0] != expected_bytes:
            raise ModbusTransportError("tamanho inválido na leitura Modbus")
        return list(struct.unpack(f">{count}H", response[1:]))

    def write_holding_registers(self, address: int, values: list[int]) -> None:
        if not 0 <= address <= 0xFFFF or not 1 <= len(values) <= 123 or address + len(values) > 0x10000:
            raise ValueError("faixa de escrita Modbus inválida")
        if any(not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFFFF for value in values):
            raise ValueError("valor de registrador Modbus inválido")
        packed = struct.pack(f">{len(values)}H", *values)
        response = self._exchange(16, struct.pack(">HHB", address, len(values), len(packed)) + packed)
        if response != struct.pack(">HH", address, len(values)):
            raise ModbusTransportError("confirmação inválida na escrita Modbus")
