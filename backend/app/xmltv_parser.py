"""
SportZap — XMLTV Parser

Parses XMLTV XML files (from xmltvfr.fr or any standard XMLTV source)
into structured Python dicts for downstream processing.

XMLTV spec: each <programme> has:
  - start/stop attrs: "YYYYMMDDHHmmss +TZ"
  - channel attr: references a <channel id="...">
  - <title>, <sub-title>, <desc>, <category> children
"""
from __future__ import annotations

import gzip
import logging
import zipfile
from datetime import datetime, timezone, timedelta
from io import BytesIO
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


def parse_xmltv_datetime(raw: str) -> datetime:
    """Parse XMLTV datetime string like '20260329210000 +0100' into aware datetime."""
    raw = raw.strip()
    # Format: YYYYMMDDHHmmss +HHMM (or -HHMM)
    try:
        # Split timestamp and timezone
        parts = raw.split()
        dt_str = parts[0]
        tz_str = parts[1] if len(parts) > 1 else "+0000"

        dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S")

        # Parse timezone offset
        tz_sign = 1 if tz_str[0] == "+" else -1
        tz_hours = int(tz_str[1:3])
        tz_mins = int(tz_str[3:5])
        tz_offset = timedelta(hours=tz_hours * tz_sign, minutes=tz_mins * tz_sign)

        return dt.replace(tzinfo=timezone(tz_offset))
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse XMLTV datetime '{raw}': {e}")
        return datetime.now(timezone.utc)


def _text(el: Optional[ET.Element]) -> Optional[str]:
    """Safely extract text from an XML element."""
    return el.text.strip() if el is not None and el.text else None


def _load_xml_tree(source: str | Path | bytes) -> ET.Element:
    """
    Load an ElementTree root from various source types:
    - file path (.xml, .gz, .zip)
    - raw bytes
    - URL string (caller should fetch first)
    """
    if isinstance(source, bytes):
        # Try gzip first, then raw XML
        try:
            decompressed = gzip.decompress(source)
            return ET.fromstring(decompressed)
        except gzip.BadGzipFile:
            pass
        # Try zip
        try:
            with zipfile.ZipFile(BytesIO(source)) as zf:
                xml_files = [f for f in zf.namelist() if f.endswith(".xml")]
                if xml_files:
                    with zf.open(xml_files[0]) as f:
                        return ET.parse(f).getroot()
        except zipfile.BadZipFile:
            pass
        # Raw XML bytes
        return ET.fromstring(source)

    path = Path(source)
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as f:
            return ET.parse(f).getroot()
    elif path.suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            xml_files = [f for f in zf.namelist() if f.endswith(".xml")]
            if not xml_files:
                raise ValueError(f"No .xml file found in {path}")
            with zf.open(xml_files[0]) as f:
                return ET.parse(f).getroot()
    else:
        return ET.parse(path).getroot()


def parse_channels(root: ET.Element) -> dict[str, dict]:
    """
    Extract channel definitions from XMLTV root.

    Returns: { channel_id: { "name": ..., "icon_url": ... } }
    """
    channels = {}
    for ch_el in root.findall("channel"):
        ch_id = ch_el.get("id", "")
        name_el = ch_el.find("display-name")
        icon_el = ch_el.find("icon")

        channels[ch_id] = {
            "id": ch_id,
            "name": _text(name_el) or ch_id,
            "icon_url": icon_el.get("src") if icon_el is not None else None,
        }
    return channels


def parse_programmes(root: ET.Element) -> list[dict]:
    """
    Extract all programmes from XMLTV root.

    Returns list of raw programme dicts with:
      - channel_id, start, end (datetime)
      - title, subtitle, description
      - categories (list[str])
    """
    programmes = []

    for prog_el in root.findall("programme"):
        start_raw = prog_el.get("start", "")
        stop_raw = prog_el.get("stop", "")
        channel_id = prog_el.get("channel", "")

        # Parse times
        start = parse_xmltv_datetime(start_raw)
        end = parse_xmltv_datetime(stop_raw) if stop_raw else None

        # Text fields
        title = _text(prog_el.find("title"))
        subtitle = _text(prog_el.find("sub-title"))
        desc = _text(prog_el.find("desc"))

        # Categories (can have multiple)
        categories = []
        for cat_el in prog_el.findall("category"):
            cat_text = _text(cat_el)
            if cat_text:
                categories.append(cat_text.lower())

        if not title:
            continue

        programmes.append({
            "channel_id": channel_id,
            "start": start,
            "end": end,
            "title": title,
            "subtitle": subtitle,
            "description": desc,
            "categories": categories,
        })

    return programmes


def parse_xmltv(source: str | Path | bytes) -> tuple[dict[str, dict], list[dict]]:
    """
    Full parse: load source → extract channels + programmes.

    Args:
        source: file path (.xml/.gz/.zip), raw bytes, or string path

    Returns:
        (channels_dict, programmes_list)
    """
    logger.info(f"Parsing XMLTV source: {source if isinstance(source, (str, Path)) else '<bytes>'}")
    root = _load_xml_tree(source)

    channels = parse_channels(root)
    logger.info(f"  → {len(channels)} channels found")

    programmes = parse_programmes(root)
    logger.info(f"  → {len(programmes)} programmes found")

    return channels, programmes
