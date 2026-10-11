# PSX-Serial-Py
A Python file transfer utility for PlayStation 1 (PSX/PS1) development. The script makes use of the pyserial library for uploading compiled binaries from a PC to the PlayStation console's RAM via a USB-to-Serial cable (the common and cheap CH340G type). The utility is compatible with PSXSerial by PSXdev.net. 

PSX Serial transfers binary data in 1024-byte chunks from the host PC to PSX console at 115200 baud and implements some basic error checking. This includes waiting for acknowledgments (ACK) after sending the file size and each data chunk with exceptions raised if the expected ~0x06~ byte is not received. A final acknowledgment confirms successful file transfer. The script also trys to catch and handle other common error types, including serial communication errors, file I/O errors, and general exceptions. A CRC32 calculation function is also provided to further verify data integrity.

WARNING: This program was a learning experiment and a work in progress; it is not production-ready. 

## License
This project is licensed under the GNU General Public License v3. Attribution should go to [RetroGameplayer.com](http://retrogameplayer.com)
