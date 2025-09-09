@echo off
echo Adding all files and updating repository...
git add .
git commit --amend -m "Flutter Development Environment Setup Tool - Complete executable with user instructions and PyInstaller packaging"
git push origin main --force
echo Done! Updated repository with .exe file.
pause
