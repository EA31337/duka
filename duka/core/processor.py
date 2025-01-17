import struct
from datetime import timedelta, datetime
from lzma import LZMADecompressor, LZMAError, FORMAT_AUTO


def decompress_lzma(data):
    results = []
    len(data)
    while True:
        decomp = LZMADecompressor(FORMAT_AUTO, None, None)
        try:
            res = decomp.decompress(data)
        except LZMAError:
            if results:
                break  # Leftover data is not a valid LZMA/XZ stream; ignore it.
            else:
                raise  # Error on the first iteration; bail out.
        results.append(res)
        data = decomp.unused_data
        if not data:
            break
        if not decomp.eof:
            raise LZMAError("Compressed data ended before the end-of-stream marker was reached")
    return b"".join(results)


def tokenize(buffer):
    token_size = 20
    size = int(len(buffer) / token_size)
    tokens = []
    for i in range(0, size):
        tokens.append(struct.unpack('!IIIff', buffer[i * token_size: (i + 1) * token_size]))
    return tokens


def add_hour(ticks):
    if len(ticks) is 0:
        return ticks

    hour_delta = 0

    if ticks[0][0].weekday() == 6:
        hour_delta = 22

    for index, v in enumerate(ticks):
        if index != 0:
            if ticks[index - 1][0].minute > ticks[index][0].minute:
                hour_delta = ticks[index - 1][0].hour + 1
            else:
                hour_delta = ticks[index - 1][0].hour
        ticks[index] = (v[0] + timedelta(hours=hour_delta), v[1], v[2], v[3], v[4])

    return ticks


def normalize(day, ticks):
    def norm(time, ask, bid, volume_ask, volume_bid):
        date = datetime(day.year, day.month, day.day) + timedelta(milliseconds=time)
        return date, ask / 100000, bid / 100000, round(volume_ask * 1000000), round(volume_bid * 1000000)

    return add_hour(list(map(lambda x: norm(*x), ticks)))


def decompress(day, compressed_buffer):
    if compressed_buffer.nbytes == 0:
        return compressed_buffer
    return normalize(day, tokenize(decompress_lzma(compressed_buffer)))
