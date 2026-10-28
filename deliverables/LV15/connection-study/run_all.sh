#!/bin/sh
# Rebuild every LV15 result from a clean shell: revision C (the step) and revision D (the final base design).
# Needs LV13 and LV14 in the folders beside this one.
set -e
cd "$(dirname "$0")/model"
python3 n1.py > ../results/n1.txt
python3 checks.py > ../results/checks.txt 2>/dev/null
python3 sld.py > /dev/null
LV15_REV=D python3 n1.py > ../results/n1_D.txt
python3 checks_d.py > ../results/checks_D.txt 2>/dev/null
LV15_REV=D python3 sld.py > /dev/null
python3 report.py > /dev/null
cd ..
python3 -m pytest -q tests | tail -1 > results/tests.txt
cat results/tests.txt
