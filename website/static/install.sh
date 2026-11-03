#!/bin/sh
# Installs HumanLang (the `hl` program) on macOS or Linux, just for you (no password needed).
# Use it with:   curl -fsSL https://notsabbir4.github.io/HumanLang/install.sh | sh
set -eu

repo="notsabbir4/HumanLang"
os="$(uname -s)"
arch="$(uname -m)"

case "$os" in
  Linux)  file="hl-linux"; want="x86_64 (the usual kind of Linux computer)" ;;
  Darwin) file="hl-macos"; want="arm64 (a Mac with an M1 chip or newer)" ;;
  *)
    echo "Sorry, this script is only for macOS and Linux. On Windows, download HumanLang-Setup.exe instead:"
    echo "https://notsabbir4.github.io/HumanLang/install.html"
    exit 1 ;;
esac

case "$os-$arch" in
  Linux-x86_64|Linux-amd64|Darwin-arm64) ;;
  *)
    echo "Sorry, the ready-made program is for $want, and this computer is $arch."
    echo "You can still use HumanLang in your browser: https://notsabbir4.github.io/HumanLang/playground.html"
    exit 1 ;;
esac

dir="${HL_INSTALL_DIR:-$HOME/.local/bin}"
mkdir -p "$dir"
url="https://github.com/$repo/releases/latest/download/$file"
tmp="$dir/.hl-download.$$"

echo "Downloading HumanLang from $url"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$url" -o "$tmp"
elif command -v wget >/dev/null 2>&1; then
  wget -q "$url" -O "$tmp"
else
  echo "I need either curl or wget to download the program, and this computer has neither."
  exit 1
fi
chmod +x "$tmp"
mv "$tmp" "$dir/hl"

echo "Installed: $("$dir/hl" --version)  ->  $dir/hl"

case ":$PATH:" in
  *":$dir:"*) echo "Done. Type:  hl --version" ;;
  *)
    case "${SHELL:-}" in
      */zsh)  rc="$HOME/.zshrc" ;;
      */bash) if [ "$os" = "Darwin" ]; then rc="$HOME/.bash_profile"; else rc="$HOME/.bashrc"; fi ;;
      *)      rc="$HOME/.profile" ;;
    esac
    if [ "$dir" = "$HOME/.local/bin" ]; then line='export PATH="$HOME/.local/bin:$PATH"'; else line="export PATH=\"$dir:\$PATH\""; fi
    if ! grep -qsF "$line" "$rc" 2>/dev/null; then
      printf '\n# added by the HumanLang installer\n%s\n' "$line" >> "$rc"
    fi
    echo "I added $dir to your PATH in $rc."
    echo "Close this window, open a new Terminal, and type:  hl --version" ;;
esac
