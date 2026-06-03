#!/usr/bin/env bash
# Install Пепельный Сад on Linux x64 (~/.local/share/pepelny-sad)
set -euo pipefail

APP_NAME="pepelny-sad"
INSTALL_DIR="${PEPELNY_INSTALL_DIR:-$HOME/.local/share/pepelny-sad}"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
YES=0

usage() {
  echo "Usage: $0 [--yes] [SOURCE_DIR]"
  echo "  SOURCE_DIR  unpacked pepelny-sad-linux-x64 directory (default: ./pepelny-sad-linux-x64)"
}

for arg in "$@"; do
  case "$arg" in
    --yes|-y) YES=1 ;;
    -h|--help) usage; exit 0 ;;
    *) SOURCE_DIR="$arg" ;;
  esac
done

SOURCE_DIR="${SOURCE_DIR:-./pepelny-sad-linux-x64}"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Source directory not found: $SOURCE_DIR" >&2
  exit 1
fi

if [[ "$YES" -ne 1 ]]; then
  echo "Install to: $INSTALL_DIR"
  read -r -p "Continue? [Y/n] " reply
  reply=${reply:-Y}
  if [[ ! "$reply" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
  fi
fi

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR"
rsync -a --delete "$SOURCE_DIR/" "$INSTALL_DIR/"

cat > "$BIN_DIR/$APP_NAME" <<EOF
#!/usr/bin/env bash
exec "$INSTALL_DIR/pepelny-sad" "\$@"
EOF
chmod +x "$BIN_DIR/$APP_NAME" "$INSTALL_DIR/pepelny-sad"

cat > "$DESKTOP_DIR/pepelny-sad.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Пепельный Сад
Exec=$INSTALL_DIR/pepelny-sad
Terminal=false
Categories=Game;
EOF

echo "Installed to $INSTALL_DIR"
echo "Run: $APP_NAME"
