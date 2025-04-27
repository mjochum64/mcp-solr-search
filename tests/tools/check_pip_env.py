#!/usr/bin/env python3
"""
Diagnoseskript zur Überprüfung der Python- und pip-Umgebungskonfiguration.

Dieses Skript liefert Informationen über die aktive Python- und pip-Installation,
um Probleme mit virtuellen Umgebungen zu diagnostizieren.
"""
import os
import sys
import site
import subprocess
from pathlib import Path

def run_command(cmd):
    """
    Führt einen Shell-Befehl aus und gibt die Ausgabe zurück.
    
    Args:
        cmd (str): Der auszuführende Befehl.
    
    Returns:
        str: Die Ausgabe des Befehls.
    """
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Fehler: {e.stderr.strip()}"

def check_environment():
    """
    Überprüft die Python- und pip-Umgebungsdetails.
    
    Returns:
        None: Gibt Informationen auf der Konsole aus.
    """
    # Python-Pfad und Version
    print(f"Python-Executable: {sys.executable}")
    print(f"Python-Version: {sys.version}")
    
    # Virtuelle Umgebung
    venv = os.environ.get("VIRTUAL_ENV")
    print(f"Aktive virtuelle Umgebung: {venv or 'Keine'}")
    
    # pip-Informationen
    pip_location = run_command("which pip")
    pip_version = run_command("pip --version")
    
    print(f"pip-Pfad: {pip_location}")
    print(f"pip-Version: {pip_version}")
    
    # sys.path überprüfen
    print("\nPython-Suchpfade (sys.path):")
    for path in sys.path:
        print(f"  - {path}")
    
    # Site-Packages
    print("\nSite-packages Verzeichnisse:")
    for path in site.getsitepackages():
        print(f"  - {path}")
    
    # PATH-Variable
    print("\nPATH-Variable:")
    path_entries = os.environ.get("PATH", "").split(":")
    for entry in path_entries:
        print(f"  - {entry}")
    
    # Prüfen, ob pip in virtueller Umgebung vorhanden ist
    if venv:
        venv_pip = os.path.join(venv, "bin", "pip")
        if os.path.exists(venv_pip):
            print(f"\nDas virtuelle Umgebungs-pip existiert hier: {venv_pip}")
            if pip_location != venv_pip:
                print("WARNUNG: Das System nutzt nicht das pip aus der virtuellen Umgebung!")
                print(f"Tipp: Verwenden Sie '{venv_pip}' direkt oder korrigieren Sie die PATH-Variable.")
        else:
            print(f"\nWARNUNG: Kein pip in der virtuellen Umgebung gefunden: {venv_pip}")

if __name__ == "__main__":
    print("=== Python/pip Umgebungsdiagnose ===")
    check_environment()
    print("===================================")