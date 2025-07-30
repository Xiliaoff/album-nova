@echo off
title Serveur Concours Photo
cd /d "%~dp0"

:: Vérifie si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo Python n'est pas installé ou n'est pas dans le PATH.
    pause
    exit /b
)

:: Lance le serveur Python
echo Lancement du serveur photo sur http://localhost:2010 ...
python serveur_photo.py

pause
