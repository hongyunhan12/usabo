# Chinese Flashcard App - Deployment Guide

This guide explains how to share the Chinese Flashcard App with others so they can use it.

## 🚀 Deployment Options

### Option 1: Local Network Sharing (Easiest - Same WiFi)

Perfect for sharing with friends/family on the same network (home, office, school WiFi).

#### Steps:

1. **Find your computer's IP address:**
   - **Windows**: Open Command Prompt and type `ipconfig`
     - Look for "IPv4 Address" (e.g., `192.168.1.100`)
   - **Mac/Linux**: Open Terminal and type `ifconfig` or `ip addr`
     - Look for your WiFi adapter's IP address

2. **Start the server:**
   ```bash
   py flashcard_app.py
   ```
   Or use the batch file:
   ```bash
   run_flashcard.bat
   ```

3. **Share the URL:**
   - Your local URL: `http://localhost:8001`
   - **Share this URL with others**: `http://YOUR_IP_ADDRESS:8001`
   - Example: `http://192.168.1.100:8001`

4. **Make sure:**
   - Your computer and others are on the same WiFi network
   - Windows Firewall allows connections on port 8001 (or 8002)
   - The server is running

#### Windows Firewall Setup:
If others can't connect, you may need to allow the port:
```powershell
# Run PowerShell as Administrator
New-NetFirewallRule -DisplayName "Flashcard App" -Direction Inbound -LocalPort 8001,8002 -Protocol TCP -Action Allow
```

---

### Option 2: Cloud Deployment (Free Options)

Deploy to the cloud so anyone can access it from anywhere.

#### A. Render.com (Recommended - Free Tier Available)

1. **Create a GitHub repository:**
   - Create a new repo on GitHub
   - Upload your files:
     - `flashcard_app.py`
     - `templates/flashcard.html`
     - `requirements.txt`
     - `Chinese_words_list.xlsx` (or provide instructions to upload)

2. **Create `Procfile`** (for Render):
   ```
   web: uvicorn flashcard_app:app --host 0.0.0.0 --port $PORT
   ```

3. **Create `runtime.txt`** (specify Python version):
   ```
   python-3.11.0
   ```

4. **Deploy on Render:**
   - Go to [render.com](https://render.com)
   - Sign up/login
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - **Name**: chinese-flashcard-app
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn flashcard_app:app --host 0.0.0.0 --port $PORT`
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Your app will be live at: `https://your-app-name.onrender.com`

#### B. Railway.app (Free Tier Available)

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and deploy:**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Or use Railway Dashboard:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Connect GitHub repo or upload files
   - Railway auto-detects FastAPI and deploys

#### C. PythonAnywhere (Free Tier Available)

1. **Sign up** at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload files:**
   - Go to "Files" tab
   - Upload `flashcard_app.py`, `templates/`, and `Chinese_words_list.xlsx`

3. **Install dependencies:**
   - Go to "Tasks" tab
   - Create a new task: `pip3.10 install --user fastapi uvicorn pandas openpyxl jinja2`

4. **Create Web App:**
   - Go to "Web" tab
   - Click "Add a new web app"
   - Choose "Manual configuration" → Python 3.10
   - Edit WSGI file:
     ```python
     import sys
     path = '/home/YOUR_USERNAME/mysite'
     if path not in sys.path:
         sys.path.append(path)
     
     from flashcard_app import app
     application = app
     ```

5. **Reload web app** - Your app will be live!

---

### Option 3: Share Files for Local Installation

Let others run the app on their own computers.

#### Create a Share Package:

1. **Create a folder** with these files:
   ```
   flashcard_package/
   ├── flashcard_app.py
   ├── templates/
   │   └── flashcard.html
   ├── requirements.txt
   ├── Chinese_words_list.xlsx
   ├── README_INSTALL.md
   └── run_flashcard.bat (Windows)
   ```

2. **Create `README_INSTALL.md`:**
   ```markdown
   # Chinese Flashcard App - Installation

   ## Quick Start

   1. Install Python 3.7+ from python.org
   2. Open terminal/command prompt in this folder
   3. Install dependencies:
      ```
      pip install -r requirements.txt
      ```
   4. Run the app:
      ```
      python flashcard_app.py
      ```
   5. Open browser: http://localhost:8001
   ```

3. **Share the folder:**
   - Zip it and email/share via Google Drive, Dropbox, etc.
   - Or upload to GitHub and share the link

---

### Option 4: Docker Container (Advanced)

Create a Docker container for easy deployment.

#### Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flashcard_app.py .
COPY templates/ templates/
COPY Chinese_words_list.xlsx .

EXPOSE 8001

CMD ["uvicorn", "flashcard_app:app", "--host", "0.0.0.0", "--port", "8001"]
```

#### Build and run:
```bash
docker build -t chinese-flashcard .
docker run -p 8001:8001 chinese-flashcard
```

Share the Docker image or Dockerfile with others.

---

## 📋 Pre-Deployment Checklist

Before sharing, make sure:

- [ ] Excel file path is correct or configurable
- [ ] All dependencies are in `requirements.txt`
- [ ] Port is configurable (for cloud deployment)
- [ ] No hardcoded paths (use environment variables)
- [ ] Error handling is in place
- [ ] App works locally first

---

## 🔧 Making the App More Deployable

### Update `flashcard_app.py` for better deployment:

```python
# Add environment variable support
import os
EXCEL_FILE_PATH = Path(os.getenv("EXCEL_FILE_PATH", r"C:\Users\nieli\Documents\Flashcard\Chinese_words_list.xlsx"))

# Make port configurable
PORT = int(os.getenv("PORT", 8001))
```

### Create `.env.example`:
```
EXCEL_FILE_PATH=path/to/your/excel/file.xlsx
PORT=8001
```

---

## 🌐 Recommended: Render.com Deployment

**Why Render.com?**
- ✅ Free tier available
- ✅ Easy GitHub integration
- ✅ Automatic HTTPS
- ✅ Auto-deploys on git push
- ✅ No credit card required for free tier

**Quick Steps:**
1. Push code to GitHub
2. Connect GitHub to Render
3. Render auto-detects FastAPI
4. Add environment variables if needed
5. Deploy!

**Your app will be live at:** `https://your-app-name.onrender.com`

---

## 📱 Mobile Access

Once deployed, the app works on:
- ✅ Desktop browsers (Chrome, Firefox, Safari, Edge)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)
- ✅ Tablets
- ✅ Responsive design included

---

## 🆘 Troubleshooting

### Others can't connect (Local Network):
- Check Windows Firewall settings
- Verify same WiFi network
- Check IP address is correct
- Try different port (8002)

### Cloud deployment fails:
- Check `requirements.txt` has all dependencies
- Verify Python version compatibility
- Check build logs for errors
- Ensure Excel file is included or uploaded

### Excel file not found:
- Update `EXCEL_FILE_PATH` in code
- Or use environment variable
- Make sure file is in the deployment package

---

## 📞 Need Help?

- Check the main README: `FLASHCARD_README.md`
- Review error messages in browser console (F12)
- Check server logs for detailed errors

---

## 🎯 Quick Summary

**For quick sharing (same network):**
→ Use Option 1 (Local Network Sharing)

**For public access (anyone, anywhere):**
→ Use Option 2A (Render.com) - Easiest cloud option

**For offline use:**
→ Use Option 3 (Share Files)

**For advanced users:**
→ Use Option 4 (Docker)

