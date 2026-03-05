@echo off
cd /d C:\projects\PPW
echo === git status ===
git status --short
echo === git log (last 3) ===
git log --oneline -3
echo === tags ===
git tag
echo === remote ===
git remote -v

