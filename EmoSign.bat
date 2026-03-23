@echo off
title EmoSign - Sign Language Translator
cd /d "%~dp0"
chcp 65001 >nul

cls
echo.
echo   ✧･ﾟ: *✧･ﾟ:* EmoSign *:･ﾟ✧*:･ﾟ✧
echo.
echo   ███████╗███╗   ███╗ ██████╗ ███████╗██╗ ██████╗ ███╗   ██╗
echo   ██╔════╝████╗ ████║██╔═══██╗██╔════╝██║██╔════╝ ████╗  ██║
echo   █████╗  ██╔████╔██║██║   ██║███████╗██║██║  ███╗██╔██╗ ██║
echo   ██╔══╝  ██║╚██╔╝██║██║   ██║╚════██║██║██║   ██║██║╚██╗██║
echo   ███████╗██║ ╚═╝ ██║╚██████╔╝███████║██║╚██████╔╝██║ ╚████║
echo   ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
echo.
echo   ╔═══════════════════════════════════════════════════════════╗
echo   ║  Emotion ^& Sign Language Translator  v3.0.0              ║
echo   ║  Powered by MediaPipe ^| PyTorch ^| Python                ║
echo   ╚═══════════════════════════════════════════════════════════╝
echo.
echo   ⭐ ✦ ✧  *:･ﾟ✧,･:*:✧ﾟ*  ✦ ⭐
echo   🌸  Real-time sign language detection  🌸
echo   ⭐ ✦ ✧  *:･ﾟ✧,･:*:✧ﾟ*  ✦ ⭐
echo.
echo   [✓] Initializing modules...
echo   [✓] Loading AI models...
echo   [✓] Preparing interface...
echo.

python main.py

echo.
echo   ✧･ﾟ: *✧･ﾟ:* Goodbye! *:･ﾟ✧*:･ﾟ✧
pause
