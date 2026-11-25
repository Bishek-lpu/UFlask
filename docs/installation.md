# Installation

uFlask has **zero external dependencies**. The package itself is the only thing you need.

---

## On Raspberry Pi Pico W (MicroPython)

Upload the `uflask/` package directory to your Pico W. Only the `uflask/` subfolder is needed — not the whole project.

### Option 1 — Thonny IDE (Beginner-friendly)

1. Open **Thonny** → connect your Pico W via USB
2. In the file manager, navigate to your project folder
3. Select the `uflask/` directory → right-click → **Upload to /**
4. Create your `main.py` on the Pico W and start coding

### Option 2 — mpremote (Command line)

```bash
# Install mpremote
pip install mpremote

# Upload the package
mpremote connect /dev/ttyUSB0 cp -r uflask/ :uflask/

# Upload your app
mpremote connect /dev/ttyUSB0 cp main.py :main.py

# Run it
mpremote connect /dev/ttyUSB0 run main.py
```

> **Windows users:** replace `/dev/ttyUSB0` with your COM port, e.g. `COM3`

### Option 3 — rshell

```bash
pip install rshell
rshell -p /dev/ttyUSB0

# Inside rshell:
cp -r uflask/ /pyboard/
cp main.py /pyboard/
repl   # then press Ctrl+D to soft-reset
```

### Option 4 — ampy

```bash
pip install adafruit-ampy
ampy --port /dev/ttyUSB0 mkdir uflask
ampy --port /dev/ttyUSB0 put uflask/__init__.py uflask/__init__.py
# repeat for each file…
```

---

## On CPython (Development / Testing)

uFlask's `_compat.py` shim makes the library work on regular Python 3.9+ too, so you can develop and test locally without hardware.

### Install from source

```bash
git clone https://github.com/bishek/uflask
cd uflask
pip install -e ".[dev]"
```

### Install via pip (once published)

```bash
pip install uflask

# With development tools:
pip install uflask[dev]

# With docs tools:
pip install uflask[docs]
```

---

## MicroPython Firmware

uFlask requires **MicroPython 1.20 or newer** on the Pico W.

| Feature used | Min version |
|---|---|
| `uasyncio` | 1.19 |
| `asyncio.wait_for` | 1.20 |
| `network.WLAN` | 1.19 |
| `ujson` | any |

Download the latest firmware from [micropython.org/download/RPI_PICO_W](https://micropython.org/download/RPI_PICO_W/) and flash it using the **Thonny** firmware installer or:

```bash
# Hold BOOTSEL → plug in USB → release BOOTSEL
# Pico appears as a USB drive
cp RPI_PICO_W-*.uf2 /Volumes/RPI-RP2/
```

---

## Verifying the Installation

After uploading, open a MicroPython REPL and run:

```python
import uflask
print(uflask.__version__)   # → 1.0.0
```

If you see the version number, uFlask is installed correctly.
