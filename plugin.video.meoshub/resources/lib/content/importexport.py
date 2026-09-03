# -*- coding: utf-8 -*-
"""Import content-source lists from CSV/XLSX, and export integrations,
scrapers and favorites for backup or sharing.

Import file format (first row = header, columns in any order):
    title, category, type, value
  - category: movies | tvshows | networks | sports | ppv | livetv
  - type:     stream  (value = a direct playable URL)
              addon   (value = an installed add-on id to integrate)
  - value:    the URL or add-on id described above

Only a single-sheet, simple XLSX layout is supported (no formulas/styles) -
this keeps MEOS Hub free of any third-party spreadsheet library dependency.
"""
import csv
import io
import os
import xml.etree.ElementTree as ET
import zipfile

from resources.lib.content import favorites as favorites_content
from resources.lib.integrations import manager as integrations_manager
from resources.lib.scrapers import manager as scrapers_manager
from resources.lib.utils import kodi

XLSX_NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def _read_csv_rows(file_path):
    with open(file_path, 'r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        return [{(k or '').strip().lower(): (v or '').strip() for k, v in row.items()} for row in reader]


def _read_xlsx_rows(file_path):
    with zipfile.ZipFile(file_path) as archive:
        shared_strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            tree = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            for si in tree.findall('m:si', XLSX_NS):
                text = ''.join(t.text or '' for t in si.findall('.//m:t', XLSX_NS))
                shared_strings.append(text)

        sheet_tree = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        rows = []
        for row in sheet_tree.findall('.//m:row', XLSX_NS):
            values = []
            for cell in row.findall('m:c', XLSX_NS):
                value_node = cell.find('m:v', XLSX_NS)
                text = value_node.text if value_node is not None else ''
                if cell.get('t') == 's' and text:
                    text = shared_strings[int(text)]
                values.append(text)
            rows.append(values)

    if not rows:
        return []
    header = [(h or '').strip().lower() for h in rows[0]]
    parsed = []
    for row in rows[1:]:
        entry = {}
        for index, key in enumerate(header):
            entry[key] = row[index] if index < len(row) else ''
        parsed.append(entry)
    return parsed


def import_sources(file_path):
    """Import a CSV or XLSX file of content sources. Returns (added, skipped)."""
    if not file_path or not os.path.exists(file_path):
        return 0, 0

    if file_path.lower().endswith('.xlsx'):
        rows = _read_xlsx_rows(file_path)
    else:
        rows = _read_csv_rows(file_path)

    added = 0
    skipped = 0
    for row in rows:
        row_type = row.get('type', '').strip().lower()
        value = row.get('value', '').strip()
        title = row.get('title', '').strip()
        if row_type == 'addon' and value:
            if integrations_manager.add_custom_integration(value, title or value):
                added += 1
            else:
                skipped += 1
        elif row_type == 'stream' and value:
            item = {
                'title': title or value,
                'url': value,
                'plot': '',
                'poster': '',
                'year': '',
                'source': 'import',
            }
            if favorites_content.add_favorite(item):
                added += 1
            else:
                skipped += 1
        else:
            skipped += 1
    return added, skipped


def _write_json(folder, filename, data):
    import json
    directory = kodi.ensure_dir(folder)
    path = os.path.join(directory, filename)
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(json.dumps(data, indent=2, ensure_ascii=False))
    return path


def export_integrations(folder):
    custom = integrations_manager.list_custom_integrations()
    return _write_json(folder, 'meoshub_integrations.json', custom)


def export_scrapers(folder):
    custom = scrapers_manager.list_custom_scrapers()
    return _write_json(folder, 'meoshub_scrapers.json', custom)


def export_favorites(folder):
    favorites = favorites_content.list_favorites()
    return _write_json(folder, 'meoshub_favorites.json', favorites)
