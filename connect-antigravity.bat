@echo off
title NekoAFK Antigravity Bridge
echo ====================================================
echo  Connecting Antigravity to NekoAFK Companion...
echo ====================================================
cd /d "%~dp0"
node integrations\antigravity\nekoafk-antigravity.mjs %*
pause
