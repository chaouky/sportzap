# SportZap ⚡

> Programme TV Sport — France  
> Ne ratez plus aucun match.

SportZap est une application mobile qui affiche tous les événements sportifs diffusés à la télévision française, filtrés par vos chaînes et vos équipes favorites, avec des rappels avant chaque match.

![Status](https://img.shields.io/badge/status-MVP%20in%20progress-yellow)
![License](https://img.shields.io/badge/license-proprietary-red)

---

## Architecture

```
sportzap/
├── backend/                 ← FastAPI + Python
│   ├── app/
│   │   ├── xmltv_parser.py      # Parse XMLTV XML (gz/zip/raw)
│   │   ├── sport_extractor.py   # Filtre + classifie + extrait entités
│   │   ├── entity_registry.py   # 111 entités, 241 alias, logos ESPN
│   │   ├── fetcher.py           # Download + cache xmltvfr.fr
│   │   ├── models.py            # Pydantic models
│   │   └── main.py              # REST API (5 endpoints)
│   ├── data/sample_xmltv.xml    # Test data
│   └── tests/                   # Pipeline + entity matching tests
│
├── app/                     ← Expo / React Native
│   ├── App.tsx                  # Entry + tab navigation
│   ├── src/
│   │   ├── screens/
│   │   │   ├── HomeScreen.tsx       # Programme du jour
│   │   │   ├── FavoritesScreen.tsx  # Suivre équipes/compétitions
│   │   │   └── ChannelsScreen.tsx   # Sélection chaînes
│   │   ├── components/
│   │   │   ├── EventCard.tsx        # Carte match
│   │   │   ├── EntityAvatar.tsx     # Logos/drapeaux/photos
│   │   │   ├── SportIcon.tsx        # Icônes sport
│   │   │   └── NotificationSettings.tsx
│   │   ├── hooks/
│   │   │   ├── useEvents.ts         # Fetch + filtre + groupe
│   │   │   ├── useChannels.ts       # Mes Chaînes (AsyncStorage)
│   │   │   ├── useFavorites.ts      # Mes Favoris (AsyncStorage)
│   │   │   └── useAlerts.ts         # Notifications push
│   │   ├── services/
│   │   │   ├── api.ts               # Client FastAPI
│   │   │   └── notifications.ts     # Expo Notifications
│   │   ├── constants/
│   │   │   ├── index.ts             # Couleurs, sports, badges
│   │   │   ├── channels.ts          # 21 chaînes, 7 bouquets
│   │   │   └── favorites.ts         # 25 compétitions, 15 équipes
│   │   └── types/index.ts
│   └── assets/fonts/            # Instrument Serif + DM Mono
```

## Features

- [x] **Pipeline XMLTV → JSON** — Parse xmltvfr.fr (402 chaînes), filtre sport, classifie 8+ sports, extrait équipes/joueurs/pays
- [x] **Entity matching** — 111 entités (Ligue 1, Top 14, PL, Liga, NBA...) avec logos ESPN, drapeaux, photos joueurs
- [x] **3 formats XMLTV gérés** — `Sport : Compétition`, `Sport - Compétition`, desc fallback
- [x] **Design éditorial "Stacked"** — Light mode, typo Instrument Serif + DM Mono
- [x] **Mes Chaînes** — 21 chaînes / 7 bouquets, toggle par groupe, persistence
- [x] **Mes Favoris** — Follow équipes + compétitions, recherche, matching sur events
- [x] **Notifications push** — Rappel configurable (5-60 min), auto-schedule favoris
- [x] **Avatars adaptatifs** — Clubs (logo ESPN), pays (drapeau), joueurs (headshot + mini-drapeau)
- [ ] Live scores (API-Sports enrichment)
- [ ] Dark mode (design Frost)
- [ ] Recherche globale
- [ ] Widget iOS/Android

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Test pipeline
python tests/test_standalone.py        # 15/15 ✅
python tests/test_entity_matching.py   # 52/52 ✅

# Run API
uvicorn app.main:app --reload --port 8000
```

### App

```bash
cd app

# Download fonts (Google Fonts):
# Instrument Serif (Regular + Italic) → assets/fonts/
# DM Mono (Regular + Medium) → assets/fonts/

npm install
npx expo start
```

> Update `API_BASE_URL` in `src/constants/index.ts` with your machine's IP for device testing.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/events` | Events du jour (filtrable: `?date=`, `?sport=`, `?channel=`, `?free_only=`) |
| `GET` | `/api/events/{id}` | Détail d'un événement |
| `GET` | `/api/channels` | Chaînes avec programmation sport |
| `GET` | `/api/sports` | Sports disponibles + compteurs |
| `GET` | `/api/health` | Santé du service + fraîcheur données |
| `POST` | `/api/refresh` | Force re-download XMLTV |

## Data Sources

| Source | Usage | Coût |
|--------|-------|------|
| [xmltvfr.fr](https://xmltvfr.fr) | Programme TV (chaînes + horaires) | Gratuit |
| [flagcdn.com](https://flagcdn.com) | Drapeaux pays | Gratuit |
| [ESPN CDN](https://a.espncdn.com) | Logos clubs + photos joueurs | Gratuit (non-officiel) |
| [API-Sports](https://api-football.com) | Scores live (futur) | Freemium |

## Tech Stack

| Layer | Tech |
|-------|------|
| Mobile | Expo SDK 52, React Native 0.76, TypeScript |
| Backend | FastAPI, Python 3.12 |
| Data | XMLTV (XML), Redis (cache, futur) |
| Notifications | Expo Notifications (local scheduling) |
| Navigation | React Navigation 7 (bottom tabs) |
| Storage | AsyncStorage (prefs), Redis (API cache) |

## License

Proprietary — © 2026 SportZap
