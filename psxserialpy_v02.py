#!/usr/bin/env python3
# PSX Serialpy v0.2 by RetroGameplayer.com
# Licensed under the GNU General Public License v3
#
# Uploads a PSX-EXE to a PlayStation running PSXSERIAL (psxdev.net) or the
# Hitmen serial loader it is based on, over a 3-wire USB-serial cable.
#
# Wire protocol (taken from the Hitmen receiver source and the PSXSERIAL PC
# client; the console never sends ACKs during the transfer):
#   1. PC sends 'c' (0x63) as a sync byte. PSXSERIAL answers with one byte.
#   2. PC sends the full 2048-byte PSX-EXE header.
#   3. PC sends three 4-byte little-endian values copied from that header:
#        offset 16 = initial program counter (where execution starts)
#        offset 24 = load address in RAM
#        offset 28 = size of the program code (everything after the header)
#   4. PC sends the program code. The console copies exactly "size" bytes to
#      the load address and then jumps to the program counter.
#   5. PC sends 2048 bytes of 0xFF filler, as the official client does.
#
# Usage:
#   python psxserialpy_v02.py                      (asks for file and port)
#   python psxserialpy_v02.py GAME.EXE COM3
#   python psxserialpy_v02.py GAME.EXE /dev/ttyUSB0
#   python psxserialpy_v02.py --list               (show serial ports)

import argparse
import binascii
import os
import struct
import sys
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("pyserial is not installed. Install it with:  pip install pyserial")
    sys.exit(1)

BAUD_RATE = 115200
HEADER_SIZE = 2048
BLOCK_SIZE = 2048
SYNC_BYTE = b'\x63'          # 'c' (decimal 99)
EXE_MAGIC = b'PS-X EXE'
RAM_START = 0x80000000
RAM_END = 0x80200000         # 2 MB of main RAM on a retail console


class TransferError(Exception):
    pass


def parse_psx_exe(data):
    """Check that data is a PSX-EXE and return (pc, load_addr, code_size)."""
    if len(data) < HEADER_SIZE:
        raise TransferError(f"File is only {len(data)} bytes; a PSX-EXE has a {HEADER_SIZE}-byte header.")
    if data[0:8] != EXE_MAGIC:
        raise TransferError(
            "File does not start with 'PS-X EXE'. PSXSERIAL can only run PSX-EXE files "
            "(raw binaries, ELF and CPE files must be converted first).")

    pc, = struct.unpack_from('<I', data, 16)
    load_addr, code_size = struct.unpack_from('<II', data, 24)
    body_len = len(data) - HEADER_SIZE

    if code_size == 0:
        raise TransferError("Header says the program size is 0 bytes.")
    if code_size > body_len:
        raise TransferError(
            f"Header says the program is {code_size} bytes but the file only has "
            f"{body_len} bytes after the header. The file is probably truncated.")
    if not (RAM_START <= load_addr and load_addr + code_size <= RAM_END):
        print(f"WARNING: load range 0x{load_addr:08X}-0x{load_addr + code_size:08X} "
              "is outside 2 MB retail RAM. Fine on an 8 MB dev unit, will crash on a retail console.")
    if load_addr < 0x80010000:
        print(f"WARNING: load address 0x{load_addr:08X} overlaps the BIOS/kernel area "
              "(below 0x80010000). The upload will probably crash the console.")
    if len(data) % BLOCK_SIZE:
        print(f"Note: file size is not a multiple of {BLOCK_SIZE} bytes. "
              "The official PSXSERIAL client rejects such files, but this tool sends them anyway.")

    return pc, load_addr, code_size


def sync_with_console(ser, wait_for_reply, attempts):
    """Send the sync byte and, for PSXSERIAL, wait for the console to answer."""
    ser.reset_input_buffer()

    if not wait_for_reply:
        # Hitmen-style receivers do not answer. Send 'c' exactly once: a second
        # 'c' would be read as the first byte of the header and break the upload.
        ser.write(SYNC_BYTE)
        ser.flush()
        time.sleep(0.5)
        print("Sync byte sent (not waiting for a reply).")
        return

    for attempt in range(1, attempts + 1):
        ser.write(SYNC_BYTE)
        ser.flush()
        reply = ser.read(1)          # waits up to the port timeout (2 s)
        if reply:
            time.sleep(0.2)          # let any extra reply bytes arrive, then discard them
            ser.reset_input_buffer()
            print(f"Console answered (0x{reply[0]:02X}). Starting upload.")
            return
        print(f"  No answer from console (attempt {attempt}/{attempts})...")

    raise TransferError(
        "The console never answered the sync byte.\n"
        "  - Is the PlayStation showing 'STANDING BY...'?\n"
        "  - Are TX and RX crossed (PC TX -> PSX RX, PC RX -> PSX TX) and GND connected?\n"
        "  - Is the CH340 module set to 3.3V, and is this the right port?\n"
        "  - If your loader never sends a reply (e.g. older Hitmen serial loader),\n"
        "    reset the console and run again with --no-wait.")


def transfer_exe(file_path, port, wait_for_reply=True, attempts=10):
    with open(file_path, 'rb') as f:
        data = f.read()

    pc, load_addr, code_size = parse_psx_exe(data)
    seconds = (HEADER_SIZE + 12 + code_size + BLOCK_SIZE) * 10 / BAUD_RATE
    print(f"File:          {os.path.basename(file_path)} ({len(data)} bytes)")
    print(f"Start address: 0x{pc:08X}")
    print(f"Load address:  0x{load_addr:08X}")
    print(f"Program size:  {code_size} bytes (about {seconds:.0f} s at {BAUD_RATE} baud)")
    print(f"CRC32:         {binascii.crc32(data) & 0xFFFFFFFF:08X} (for your records; the console does not check it)")
    print()

    # 8 data bits, no parity, 1 stop bit, no flow control: matches the PSX side.
    with serial.Serial(port, BAUD_RATE, bytesize=8, parity='N', stopbits=1,
                       timeout=2, write_timeout=10) as ser:
        try:
            ser.rts = True           # the official client does this; a 3-wire cable ignores it
            ser.dtr = True
        except (OSError, serial.SerialException):
            pass                     # some adapters/virtual ports do not support these lines
        time.sleep(0.5)              # some CH340 drivers need a moment after opening

        sync_with_console(ser, wait_for_reply, attempts)

        # Header, then the three values the receiver reads separately.
        # They are copied straight from the file, which already stores them
        # little-endian, exactly what the console expects.
        ser.write(data[0:HEADER_SIZE])
        ser.write(data[16:20])
        ser.write(data[24:28])
        ser.write(data[28:32])

        body = data[HEADER_SIZE:HEADER_SIZE + code_size]
        sent = 0
        for offset in range(0, len(body), BLOCK_SIZE):
            chunk = body[offset:offset + BLOCK_SIZE]
            ser.write(chunk)
            sent += len(chunk)
            pct = sent * 100 // len(body)
            print(f"\rSending: {sent}/{len(body)} bytes ({pct}%)", end='', flush=True)
        print()

        # Same 0xFF filler the official PSXSERIAL client sends at the end.
        ser.write(b'\xFF' * BLOCK_SIZE)
        ser.flush()                  # wait until the OS has handed everything to the adapter
        time.sleep(0.5)              # and give the adapter time to clock out its own buffer

    print("Upload finished. The console should now be running your program.")
    print("(There is no confirmation from the console; a black screen or freeze usually means "
          "a bad cable connection or a program that does not run from this address.)")


def list_ports():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found. Is the USB-serial adapter plugged in and its driver installed?")
        return []
    print("Serial ports found:")
    for p in ports:
        note = "  <- looks like a CH340" if (p.vid == 0x1A86) else ""
        print(f"  {p.device:15} {p.description}{note}")
    return ports


def ask_for_file():
    while True:
        path = input("Path to the PSX-EXE file: ").strip().strip('"').strip("'")
        if os.path.isfile(path):
            return path
        print("File not found. Tip: you can drag the file into this window to paste its path.")


def ask_for_port():
    ports = list_ports()
    default = ports[0].device if len(ports) == 1 else None
    while True:
        prompt = "Serial port" + (f" [{default}]" if default else " (e.g. COM3 or /dev/ttyUSB0)") + ": "
        port = input(prompt).strip() or default
        if port:
            return port


def main():
    parser = argparse.ArgumentParser(description="Upload a PSX-EXE to a PlayStation running PSXSERIAL.")
    parser.add_argument('file', nargs='?', help="PSX-EXE file to upload")
    parser.add_argument('port', nargs='?', help="serial port, e.g. COM3 or /dev/ttyUSB0")
    parser.add_argument('--list', action='store_true', help="list serial ports and exit")
    parser.add_argument('--no-wait', action='store_true',
                        help="send the sync byte once and do not wait for a reply "
                             "(for loaders that never answer)")
    args = parser.parse_args()

    print("PSX Serialpy v0.2 - PSX-EXE uploader")
    print("====================================")

    if args.list:
        list_ports()
        return 0

    file_path = args.file or ask_for_file()
    port = args.port or ask_for_port()
    print()

    try:
        transfer_exe(file_path, port, wait_for_reply=not args.no_wait)
    except TransferError as e:
        print(f"\nERROR: {e}")
        return 1
    except serial.SerialException as e:
        print(f"\nSerial port error: {e}")
        print("Check the port name and make sure no other program (e.g. a terminal or the "
              "PSXSERIAL GUI) has the port open.")
        return 1
    except OSError as e:
        print(f"\nFile error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nCancelled. Reset the console before trying again.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
