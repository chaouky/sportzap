#!/bin/bash
# SportZap — Local development setup
# Usage: ./setup.sh

set -e

echo "═══════════════════════════════════════"
echo "  SportZap — Setup"
echo "═══════════════════════════════════════"

# ── Backend ──
echo ""
echo "▸ Setting up backend..."
cd backend

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "  ✓ Virtual environment created"
fi

source .venv/bin/activate
pip install -q -r requirements.txt
echo "  ✓ Python dependencies installed"

echo ""
echo "▸ Running backend tests..."
python tests/test_standalone.py
echo ""
python tests/test_entity_matching.py

cd ..

# ── App ──
echo ""
echo "▸ Setting up app..."
cd app

if [ ! -d "node_modules" ]; then
  npm install
  echo "  ✓ Node dependencies installed"
fi

# Check fonts
if [ ! -d "assets/fonts" ] || [ -z "$(ls -A assets/fonts 2>/dev/null)" ]; then
  echo ""
  echo "  ⚠️  Fonts manquantes !"
  echo "  Téléchargez depuis Google Fonts et placez dans app/assets/fonts/ :"
  echo "    - InstrumentSerif-Regular.ttf"
  echo "    - InstrumentSerif-Italic.ttf"
  echo "    - DMMono-Regular.ttf"
  echo "    - DMMono-Medium.ttf"
fi

cd ..

echo ""
echo "═══════════════════════════════════════"
echo "  ✅ Setup terminé !"
echo ""
echo "  Backend:  cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "  App:      cd app && npx expo start"
echo "═══════════════════════════════════════"
