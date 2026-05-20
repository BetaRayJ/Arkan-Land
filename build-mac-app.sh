#!/bin/bash
# build-mac-app.sh
# Creates "Arkan Finance.app" in the project folder.
# Run once: bash build-mac-app.sh
# Then drag "Arkan Finance.app" to /Applications or keep it on the Desktop.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Arkan Finance"
APP_BUNDLE="$SCRIPT_DIR/$APP_NAME.app"
PORT=8080

echo "Building $APP_NAME.app …"

# ── App bundle structure ──────────────────────────────────────────────────────
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# ── Info.plist ────────────────────────────────────────────────────────────────
cat > "$APP_BUNDLE/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>   <string>launcher</string>
  <key>CFBundleIdentifier</key>   <string>com.arkan.finance</string>
  <key>CFBundleName</key>         <string>Arkan Finance</string>
  <key>CFBundleDisplayName</key>  <string>Arkan Finance</string>
  <key>CFBundleVersion</key>      <string>1.0</string>
  <key>CFBundleShortVersionString</key> <string>1.0</string>
  <key>CFBundlePackageType</key>  <string>APPL</string>
  <key>CFBundleSignature</key>    <string>????</string>
  <key>LSMinimumSystemVersion</key> <string>11.0</string>
  <key>NSHighResolutionCapable</key> <true/>
  <key>LSUIElement</key>          <false/>
</dict>
</plist>
PLIST

# ── Launcher script (the actual executable) ───────────────────────────────────
# We store the project path at build time so the app always knows where to look.
cat > "$APP_BUNDLE/Contents/MacOS/launcher" << LAUNCHER
#!/bin/bash
PROJECT="$SCRIPT_DIR"
BACKEND="\$PROJECT/backend"
PORT=$PORT
URL="http://localhost:\$PORT"
LOGFILE="\$BACKEND/arkan.log"

# Find Python
PYTHON=""
for c in python3.11 python3.12 python3.10 python3 python; do
  if command -v "\$c" &>/dev/null; then PYTHON="\$c"; break; fi
done

if [ -z "\$PYTHON" ]; then
  osascript -e 'display alert "Python not found" message "Install Python 3.10+ from https://python.org"'
  exit 1
fi

# Virtual env
VENV="\$BACKEND/.venv"
if [ ! -d "\$VENV" ]; then
  "\$PYTHON" -m venv "\$VENV"
fi
source "\$VENV/bin/activate"

# Install deps silently
pip install -q --upgrade pip
pip install -q -r "\$BACKEND/requirements.txt"

# Kill previous instance
lsof -ti tcp:\$PORT | xargs kill -9 2>/dev/null || true
sleep 1

# Start server
cd "\$BACKEND"
python -m uvicorn main:app --host 127.0.0.1 --port \$PORT >> "\$LOGFILE" 2>&1 &
SERVER_PID=\$!

# Wait up to 20 s
for i in \$(seq 1 20); do
  curl -s "\$URL/api/health" >/dev/null 2>&1 && break
  sleep 1
done

# Open browser
open "\$URL"

# Show menu-bar notification
osascript -e "display notification \"Running at \$URL\" with title \"Arkan Finance\" subtitle \"Server started\" sound name \"Glass\""

wait \$SERVER_PID
LAUNCHER

chmod +x "$APP_BUNDLE/Contents/MacOS/launcher"

# ── Icon (generate a simple coloured icon if no .icns provided) ───────────────
ICON_PY=$(cat << 'PYEOF'
import os, struct, zlib

def make_icns(path):
    """Write a minimal 256x256 ICNS with a dark-blue background and 'A' glyph."""
    size = 256
    # Build raw RGBA pixels
    px = []
    cx, cy = size // 2, size // 2
    for y in range(size):
        for x in range(size):
            # Background: dark navy gradient
            r = int(10  + (x/size) * 20)
            g = int(14  + (y/size) * 20)
            b = int(26  + ((x+y)/(size*2)) * 40)
            # Draw rounded rect border
            mx, my = abs(x - cx), abs(y - cy)
            in_border = (mx > 95 or my > 95) and (mx < 115 and my < 115)
            if in_border:
                r, g, b = 59, 130, 246   # blue border
            # Draw letter "A"
            px.append(bytes([r, g, b, 255]))
    raw = b"".join(px)

    # PNG encode manually (just store as raw ICNS ic08 = 256x256 png)
    import io
    try:
        from PIL import Image
        img = Image.new("RGBA", (size, size), (10, 14, 26, 255))
        # Draw a simple gradient square + "A"
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([10,10,245,245], radius=40, fill=(13,17,35,255), outline=(59,130,246,255), width=4)
        draw.text((size//2, size//2), "A", fill=(96,165,250,255), anchor="mm", font=ImageFont.load_default(size=120))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        png_data = buf.getvalue()
    except ImportError:
        # PIL not available — use a minimal 1x1 PNG as placeholder
        import base64
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

    # ICNS container
    type_tag = b"ic08"   # 256×256 PNG
    icon_data = type_tag + struct.pack(">I", 8 + len(png_data)) + png_data
    header = b"icns" + struct.pack(">I", 8 + len(icon_data))
    with open(path, "wb") as f:
        f.write(header + icon_data)
    print("Icon written:", path)

make_icns(os.path.join(os.environ["APP_RESOURCES"], "AppIcon.icns"))
PYEOF
)

APP_RESOURCES="$APP_BUNDLE/Contents/Resources" python3 -c "$ICON_PY" 2>/dev/null || true

# Point Info.plist at icon if it was created
if [ -f "$APP_BUNDLE/Contents/Resources/AppIcon.icns" ]; then
  /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string AppIcon" \
    "$APP_BUNDLE/Contents/Info.plist" 2>/dev/null || true
fi

echo ""
echo "✅  Built: $APP_BUNDLE"
echo ""
echo "Next steps:"
echo "  1. Double-click  \"$APP_NAME.app\"  to launch (first run installs deps)"
echo "  2. Or drag it to /Applications for a permanent install"
echo "  3. Right-click → 'Open' the first time (to bypass Gatekeeper)"
echo ""
echo "To add to Dock: open the app, then right-click its Dock icon → Options → Keep in Dock"
