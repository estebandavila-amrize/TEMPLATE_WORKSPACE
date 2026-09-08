#!/usr/bin/env python3
"""
snow_read_attachment.py
-----------------------
Lista y extrae el contenido de los adjuntos de un registro de ServiceNow
usando la Table API + Attachment API.

Especializado para extraer texto de archivos .docx (Word), pero descarga
cualquier tipo de adjunto al directorio de salida.

CREDENCIALES (nunca en el codigo):
  Se leen de variables de entorno:
    SNOW_INSTANCE   ej. https://oneservicena.service-now.com
    SNOW_USER       usuario (basic auth)
    SNOW_PASS       contrasena

USO:
  # Definir credenciales una vez en la sesion de PowerShell:
  #   $env:SNOW_INSTANCE = "https://oneservicena.service-now.com"
  #   $env:SNOW_USER     = "kiro_integration"
  #   $env:SNOW_PASS     = "********"

  # Listar adjuntos de un incident:
  python snow_read_attachment.py --number INC08340528 --list

  # Extraer texto de todos los .docx del incident:
  python snow_read_attachment.py --number INC08340528 --extract-docx

  # Descargar TODOS los adjuntos a ./downloads:
  python snow_read_attachment.py --number INC08340528 --download-all

  # Trabajar contra otra tabla (default: incident):
  python snow_read_attachment.py --table change_request --number CHG0435576 --list
"""

import argparse
import os
import sys
import zipfile
import io
import re
from xml.etree import ElementTree as ET

try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    sys.exit("ERROR: falta 'requests'. Instala con: python -m pip install requests")


# --- Word namespace para leer document.xml ---
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def get_env_config():
    """Lee credenciales de variables de entorno. Falla claro si faltan."""
    instance = os.environ.get("SNOW_INSTANCE", "").rstrip("/")
    user = os.environ.get("SNOW_USER", "")
    password = os.environ.get("SNOW_PASS", "")
    missing = [k for k, v in
               (("SNOW_INSTANCE", instance), ("SNOW_USER", user), ("SNOW_PASS", password))
               if not v]
    if missing:
        sys.exit(
            "ERROR: faltan variables de entorno: " + ", ".join(missing) + "\n"
            "Definelas antes de ejecutar. En PowerShell:\n"
            '  $env:SNOW_INSTANCE = "https://oneservicena.service-now.com"\n'
            '  $env:SNOW_USER     = "tu_usuario"\n'
            '  $env:SNOW_PASS     = "tu_clave"'
        )
    return instance, HTTPBasicAuth(user, password)


def resolve_record_sys_id(session, instance, auth, table, number):
    """Obtiene el sys_id de un registro a partir de su numero (ej INC..., CHG...)."""
    url = f"{instance}/api/now/table/{table}"
    params = {"sysparm_query": f"number={number}", "sysparm_fields": "sys_id,number",
              "sysparm_limit": 1}
    r = session.get(url, auth=auth, params=params,
                    headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    result = r.json().get("result", [])
    if not result:
        sys.exit(f"ERROR: no se encontro el registro {number} en la tabla {table}.")
    return result[0]["sys_id"]


def list_attachments(session, instance, auth, table, record_sys_id):
    """Devuelve la lista de adjuntos (metadatos) de un registro."""
    url = f"{instance}/api/now/attachment"
    params = {
        "sysparm_query": f"table_name={table}^table_sys_id={record_sys_id}",
        "sysparm_fields": "sys_id,file_name,content_type,size_bytes,sys_created_on,sys_created_by",
    }
    r = session.get(url, auth=auth, params=params,
                    headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json().get("result", [])


def download_attachment_bytes(session, instance, auth, attachment_sys_id):
    """Descarga el binario de un adjunto por su sys_id."""
    url = f"{instance}/api/now/attachment/{attachment_sys_id}/file"
    r = session.get(url, auth=auth, timeout=60)
    r.raise_for_status()
    return r.content


def extract_docx_text(data: bytes) -> str:
    """Extrae el texto de un .docx (ZIP con word/document.xml) usando solo stdlib."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return "[No es un .docx valido / archivo corrupto]"

    parts = []
    # document.xml principal + headers/footers si existen
    targets = [n for n in zf.namelist()
               if n == "word/document.xml"
               or re.match(r"word/(header|footer)\d*\.xml$", n)]
    for name in targets:
        try:
            xml_bytes = zf.read(name)
            root = ET.fromstring(xml_bytes)
        except (KeyError, ET.ParseError):
            continue
        # Cada parrafo <w:p>; texto en <w:t>; saltos <w:br>/<w:tab>
        for para in root.iter(f"{{{W_NS}}}p"):
            texts = []
            for node in para.iter():
                tag = node.tag.split("}")[-1]
                if tag == "t" and node.text:
                    texts.append(node.text)
                elif tag == "tab":
                    texts.append("\t")
                elif tag == "br":
                    texts.append("\n")
            line = "".join(texts).strip()
            if line:
                parts.append(line)
    return "\n".join(parts) if parts else "[El documento no contiene texto extraible]"


def human_size(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n/1:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TB"


def main():
    ap = argparse.ArgumentParser(description="Lee/extrae adjuntos de ServiceNow.")
    ap.add_argument("--table", default="incident", help="Tabla (default: incident)")
    ap.add_argument("--number", required=True, help="Numero del registro (INC..., CHG...)")
    ap.add_argument("--list", action="store_true", help="Solo listar los adjuntos")
    ap.add_argument("--extract-docx", action="store_true",
                    help="Extraer y mostrar el texto de los adjuntos .docx")
    ap.add_argument("--download-all", action="store_true",
                    help="Descargar todos los adjuntos al directorio de salida")
    ap.add_argument("--outdir", default="downloads", help="Directorio de descarga")
    args = ap.parse_args()

    instance, auth = get_env_config()
    session = requests.Session()

    print(f"[i] Instancia: {instance}")
    print(f"[i] Resolviendo {args.number} en tabla {args.table} ...")
    record_sys_id = resolve_record_sys_id(session, instance, auth, args.table, args.number)
    print(f"[i] sys_id: {record_sys_id}")

    attachments = list_attachments(session, instance, auth, args.table, record_sys_id)
    if not attachments:
        print("[!] El registro no tiene adjuntos.")
        return
    print(f"[i] {len(attachments)} adjunto(s) encontrado(s):\n")
    for i, a in enumerate(attachments, 1):
        print(f"  {i}. {a['file_name']}")
        print(f"     tipo={a.get('content_type')}  tam={human_size(a.get('size_bytes'))}"
              f"  por={a.get('sys_created_by')}  {a.get('sys_created_on')}")
    print()

    if args.list and not (args.extract_docx or args.download_all):
        return

    if args.download_all:
        os.makedirs(args.outdir, exist_ok=True)

    for a in attachments:
        name = a["file_name"]
        is_docx = name.lower().endswith(".docx") or \
            "wordprocessingml.document" in (a.get("content_type") or "")

        need_bytes = args.download_all or (args.extract_docx and is_docx)
        if not need_bytes:
            continue

        data = download_attachment_bytes(session, instance, auth, a["sys_id"])

        if args.download_all:
            safe = re.sub(r'[<>:"/\\|?*]', "_", name)
            path = os.path.join(args.outdir, safe)
            with open(path, "wb") as f:
                f.write(data)
            print(f"[+] Descargado: {path} ({human_size(len(data))})")

        if args.extract_docx and is_docx:
            print("\n" + "=" * 70)
            print(f"CONTENIDO EXTRAIDO: {name}")
            print("=" * 70)
            print(extract_docx_text(data))
            print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
