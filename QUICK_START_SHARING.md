# Quick Start: Sharing Your Flashcard App

## 🚀 Fastest Way: Local Network (Same WiFi)

**Perfect for:** Sharing with friends/family at home, school, or office

### Steps:

1. **Find your IP address:**
   - Windows: Open Command Prompt → type `ipconfig` → look for "IPv4 Address"
   - Example: `192.168.1.100`

2. **Start the server:**
   ```bash
   run_flashcard.bat
   ```
   Or:
   ```bash
   py flashcard_app.py
   ```

3. **Share this URL with others:**
   ```
   http://YOUR_IP_ADDRESS:8001
   ```
   Example: `http://192.168.1.100:8001`

4. **Make sure:**
   - ✅ Everyone is on the same WiFi network
   - ✅ Windows Firewall allows port 8001 (or 8002)

**That's it!** Others can now open the URL in their browser and use the app.

---

## 🌐 For Public Access (Anyone, Anywhere)

**Recommended:** Deploy to Render.com (Free!)

### Quick Deploy Steps:

1. **Create GitHub account** (if you don't have one): github.com

2. **Create a new repository:**
   - Go to github.com/new
   - Name it: `chinese-flashcard-app`
   - Make it Public
   - Click "Create repository"

3. **Upload your files:**
   - Upload these files to GitHub:
     - `flashcard_app.py`
     - `templates/flashcard.html`
     - `requirements.txt`
     - `Procfile` (already created)
     - `runtime.txt` (already created)
     - `Chinese_words_list.xlsx` (or instructions to upload)

4. **Deploy on Render:**
   - Go to [render.com](https://render.com)
   - Sign up (free)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Click "Create Web Service"
   - Wait 5-10 minutes
   - **Done!** Your app is live at: `https://your-app-name.onrender.com`

**Share this URL with anyone, anywhere!**

---

## 📦 Share Files for Local Installation

**Perfect for:** Offline use or when others want to run it themselves

1. **Create a zip file** with:
   - `flashcard_app.py`
   - `templates/` folder
   - `requirements.txt`
   - `Chinese_words_list.xlsx`
   - `run_flashcard.bat`

2. **Share via:**
   - Email attachment
   - Google Drive / Dropbox
   - USB drive

3. **Tell them to:**
   - Install Python 3.7+
   - Run: `pip install -r requirements.txt`
   - Run: `python flashcard_app.py`
   - Open: `http://localhost:8001`

---

## 🆘 Troubleshooting

**Can't connect?**
- Check Windows Firewall
- Verify same WiFi network
- Try port 8002 instead

**Need more help?**
- See full guide: `FLASHCARD_DEPLOYMENT.md`

