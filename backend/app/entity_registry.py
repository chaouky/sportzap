"""
SportZap — Entity Registry

Maps raw XMLTV team/player names → structured entity metadata
(logo URLs, country codes, short names, aliases).

This is the bridge between the messy XMLTV text and the polished
frontend avatars. Uses fuzzy matching to handle name variants.

Sources:
  - Club logos: ESPN CDN (free, unofficial)
  - Flags: flagcdn.com (free)
  - Player photos: ESPN headshots (free, unofficial)

In production, migrate to TheSportsDB or API-Sports for
official logos with proper licensing.
"""
from __future__ import annotations

import re
from functools import lru_cache
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EntityProfile:
    """Visual + metadata profile for a team/player/country."""
    canonical_name: str          # Display name: "Paris Saint-Germain"
    short_name: str              # Short: "PSG"
    entity_type: str             # "club" | "country" | "player"
    sport: str                   # Primary sport context
    country_code: Optional[str] = None   # ISO-2: "fr"
    logo_url: Optional[str] = None       # Club crest / event logo
    photo_url: Optional[str] = None      # Player headshot
    colors: tuple[str, str] = ("#666", "#999")  # Primary, secondary
    aliases: list[str] = field(default_factory=list)  # All known name variants


# ═══════════════════════════════════════════════════════
# ESPN CDN helpers
# ═══════════════════════════════════════════════════════

def _espn_soccer(eid: int) -> str:
    return f"https://a.espncdn.com/i/teamlogos/soccer/500/{eid}.png"

# Anciens identifiants ESPN (fichiers /rugby/500/ désormais en 404) -> identifiants actuels
# (/rugby/teams/500/). None = pas de logo ESPN : le repli Wikipédia (other_teams.json) prend le relais.
_ESPN_RUGBY_IDS = {
    2584: 25922, 2576: 99855, 2580: 25921, 2577: 119318, 2570: 25917, 2583: 25986,
    2569: 143737, 2568: 25916, 2573: 25918, 2579: 270567, 2572: 143736,
    2567: None, 2571: None, 2578: None, 2585: None,
}


def _espn_rugby(eid: int) -> str | None:
    new_id = _ESPN_RUGBY_IDS.get(eid, eid)
    if new_id is None:
        return None
    return f"https://a.espncdn.com/i/teamlogos/rugby/teams/500/{new_id}.png"

def _espn_nba(eid: int) -> str:
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{eid}.png"

def _espn_player(eid: int, sport: str = "tennis") -> str:
    return f"https://a.espncdn.com/combiner/i?img=/i/headshots/{sport}/players/full/{eid}.png&w=130&h=100"

def _flag(code: str) -> str:
    return f"https://flagcdn.com/w80/{code}.png"


# ═══════════════════════════════════════════════════════
# REGISTRY DATA
# ═══════════════════════════════════════════════════════

ENTITY_REGISTRY: list[EntityProfile] = [

    # ────────────────────────────────────────────
    # FOOTBALL — Ligue 1
    # ────────────────────────────────────────────
    EntityProfile("Paris Saint-Germain", "PSG", "club", "football", "fr",
        logo_url=_espn_soccer(160), colors=("#004170", "#DA291C"),
        aliases=["Paris-SG", "Paris SG", "Paris Saint Germain", "PSG", "Paris-Saint-Germain"]),

    EntityProfile("Paris FC", "Paris FC", "club", "football", "fr",
        logo_url=_espn_soccer(6851), colors=("#003189", "#FFFFFF"),
        aliases=["Paris FC", "PFC"]),

    EntityProfile("Olympique de Marseille", "OM", "club", "football", "fr",
        logo_url=_espn_soccer(176), colors=("#2FAEE0", "#FFFFFF"),
        aliases=["Olympique de Marseille", "OM", "Marseille", "O. Marseille"]),

    EntityProfile("Olympique Lyonnais", "OL", "club", "football", "fr",
        logo_url=_espn_soccer(167), colors=("#1D4A8D", "#ED1C24"),
        aliases=["Olympique Lyonnais", "OL", "Lyon", "O. Lyonnais"]),

    EntityProfile("AS Monaco", "Monaco", "club", "football", "fr",
        logo_url=_espn_soccer(174), colors=("#E4002B", "#FFFFFF"),
        aliases=["AS Monaco", "Monaco", "AS Monaco FC"]),

    EntityProfile("LOSC Lille", "LOSC", "club", "football", "fr",
        logo_url=_espn_soccer(166), colors=("#E4002B", "#1D1D1B"),
        aliases=["LOSC Lille", "LOSC", "Lille", "Lille OSC"]),

    EntityProfile("Stade Rennais", "Rennes", "club", "football", "fr",
        logo_url=_espn_soccer(169), colors=("#DA291C", "#000000"),
        aliases=["Stade Rennais", "Rennes", "Stade Rennais FC"]),

    EntityProfile("RC Lens", "Lens", "club", "football", "fr",
        logo_url=_espn_soccer(175), colors=("#F1C40F", "#E4002B"),
        aliases=["RC Lens", "Lens", "Racing Club de Lens"]),

    EntityProfile("OGC Nice", "Nice", "club", "football", "fr",
        logo_url=_espn_soccer(2502), colors=("#000000", "#DA291C"),
        aliases=["OGC Nice", "Nice", "OGC Nice Côte d'Azur"]),

    EntityProfile("RC Strasbourg", "Strasbourg", "club", "football", "fr",
        logo_url=_espn_soccer(180), colors=("#0055A4", "#FFFFFF"),
        aliases=["RC Strasbourg", "Strasbourg", "RC Strasbourg Alsace"]),

    EntityProfile("FC Nantes", "Nantes", "club", "football", "fr",
        logo_url=_espn_soccer(165), colors=("#00A651", "#F1C40F"),
        aliases=["FC Nantes", "Nantes"]),

    EntityProfile("Montpellier HSC", "Montpellier", "club", "football", "fr",
        logo_url=_espn_soccer(274), colors=("#FF6900", "#003DA6"),
        aliases=["Montpellier HSC", "Montpellier", "Montpellier Hérault"]),

    EntityProfile("Stade de Reims", "Reims", "club", "football", "fr",
        logo_url=_espn_soccer(3243), colors=("#DA291C", "#FFFFFF"),
        aliases=["Stade de Reims", "Reims"]),

    EntityProfile("Toulouse FC", "TFC", "club", "football", "fr",
        logo_url=_espn_soccer(179), colors=("#6B2C91", "#FFFFFF"),
        aliases=["Toulouse FC", "Toulouse", "TFC"]),

    EntityProfile("AJ Auxerre", "Auxerre", "club", "football", "fr",
        logo_url=_espn_soccer(172), colors=("#003DA6", "#FFFFFF"),
        aliases=["AJ Auxerre", "Auxerre"]),

    EntityProfile("Angers SCO", "Angers", "club", "football", "fr",
        logo_url=_espn_soccer(7868), colors=("#000000", "#FFFFFF"),
        aliases=["Angers SCO", "Angers"]),

    EntityProfile("AS Saint-Étienne", "ASSE", "club", "football", "fr",
        logo_url=_espn_soccer(178), colors=("#00843D", "#FFFFFF"),
        aliases=["AS Saint-Étienne", "AS Saint-Etienne", "Saint-Étienne", "Saint-Etienne", "ASSE"]),

    EntityProfile("Le Havre AC", "Le Havre", "club", "football", "fr",
        logo_url=_espn_soccer(3236), colors=("#0055A4", "#87CEEB"),
        aliases=["Le Havre AC", "Le Havre", "HAC"]),

    EntityProfile("Stade Brestois", "Brest", "club", "football", "fr",
        logo_url=_espn_soccer(6997), colors=("#DA291C", "#FFFFFF"),
        aliases=["Stade Brestois", "Brest", "Stade Brestois 29"]),

    # ────────────────────────────────────────────
    # FOOTBALL — Premier League (top clubs)
    # ────────────────────────────────────────────
    EntityProfile("Arsenal FC", "Arsenal", "club", "football", "gb-eng",
        logo_url=_espn_soccer(359), colors=("#EF0107", "#063672"),
        aliases=["Arsenal FC", "Arsenal"]),

    EntityProfile("Manchester City", "Man City", "club", "football", "gb-eng",
        logo_url=_espn_soccer(382), colors=("#6CABDD", "#1C2C5B"),
        aliases=["Manchester City", "Man City", "Man. City", "Manchester City FC"]),

    EntityProfile("Liverpool FC", "Liverpool", "club", "football", "gb-eng",
        logo_url=_espn_soccer(364), colors=("#C8102E", "#00B2A9"),
        aliases=["Liverpool FC", "Liverpool"]),

    EntityProfile("Chelsea FC", "Chelsea", "club", "football", "gb-eng",
        logo_url=_espn_soccer(363), colors=("#034694", "#DBA111"),
        aliases=["Chelsea FC", "Chelsea"]),

    EntityProfile("Manchester United", "Man Utd", "club", "football", "gb-eng",
        logo_url=_espn_soccer(360), colors=("#DA291C", "#FBE122"),
        aliases=["Manchester United", "Man Utd", "Man. United", "Manchester United FC"]),

    EntityProfile("Tottenham Hotspur", "Tottenham", "club", "football", "gb-eng",
        logo_url=_espn_soccer(367), colors=("#132257", "#FFFFFF"),
        aliases=["Tottenham Hotspur", "Tottenham", "Spurs"]),

    EntityProfile("Aston Villa", "Aston Villa", "club", "football", "gb-eng",
        logo_url=_espn_soccer(362), colors=("#670E36", "#95BFE5"),
        aliases=["Aston Villa", "Aston Villa FC"]),

    EntityProfile("Newcastle United", "Newcastle", "club", "football", "gb-eng",
        logo_url=_espn_soccer(361), colors=("#241F20", "#FFFFFF"),
        aliases=["Newcastle United", "Newcastle", "Newcastle Utd"]),

    # ────────────────────────────────────────────
    # FOOTBALL — Liga (top clubs)
    # ────────────────────────────────────────────
    EntityProfile("Real Madrid CF", "Real Madrid", "club", "football", "es",
        logo_url=_espn_soccer(86), colors=("#FEBE10", "#00529F"),
        aliases=["Real Madrid", "Real Madrid CF", "R. Madrid"]),

    EntityProfile("FC Barcelone", "Barça", "club", "football", "es",
        logo_url=_espn_soccer(83), colors=("#A50044", "#004D98"),
        aliases=["FC Barcelone", "FC Barcelona", "Barça", "Barcelone", "Barcelona"]),

    EntityProfile("Atlético Madrid", "Atlético", "club", "football", "es",
        logo_url=_espn_soccer(1068), colors=("#CB3524", "#FFFFFF"),
        aliases=["Atlético Madrid", "Atletico Madrid", "Atlético", "Atletico"]),


    # ────────────────────────────────────────────
    # FOOTBALL — Liga & Liga 2 (clubs du calendrier ESPN)
    # ────────────────────────────────────────────
    EntityProfile("Deportivo Alavés", "Alavés", "club", "football", "es",
        logo_url=_espn_soccer(96), colors=("#0000FF", "#FFFFFF"),
        aliases=["Alavés", "Alaves", "Deportivo Alavés", "Deportivo Alaves"]),

    EntityProfile("Athletic Club", "Athletic", "club", "football", "es",
        logo_url=_espn_soccer(93), colors=("#C8142F", "#FFFFFF"),
        aliases=["Athletic Club", "Athletic Bilbao", "Athletic Club Bilbao", "Bilbao"]),

    EntityProfile("Celta Vigo", "Celta", "club", "football", "es",
        logo_url=_espn_soccer(85), colors=("#6CACE4", "#FFFFFF"),
        aliases=["Celta Vigo", "Celta de Vigo", "Celta"]),

    EntityProfile("Deportivo La Corogne", "Deportivo", "club", "football", "es",
        logo_url=_espn_soccer(90), colors=("#3366CC", "#FFFFFF"),
        aliases=["Deportivo La Corogne", "Deportivo La Coruña", "Deportivo La Coruna", "RC Deportivo", "Deportivo"]),

    EntityProfile("Elche CF", "Elche", "club", "football", "es",
        logo_url=_espn_soccer(3751), colors=("#288A00", "#FFFFFF"),
        aliases=["Elche", "Elche CF"]),

    EntityProfile("Espanyol Barcelone", "Espanyol", "club", "football", "es",
        logo_url=_espn_soccer(88), colors=("#3366CC", "#FFFFFF"),
        aliases=["Espanyol Barcelone", "Espanyol", "RCD Espanyol", "Espanyol Barcelona"]),

    EntityProfile("Getafe CF", "Getafe", "club", "football", "es",
        logo_url=_espn_soccer(2922), colors=("#0000FF", "#FFFFFF"),
        aliases=["Getafe", "Getafe CF"]),

    EntityProfile("Levante UD", "Levante", "club", "football", "es",
        logo_url=_espn_soccer(1538), colors=("#C8142F", "#003A8F"),
        aliases=["Levante", "Levante UD"]),

    EntityProfile("Málaga CF", "Málaga", "club", "football", "es",
        logo_url=_espn_soccer(99), colors=("#B9E8F0", "#FFFFFF"),
        aliases=["Málaga", "Malaga", "Malaga CF", "Málaga CF"]),

    EntityProfile("CA Osasuna", "Osasuna", "club", "football", "es",
        logo_url=_espn_soccer(97), colors=("#CD0000", "#FFFFFF"),
        aliases=["Osasuna", "CA Osasuna"]),

    EntityProfile("Racing Santander", "Racing", "club", "football", "es",
        logo_url=_espn_soccer(87), colors=("#3B6C1A", "#FFFFFF"),
        aliases=["Racing Santander", "Racing de Santander", "Racing Santander"]),

    EntityProfile("Rayo Vallecano", "Rayo", "club", "football", "es",
        logo_url=_espn_soccer(101), colors=("#FFFFFF", "#CD0000"),
        aliases=["Rayo Vallecano", "Rayo"]),

    EntityProfile("Real Betis", "Betis", "club", "football", "es",
        logo_url=_espn_soccer(244), colors=("#288A00", "#FFFFFF"),
        aliases=["Real Betis", "Betis Séville", "Betis Seville", "Betis", "Real Betis Séville"]),

    EntityProfile("Real Sociedad", "Real Sociedad", "club", "football", "es",
        logo_url=_espn_soccer(89), colors=("#3366CC", "#FFFFFF"),
        aliases=["Real Sociedad"]),

    EntityProfile("FC Séville", "Séville", "club", "football", "es",
        logo_url=_espn_soccer(243), colors=("#D81022", "#FFFFFF"),
        aliases=["FC Séville", "FC Seville", "Séville", "Seville", "Sevilla", "Sevilla FC", "FC Sevilla"]),

    EntityProfile("Valence CF", "Valence", "club", "football", "es",
        logo_url=_espn_soccer(94), colors=("#FF6F00", "#FFFFFF"),
        aliases=["Valence", "Valence CF", "Valencia", "Valencia CF"]),

    EntityProfile("Villarreal CF", "Villarreal", "club", "football", "es",
        logo_url=_espn_soccer(102), colors=("#FFFF00", "#6CACE4"),
        aliases=["Villarreal", "Villarreal CF", "FC Villarreal"]),

    EntityProfile("Albacete", "Albacete", "club", "football", "es",
        logo_url=_espn_soccer(2737), colors=("#BC0814", "#FFFFFF"),
        aliases=["Albacete", "Albacete Balompié"]),

    EntityProfile("UD Almería", "Almería", "club", "football", "es",
        logo_url=_espn_soccer(6832), colors=("#C8142F", "#FFFFFF"),
        aliases=["Almería", "Almeria", "UD Almería"]),

    EntityProfile("Burgos CF", "Burgos", "club", "football", "es",
        logo_url=_espn_soccer(12597), colors=("#000000", "#FFFFFF"),
        aliases=["Burgos", "Burgos CF"]),

    EntityProfile("CE Sabadell", "Sabadell", "club", "football", "es",
        logo_url=_espn_soccer(11487), colors=("#000000", "#FFFFFF"),
        aliases=["CE Sabadell", "Sabadell"]),

    EntityProfile("CD Castellón", "Castellón", "club", "football", "es",
        logo_url=_espn_soccer(4438), colors=("#000000", "#FFFFFF"),
        aliases=["Castellón", "Castellon", "CD Castellón"]),

    EntityProfile("AD Ceuta", "Ceuta", "club", "football", "es",
        logo_url=_espn_soccer(5404), colors=("#000000", "#FFFFFF"),
        aliases=["Ceuta", "AD Ceuta"]),

    EntityProfile("Cadix CF", "Cadix", "club", "football", "es",
        logo_url=_espn_soccer(3842), colors=("#FFFF00", "#FFFFFF"),
        aliases=["Cadix", "Cádiz", "Cadiz", "Cádiz CF"]),

    EntityProfile("Cordoue CF", "Cordoue", "club", "football", "es",
        logo_url=_espn_soccer(8447), colors=("#288A00", "#FFFFFF"),
        aliases=["Cordoue", "Córdoba", "Cordoba", "Córdoba CF"]),

    EntityProfile("SD Eibar", "Eibar", "club", "football", "es",
        logo_url=_espn_soccer(3752), colors=("#C00000", "#FFFFFF"),
        aliases=["Eibar", "SD Eibar"]),

    EntityProfile("CD Eldense", "Eldense", "club", "football", "es",
        logo_url=_espn_soccer(7320), colors=("#000000", "#FFFFFF"),
        aliases=["Eldense", "CD Eldense"]),

    EntityProfile("FC Andorra", "Andorra", "club", "football", "es",
        logo_url=_espn_soccer(20179), colors=("#000000", "#FFFFFF"),
        aliases=["FC Andorra", "Andorre"]),

    EntityProfile("Gérone FC", "Gérone", "club", "football", "es",
        logo_url=_espn_soccer(9812), colors=("#C60000", "#FFFFFF"),
        aliases=["Gérone", "Girona", "Girona FC", "Gérone FC"]),

    EntityProfile("Grenade CF", "Grenade", "club", "football", "es",
        logo_url=_espn_soccer(3747), colors=("#C8142F", "#FFFFFF"),
        aliases=["Grenade", "Granada", "Granada CF"]),

    EntityProfile("UD Las Palmas", "Las Palmas", "club", "football", "es",
        logo_url=_espn_soccer(98), colors=("#FFFF00", "#FFFFFF"),
        aliases=["Las Palmas", "UD Las Palmas"]),

    EntityProfile("CD Leganés", "Leganés", "club", "football", "es",
        logo_url=_espn_soccer(17534), colors=("#6CACE4", "#FFFFFF"),
        aliases=["Leganés", "Leganes", "CD Leganés"]),

    EntityProfile("Majorque", "Majorque", "club", "football", "es",
        logo_url=_espn_soccer(84), colors=("#C8142F", "#FFFFFF"),
        aliases=["Majorque", "Mallorca", "RCD Mallorca", "RCD Majorque"]),

    EntityProfile("Real Oviedo", "Oviedo", "club", "football", "es",
        logo_url=_espn_soccer(92), colors=("#E23627", "#FFFFFF"),
        aliases=["Real Oviedo", "Oviedo"]),

    EntityProfile("Real Valladolid", "Valladolid", "club", "football", "es",
        logo_url=_espn_soccer(95), colors=("#7A2D9D", "#FFFFFF"),
        aliases=["Real Valladolid", "Valladolid"]),

    EntityProfile("Sporting Gijón", "Gijón", "club", "football", "es",
        logo_url=_espn_soccer(3788), colors=("#C8142F", "#FFFFFF"),
        aliases=["Sporting Gijón", "Sporting Gijon", "Gijón", "Gijon"]),

    EntityProfile("CD Tenerife", "Tenerife", "club", "football", "es",
        logo_url=_espn_soccer(245), colors=("#008BC4", "#FFFFFF"),
        aliases=["Tenerife", "CD Tenerife"]),

    # ────────────────────────────────────────────
    # FOOTBALL — Portugal (top clubs)
    # ────────────────────────────────────────────
    EntityProfile("Sporting CP", "Sporting", "club", "football", "pt",
        logo_url=_espn_soccer(2250), colors=("#009B3A", "#FFD700"),
        aliases=["Sporting CP", "Sporting Club Portugal", "Sporting Club de Portugal",
                 "Sporting Clube de Portugal", "Sporting", "Sporting Portugal"]),

    EntityProfile("SL Benfica", "Benfica", "club", "football", "pt",
        logo_url=_espn_soccer(1929), colors=("#CC0000", "#FFFFFF"),
        aliases=["SL Benfica", "Benfica", "Sport Lisboa e Benfica"]),

    EntityProfile("FC Porto", "Porto", "club", "football", "pt",
        logo_url=_espn_soccer(437), colors=("#003087", "#FFFFFF"),
        aliases=["FC Porto", "Porto", "F.C. Porto"]),

    EntityProfile("SC Braga", "Braga", "club", "football", "pt",
        logo_url=_espn_soccer(2994), colors=("#CC0000", "#FFFFFF"),
        aliases=["SC Braga", "Braga", "Sporting Braga", "Sporting de Braga"]),

    # ────────────────────────────────────────────
    # FOOTBALL — Serie A (top clubs)
    # ────────────────────────────────────────────
    EntityProfile("Juventus FC", "Juventus", "club", "football", "it",
        logo_url=_espn_soccer(111), colors=("#000000", "#FFFFFF"),
        aliases=["Juventus FC", "Juventus", "Juve"]),

    EntityProfile("AC Milan", "AC Milan", "club", "football", "it",
        logo_url=_espn_soccer(103), colors=("#FB090B", "#000000"),
        aliases=["AC Milan", "Milan AC", "Milan"]),

    EntityProfile("Inter Milan", "Inter", "club", "football", "it",
        logo_url=_espn_soccer(110), colors=("#010E80", "#000000"),
        aliases=["Inter Milan", "Inter", "Internazionale", "FC Internazionale"]),

    EntityProfile("SSC Napoli", "Napoli", "club", "football", "it",
        logo_url=_espn_soccer(114), colors=("#12A0D7", "#FFFFFF"),
        aliases=["SSC Napoli", "Napoli", "Naples"]),

    # ────────────────────────────────────────────
    # FOOTBALL — Bundesliga (top clubs)
    # ────────────────────────────────────────────
    EntityProfile("Bayern Munich", "Bayern", "club", "football", "de",
        logo_url=_espn_soccer(132), colors=("#DC052D", "#0066B2"),
        aliases=["Bayern Munich", "Bayern", "FC Bayern", "Bayern München", "FC Bayern Munich"]),

    EntityProfile("Borussia Dortmund", "BVB", "club", "football", "de",
        logo_url=_espn_soccer(124), colors=("#FDE100", "#000000"),
        aliases=["Borussia Dortmund", "Dortmund", "BVB"]),

    EntityProfile("Bayer Leverkusen", "Leverkusen", "club", "football", "de",
        logo_url=_espn_soccer(131), colors=("#E32221", "#000000"),
        aliases=["Bayer Leverkusen", "Leverkusen", "B. Leverkusen"]),

    # ────────────────────────────────────────────
    # RUGBY — Top 14
    # ────────────────────────────────────────────
    EntityProfile("Stade Toulousain", "Toulouse", "club", "rugby", "fr",
        logo_url=_espn_rugby(2584), colors=("#E4002B", "#1D1D1B"),
        aliases=["Stade Toulousain", "Toulouse", "ST"]),

    EntityProfile("Racing 92", "Racing 92", "club", "rugby", "fr",
        logo_url=_espn_rugby(2576), colors=("#5BC5F2", "#1B2A4A"),
        aliases=["Racing 92", "Racing"]),

    EntityProfile("Stade Français", "Stade Français", "club", "rugby", "fr",
        logo_url=_espn_rugby(2580), colors=("#FF69B4", "#1B2A4A"),
        aliases=["Stade Français", "Stade Francais", "SF Paris"]),

    EntityProfile("La Rochelle", "La Rochelle", "club", "rugby", "fr",
        logo_url=_espn_rugby(2577), colors=("#F1C40F", "#000000"),
        aliases=["La Rochelle", "Stade Rochelais"]),

    EntityProfile("ASM Clermont", "Clermont", "club", "rugby", "fr",
        logo_url=_espn_rugby(2570), colors=("#F1C40F", "#003DA6"),
        aliases=["ASM Clermont", "Clermont", "ASM Clermont Auvergne"]),

    EntityProfile("RC Toulon", "Toulon", "club", "rugby", "fr",
        logo_url=_espn_rugby(2583), colors=("#DA291C", "#000000"),
        aliases=["RC Toulon", "Toulon"]),

    EntityProfile("Union Bordeaux-Bègles", "UBB", "club", "rugby", "fr",
        logo_url=_espn_rugby(2569), colors=("#C8102E", "#1D1D1B"),
        aliases=["Union Bordeaux-Bègles", "Bordeaux-Bègles", "UBB", "Bordeaux"]),

    EntityProfile("Castres Olympique", "Castres", "club", "rugby", "fr",
        logo_url=_espn_rugby(2568), colors=("#003DA6", "#FFFFFF"),
        aliases=["Castres Olympique", "Castres", "CO"]),

    EntityProfile("Montpellier HR", "MHR", "club", "rugby", "fr",
        logo_url=_espn_rugby(2573), colors=("#003DA6", "#DA291C"),
        aliases=["Montpellier Hérault Rugby", "MHR", "Montpellier HR"]),

    EntityProfile("Section Paloise", "Pau", "club", "rugby", "fr",
        logo_url=_espn_rugby(2579), colors=("#00843D", "#F1C40F"),
        aliases=["Section Paloise", "Pau"]),

    EntityProfile("Lyon OU", "LOU", "club", "rugby", "fr",
        logo_url=_espn_rugby(2572), colors=("#DA291C", "#000000"),
        aliases=["Lyon OU", "LOU", "LOU Rugby"]),

    EntityProfile("SU Agen", "Agen", "club", "rugby", "fr",
        logo_url=_espn_rugby(2567), colors=("#003DA6", "#FFFFFF"),
        aliases=["SU Agen", "Agen"]),

    EntityProfile("CA Brive", "Brive", "club", "rugby", "fr",
        logo_url=_espn_rugby(2571), colors=("#000000", "#F1C40F"),
        aliases=["CA Brive", "Brive"]),

    EntityProfile("Aviron Bayonnais", "Bayonne", "club", "rugby", "fr",
        logo_url=_espn_rugby(2578), colors=("#003DA6", "#FFFFFF"),
        aliases=["Aviron Bayonnais", "Bayonne"]),

    EntityProfile("RC Vannes", "Vannes", "club", "rugby", "fr",
        colors=("#003DA6", "#DA291C"),
        aliases=["RC Vannes", "Vannes"]),

    EntityProfile("USA Perpignan", "Perpignan", "club", "rugby", "fr",
        logo_url=_espn_rugby(2585), colors=("#F7941E", "#E4002B"),
        aliases=["USA Perpignan", "Perpignan", "USAP"]),

    # ────────────────────────────────────────────
    # BASKETBALL — NBA (top matchups on beIN)
    # ────────────────────────────────────────────
    EntityProfile("Los Angeles Lakers", "Lakers", "club", "basket", "us",
        logo_url=_espn_nba(13), colors=("#552583", "#FDB927"),
        aliases=["Los Angeles Lakers", "Lakers", "LA Lakers"]),

    EntityProfile("Boston Celtics", "Celtics", "club", "basket", "us",
        logo_url=_espn_nba(2), colors=("#007A33", "#BA9653"),
        aliases=["Boston Celtics", "Celtics"]),

    EntityProfile("Golden State Warriors", "Warriors", "club", "basket", "us",
        logo_url=_espn_nba(9), colors=("#1D428A", "#FFC72C"),
        aliases=["Golden State Warriors", "Warriors", "Golden State"]),

    EntityProfile("Milwaukee Bucks", "Bucks", "club", "basket", "us",
        logo_url=_espn_nba(15), colors=("#00471B", "#EEE1C6"),
        aliases=["Milwaukee Bucks", "Bucks"]),

    EntityProfile("Denver Nuggets", "Nuggets", "club", "basket", "us",
        logo_url=_espn_nba(7), colors=("#0E2240", "#FEC524"),
        aliases=["Denver Nuggets", "Nuggets"]),

    EntityProfile("Philadelphia 76ers", "76ers", "club", "basket", "us",
        logo_url=_espn_nba(20), colors=("#006BB6", "#ED174C"),
        aliases=["Philadelphia 76ers", "76ers", "Sixers"]),

    EntityProfile("Dallas Mavericks", "Mavericks", "club", "basket", "us",
        logo_url=_espn_nba(6), colors=("#00538C", "#002B5E"),
        aliases=["Dallas Mavericks", "Mavericks", "Dallas"]),

    EntityProfile("New York Knicks", "Knicks", "club", "basket", "us",
        logo_url=_espn_nba(18), colors=("#006BB6", "#F58426"),
        aliases=["New York Knicks", "Knicks"]),

    # ────────────────────────────────────────────
    # TENNIS — Top players
    # ────────────────────────────────────────────
    EntityProfile("Novak Djokovic", "Djokovic", "player", "tennis", "rs",
        photo_url=_espn_player(598, "tennis"),
        aliases=["N. Djokovic", "Novak Djokovic", "Djokovic"]),

    EntityProfile("Carlos Alcaraz", "Alcaraz", "player", "tennis", "es",
        photo_url=_espn_player(4685, "tennis"),
        aliases=["C. Alcaraz", "Carlos Alcaraz", "Alcaraz"]),

    EntityProfile("Jannik Sinner", "Sinner", "player", "tennis", "it",
        photo_url=_espn_player(4686, "tennis"),
        aliases=["J. Sinner", "Jannik Sinner", "Sinner"]),

    EntityProfile("Rafael Nadal", "Nadal", "player", "tennis", "es",
        photo_url=_espn_player(1506, "tennis"),
        aliases=["R. Nadal", "Rafael Nadal", "Nadal"]),

    # ────────────────────────────────────────────
    # MMA / BOXE — Notable fighters
    # ────────────────────────────────────────────
    EntityProfile("Francis Ngannou", "Ngannou", "player", "mma", "cm",
        photo_url=_espn_player(3956, "mma"),
        aliases=["Francis Ngannou", "Ngannou", "F. Ngannou"]),

    EntityProfile("Tyson Fury", "Fury", "player", "mma", "gb",
        photo_url=_espn_player(4426, "boxing"),
        aliases=["Tyson Fury", "Fury", "T. Fury"]),

    EntityProfile("Ciryl Gane", "Gane", "player", "mma", "fr",
        photo_url=_espn_player(4685, "mma"),
        aliases=["Ciryl Gane", "Gane", "C. Gane"]),

    # ────────────────────────────────────────────
    # NATIONAL TEAMS (football, rugby, handball)
    # ────────────────────────────────────────────
    *[EntityProfile(name.title(), name.title(), "country", "football", code,
        logo_url=_flag(code),
        aliases=[name.title(), name])
      for name, code in {
          "france": "fr", "allemagne": "de", "espagne": "es", "italie": "it",
          "angleterre": "gb-eng", "portugal": "pt", "belgique": "be",
          "pays-bas": "nl", "croatie": "hr", "danemark": "dk",
          "suisse": "ch", "autriche": "at", "pologne": "pl", "suède": "se",
          "norvège": "no", "serbie": "rs", "ukraine": "ua", "turquie": "tr",
          "grèce": "gr", "roumanie": "ro", "écosse": "gb-sct",
          "galles": "gb-wls", "irlande": "ie",
          "brésil": "br", "argentine": "ar", "colombie": "co",
          "mexique": "mx", "uruguay": "uy", "chili": "cl",
          "états-unis": "us", "canada": "ca",
          "japon": "jp", "corée": "kr", "australie": "au",
          "maroc": "ma", "sénégal": "sn", "cameroun": "cm",
          "algérie": "dz", "tunisie": "tn", "nigeria": "ng",
          "côte d'ivoire": "ci", "ghana": "gh",
          "afrique du sud": "za", "égypte": "eg",
      }.items()
    ],
]


# ═══════════════════════════════════════════════════════
# MATCHING ENGINE
# ═══════════════════════════════════════════════════════

# Build lookup index: alias → EntityProfile
_ALIAS_INDEX: dict[str, EntityProfile] = {}
for _profile in ENTITY_REGISTRY:
    for _alias in _profile.aliases:
        _key = _alias.strip().lower()
        _ALIAS_INDEX[_key] = _profile
    # Also index canonical and short names
    _ALIAS_INDEX[_profile.canonical_name.strip().lower()] = _profile
    _ALIAS_INDEX[_profile.short_name.strip().lower()] = _profile


def _normalize(name: str) -> str:
    """Normalize name for matching: lowercase, strip accents, remove FC/AS etc."""
    s = name.strip().lower()
    # Remove common prefixes/suffixes
    s = re.sub(r"\b(?:fc|as|rc|sc|ac|sc|og|aj|ca|su|usa|ssc|ss|us)\b", "", s).strip()
    # Remove "équipe de" prefix
    s = re.sub(r"^(?:équipe|equipe)\s+(?:de|du|des|d')\s*", "", s).strip()
    return s


def match_entity(raw_name: str, sport: Optional[str] = None) -> Optional[EntityProfile]:
    """
    Find the best matching EntityProfile for a raw XMLTV name.

    Matching strategy (in order):
      1. Exact alias match
      2. Normalized match (strip FC/AS, accents)
      3. Substring match (for partial names)

    Args:
        raw_name: Raw name from XMLTV, e.g. "Paris-SG", "Olympique Lyonnais"
        sport: Optional sport context for disambiguation

    Returns:
        EntityProfile if found, None otherwise
    """
    if not raw_name:
        return None

    key = raw_name.strip().lower()

    # 1. Exact alias match
    if key in _ALIAS_INDEX:
        profile = _ALIAS_INDEX[key]
        if sport and profile.sport != sport:
            # Sport mismatch — might be wrong entity, but still return
            pass
        return profile

    # 2. Normalized match
    norm = _normalize(raw_name)
    if norm and norm in _ALIAS_INDEX:
        return _ALIAS_INDEX[norm]

    # 3. Substring match — check if raw_name contains any known alias
    for alias_key, profile in _ALIAS_INDEX.items():
        if len(alias_key) >= 4 and alias_key in key:
            if sport and profile.sport != sport:
                continue
            return profile

    # 4. Reverse substring — check if any alias contains raw_name
    if len(norm) >= 4:
        for alias_key, profile in _ALIAS_INDEX.items():
            if norm in alias_key:
                if sport and profile.sport != sport:
                    continue
                return profile

    return None


# ═══════════════════════════════════════════════════════
# REPLI : clubs du calendrier ESPN (écusson + nom court)
# ═══════════════════════════════════════════════════════
# Le registre ci-dessus contient les noms français usuels des gros clubs. Pour les
# autres clubs des championnats suivis (data/espn_teams.json : D1/D2 de France,
# Allemagne, Angleterre, Espagne, Italie, Portugal + Turquie, Pays-Bas, Belgique,
# Écosse, Suisse), on rapproche le nom vu à la TV des noms ESPN.

_ESPN_COUNTRY = {"fra": "fr", "eng": "gb-eng", "ger": "de", "ita": "it", "esp": "es", "por": "pt",
                 "tur": "tr", "ned": "nl", "bel": "be", "sco": "gb-sct", "sui": "ch"}
_ESPN_MIN_SCORE = 0.9
_espn_teams_cache: Optional[list[dict]] = None


def _espn_teams() -> list[dict]:
    global _espn_teams_cache
    if _espn_teams_cache is None:
        import json
        from pathlib import Path
        path = Path(__file__).resolve().parent.parent / "data" / "espn_teams.json"
        try:
            _espn_teams_cache = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _espn_teams_cache = []
    return _espn_teams_cache


@lru_cache(maxsize=None)
def _espn_fallback(raw_name: str) -> Optional[EntityProfile]:
    if not raw_name:
        return None
    from .fixtures import name_score
    scored = sorted(
        ((name_score(raw_name, [t["name"], t["short"]] if t["short"] else [t["name"]]), t)
         for t in _espn_teams()),
        key=lambda x: -x[0],
    )
    if not scored or scored[0][0] < _ESPN_MIN_SCORE:
        return None
    best, team = scored[0]
    # Deux clubs aussi plausibles l'un que l'autre : on préfère ne rien afficher
    if len(scored) > 1 and scored[1][0] >= best - 0.02 and scored[1][1]["id"] != team["id"]:
        return None
    return EntityProfile(
        canonical_name=raw_name.strip(),
        short_name=(team["short"] or team["name"]).strip(),
        entity_type="club", sport="football",
        country_code=_ESPN_COUNTRY.get(team["league"].split(".")[0]),
        logo_url=_espn_soccer(team["id"]),
    )


# ═══════════════════════════════════════════════════════
# REPLI : clubs des autres sports (data/other_teams.json)
# ═══════════════════════════════════════════════════════
# NBA/WNBA, NFL, NHL, MLB, rugby (URC, Premiership, Champions Cup, Super Rugby) : logos ESPN.
# Basket (Betclic Élite, Pro B, LFB, Euroligue), handball (LNH, LFH, EHF), volley (Ligue A),
# hockey (Ligue Magnus) et Pro D2 : logos de Wikipédia.
# Un événement de sport « sport » ne cherche que dans les sports de _OTHER_SPORTS[sport].

_OTHER_SPORTS = {
    "basket": ("basket",), "rugby": ("rugby",), "handball": ("handball",),
    "volleyball": ("volleyball",), "other": ("hockey", "baseball"), "foot_us": ("nfl",),
    # Clubs de foot absents des calendriers ESPN suivis (Ligue 2/3 FR…) : logo Wikipédia
    "football": ("football_extra",),
}
_other_teams_cache: Optional[list[dict]] = None


def _other_teams() -> list[dict]:
    global _other_teams_cache
    if _other_teams_cache is None:
        import json
        from pathlib import Path
        path = Path(__file__).resolve().parent.parent / "data" / "other_teams.json"
        try:
            _other_teams_cache = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _other_teams_cache = []
    return _other_teams_cache


@lru_cache(maxsize=None)
def _other_fallback(raw_name: str, sport: str, min_score: float = _ESPN_MIN_SCORE) -> Optional[EntityProfile]:
    sports = _OTHER_SPORTS.get(sport)
    if not raw_name or not sports:
        return None
    from .fixtures import name_score
    scored = sorted(
        ((name_score(raw_name, t["aliases"]), i, t)
         for i, t in enumerate(_other_teams()) if t["sport"] in sports),
        key=lambda x: (-x[0], x[1]),
    )
    if not scored or scored[0][0] < min_score:
        return None
    best, _, team = scored[0]
    # Deux équipes aussi plausibles l'une que l'autre : on préfère ne rien afficher
    if len(scored) > 1 and scored[1][0] >= best - 0.02 and scored[1][2]["logo"] != team["logo"]:
        return None
    return EntityProfile(
        canonical_name=raw_name.strip(),
        short_name=(team["short"] or team["name"]).strip(),
        entity_type="club", sport=sport,
        logo_url=team["logo"],
    )


_US_LOGO = re.compile(r"/(?:nba|wnba|nfl|nhl|mlb)/")


def _plain(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# Sélections nationales : correspondance exacte (jamais par sous-chaîne) → drapeau
_COUNTRY_EXTRA = {
    "nouvelle-zélande": "nz", "nouvelle zélande": "nz", "fidji": "fj", "îles fidji": "fj", "géorgie": "ge",
    "samoa": "ws", "tonga": "to", "namibie": "na", "russie": "ru", "hongrie": "hu", "tchéquie": "cz",
    "république tchèque": "cz", "slovénie": "si", "slovaquie": "sk", "bulgarie": "bg", "finlande": "fi",
    "islande": "is", "lituanie": "lt", "lettonie": "lv", "estonie": "ee", "bosnie": "ba",
    "bosnie-herzégovine": "ba", "monténégro": "me", "macédoine du nord": "mk", "israël": "il",
    "arménie": "am", "azerbaïdjan": "az", "kazakhstan": "kz", "chine": "cn", "inde": "in", "iran": "ir",
    "arabie saoudite": "sa", "qatar": "qa", "pérou": "pe", "équateur": "ec", "venezuela": "ve",
    "paraguay": "py", "bolivie": "bo", "costa rica": "cr", "jamaïque": "jm", "cuba": "cu",
    "panama": "pa", "porto rico": "pr", "république dominicaine": "do", "angola": "ao", "mali": "ml",
    "rd congo": "cd", "kenya": "ke", "zimbabwe": "zw", "madagascar": "mg", "cap-vert": "cv",
    "nouvelle zelande": "nz", "états unis": "us", "usa": "us", "royaume-uni": "gb", "grande-bretagne": "gb",
    "angleterre": "gb-eng", "pays de galles": "gb-wls", "chypre": "cy", "luxembourg": "lu",
    "malte": "mt", "moldavie": "md", "albanie": "al", "kosovo": "xk", "biélorussie": "by",
    "philippines": "ph", "indonésie": "id", "thaïlande": "th", "vietnam": "vn", "taïwan": "tw",
    "hong kong": "hk", "singapour": "sg", "malaisie": "my", "nouvelle-calédonie": "nc",
    "portugal": "pt", "brésil": "br", "chili": "cl", "kenya": "ke", "ouganda": "ug", "zambie": "zm",
    "belgique": "be", "pays-bas": "nl", "suède": "se", "norvège": "no", "danemark": "dk",
}


def _country_fallback(raw_name: str) -> Optional[EntityProfile]:
    code = _COUNTRY_EXTRA.get((raw_name or "").strip().lower())
    if not code:
        return None
    n = raw_name.strip()
    return EntityProfile(n, n, "country", "football", code, logo_url=_flag(code))


def enrich_entity(entity_dict: Optional[dict], sport: str = "football") -> Optional[dict]:
    """
    Enrich a raw entity dict (from sport_extractor) with visual metadata.

    Input:  {"name": "Paris-SG", "type": "club", "country_code": null}
    Output: {"name": "Paris Saint-Germain", "type": "club", "short": "PSG",
             "country_code": "fr", "logo_url": "https://...", "colors": [...]}
    """
    if not entity_dict:
        return entity_dict

    name = entity_dict.get("name", "")
    is_club = entity_dict.get("type") in ("club", None)
    profile = match_entity(name, sport)
    # Nom exact d'une franchise américaine que le registre rapproche d'une autre
    # (« Golden State Valkyries » ≠ Warriors) : la franchise exacte l'emporte.
    if is_club and sport in ("basket", "other", "foot_us"):
        exact = _other_fallback(name, sport, 1.0)
        if exact and _US_LOGO.search(exact.logo_url or "") and (
                profile is None or _plain(profile.canonical_name) != _plain(name)):
            profile = exact
    # « Lyon » en basket ne doit pas devenir l'OL : si le profil trouvé est d'un autre sport,
    # on préfère le club du bon sport quand on le connaît.
    if profile and is_club and sport != "football" and profile.sport != sport:
        profile = _other_fallback(name, sport) or profile
    if not profile and entity_dict.get("type") == "country":
        profile = _country_fallback(name)
    if not profile and entity_dict.get("type") in ("club", None):
        if sport == "football":
            # NFL d'abord si le nom est exactement celui d'une franchise (« Los Angeles Rams » ≠ LAFC)
            profile = (_other_fallback(name, "football", 1.0)
                       or _espn_fallback(name)
                       or _other_fallback(name, "football"))
        else:
            profile = _other_fallback(name, sport)
    if not profile and entity_dict.get("type") is None:
        profile = _country_fallback(name)
    # Profil connu mais sans logo (ex. « RC Vannes ») : on complète avec le logo du bon sport
    if profile and is_club and not profile.logo_url and sport in _OTHER_SPORTS:
        alt = _other_fallback(name, sport)
        if alt and alt.logo_url:
            from dataclasses import replace
            profile = replace(profile, logo_url=alt.logo_url)
    if not profile:
        return entity_dict  # Return as-is, no enrichment

    enriched = dict(entity_dict)
    enriched["name"] = profile.canonical_name
    enriched["short"] = profile.short_name
    enriched["country_code"] = enriched.get("country_code") or profile.country_code

    if profile.entity_type in ("club", "country"):
        enriched["logo_url"] = profile.logo_url
    if profile.entity_type == "player":
        enriched["photo_url"] = profile.photo_url

    enriched["colors"] = list(profile.colors)

    return enriched


def get_registry_stats() -> dict:
    """Return registry statistics."""
    types = {}
    sports = {}
    for p in ENTITY_REGISTRY:
        types[p.entity_type] = types.get(p.entity_type, 0) + 1
        sports[p.sport] = sports.get(p.sport, 0) + 1

    return {
        "total_entities": len(ENTITY_REGISTRY),
        "total_aliases": len(_ALIAS_INDEX),
        "by_type": types,
        "by_sport": sports,
    }
