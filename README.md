# PSX-Serial-Py
A Python file transfer utility for PlayStation 1 (PSX/PS1) development. The script makes use of the pyserial library for uploading compiled binaries from a PC to the PlayStation console's RAM via a USB-to-Serial cable (the common and cheap CH340G type). The utility is compatible with PSXSerial by PSXdev.net. 

PSX Serialpy lets you test homebrew on real PlayStation 1 hardware without burning a new CD-R for every build - valuable capability given the iteration involved in game development. Boot the PSXSERIAL loader once, then send each new build from your PC over a USB-to-serial cable. It goes straight into the console’s RAM and starts running. The script is written in Python using the pyserial library. It speaks the same protocol as the official PSXSERIAL PC client by Matt at PSXDEV.net, which is based on the Hitmen serial loader. It runs on Windows, MacOS and Linux. All you need is a DIY-able cable based on the inexpensive CH340G USB-serial module, available for a few dollars.

# How it works and what you need

    A PlayStation with a serial port on the back (SCPH-1000 to SCPH-750x).
    A way to boot a CD-R: a modchip or the swap method.
    A CH340G USB-serial module and a 3-wire cable built from the wiring diagram.
    A PC with Python 3.6 or newer.
    Your program as a PSX-EXE file.

## Step 1: Build the cable

    Follow the wiring diagram. Connect PC TX to PSX RX, PC RX to PSX TX, and GND to GND. TX and RX must cross over.
    If your CH340G board has a voltage jumper, set it to 3.3V. The PlayStation’s serial port is 3.3V, and 5V can damage it.

## Step 2: Prepare the console

    Burn the PSXSERIAL image to a CD-R.
    Boot it using your modchip or the swap method.
    You should see colored bars with the title and version number, then STANDING BY.... Leave the console on this screen.

## Step 3: Set up the PC (one time only)

    Install Python from python.org. On Windows, tick “Add Python to PATH” in the installer.
    Open a command prompt. On Windows, press the Windows key, type cmd and press Enter. On macOS or Linux, open Terminal.
    Install pyserial:

   pip install pyserial

    Plug in the USB-serial module. Windows 10 and 11 usually install the CH340 driver on their own. If no port appears in the next step, download the CH340 driver from the chip maker, WCH.

## Step 4: Find your serial port

    Go to the folder holding the script. Example:

   cd C:\psxdev\tools

    List the serial ports:

   python psxserialpy_v02.py --list

    Note the port marked “looks like a CH340”. It will be something like COM3 on Windows, /dev/ttyUSB0 on Linux, or /dev/cu.usbserial-xxxx on macOS.

## Step 5: Upload your program

### Option A, answer the prompts:

python psxserialpy_v02.py

When it asks for the file, you can drag the file into the window to paste its path.

### Option B, everything on one line:

python psxserialpy_v02.py C:\psxdev\mygame\MYGAME.EXE COM3

When it works, you’ll see “Console answered”, then a progress counter, then “Upload finished”, and your program starts on the PlayStation.


WARNING: This program was a learning experiment and a work in progress; it is not production-ready. 

## License
This project is licensed under the GNU General Public License v3. Attribution should go to [RetroGameplayer.com](http://retrogameplayer.com)
