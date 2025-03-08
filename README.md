# infoHUD

infoHUD is a **low-power ePaper display system** running on a **Raspberry Pi Zero** with a **Waveshare ePaper display** and **PiSugar UPS battery**. It displays rotating content such as news, stock updates, and images, while also supporting flash messages via MQTT, webhooks, and a Python API.

## 🚀 Features
- **Rotating Display Content**: Show news, stock updates, and images.
- **Flash Message Support**: Display urgent messages from Home Assistant, emails, or API triggers.
- **External Control**:
  - MQTT (Home Assistant)
  - Webhooks
  - Python API
- **OTA Updates**: Fetch and apply updates from GitHub before each refresh.
- **Power Efficiency**: Runs only when powered, shutting down at **5% battery**.

## 📁 Folder Structure
/opt/infoHUD/ ├── src/ # Python scripts for display logic ├── config/ # Configuration files (JSON/YAML) ├── assets/ # Images, fonts, icons ├── logs/ # Log files for debugging ├── lib/ # Libraries (e.g., Waveshare ePaper) └── README.md # Project documentation

shell
Copy
Edit

## 🔧 Setup
### 1️⃣ Install Dependencies
```bash
sudo apt update && sudo apt install -y python3 python3-pip
2️⃣ Install the Waveshare ePaper Library
bash
Copy
Edit
pip3 install waveshare-epd
3️⃣ Run a Test Script
bash
Copy
Edit
python3 src/test_display.py
🛠️ Roadmap
✅ Setup Raspberry Pi Zero & PiSugar UPS
✅ Install Waveshare ePaper drivers
⏳ Develop flash messaging system
⏳ Implement OTA updates
⏳ Integrate MQTT & webhook support
