# Video Chat App (Encrypted + Audio)

Video chat between 2 PCs with **encryption** and **audio**.

## Features
- ✅ Live video (encrypted)
- ✅ Text chat (encrypted)
- ✅ **Audio calls (encrypted)** - NEW!
- ✅ **AES encryption** - All data encrypted
- ✅ Same network only

## Install

```bash
pip install -r requirements.txt
sudo apt-get install python3-tk python3-dev portaudio19-dev  # Linux only
```

## How to Use

### Change Password (Optional but recommended)
Edit `server.py` and `gui_client.py`, change:
```python
PASSWORD = "secure123"  # Change this!
```
Both files must use the same password.

### Step 1: Run Server
```bash
python server.py
```
Shows: `Using password: secure123`

Get your IP:
- **Windows:** `ipconfig` → IPv4 Address
- **Mac/Linux:** `ifconfig` → inet

### Step 2: Run Client on Both PCs
```bash
python gui_client.py
```
Enter server IP when asked.

### Done!
- Video + Audio + Chat all encrypted
- Speak into microphone - other person hears it
- Type text messages
- Everything is encrypted 🔒

## How It Works

### Encryption (AES)
- Password → SHA256 hash → Encryption key
- All data encrypted before sending
- Can't be read by anyone without password

### Audio
- Captures from microphone in real-time
- Compressed and encrypted
- Plays through speakers

### Protocol
```
[1 byte type] [4 bytes size] [encrypted data]
```
Types:
- 0 = Video frame
- 1 = Text message
- 2 = Audio chunk

## Troubleshooting

**"Could not connect"** - Server not running or wrong IP

**No audio heard** - Check microphone is plugged in

**Slow video** - Normal on slower networks, reduce resolution in code

**"Invalid password"** - Server and client passwords don't match
