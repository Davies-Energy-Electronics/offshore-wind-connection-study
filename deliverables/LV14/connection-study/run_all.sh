#!/bin/sh
# Rebuild every LV14 result from a clean shell. Needs the LV13 model (deliverables/LV13) beside this folder.
set -e
cd "$(dirname "$0")/model"
python3 revb.py > /dev/null
python3 size.py > ../results/cable_sizing.txt
python3 worked.py > /dev/null
python3 faults.py > ../results/faults.txt
python3 grading.py > ../results/grading.txt
python3 whatif_w2.py > ../results/whatif_w2.txt
cd ..
python3 -m pytest -q tests | tail -3 > results/tests.txt
cat results/tests.txt
