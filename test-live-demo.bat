@echo off
title NekoAFK Live Experience Demo
echo ====================================================
echo  Starting NekoAFK Mascot Live Demo...
echo  Watch your desktop mascot (Nova / Kuro / Neko)!
echo ====================================================
cd /d "%~dp0"
node integrations\antigravity\demo-live.mjs
pause
