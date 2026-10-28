# The Anderson and Fouad 9-bus load-flow table (C9-PUB)

Source the criteria name: P. M. Anderson and A. A. Fouad, *Power System Control and Stability*, the nine-bus
system's load-flow solution in chapter 2 (the figure of the WSCC nine-bus system with its prefault load flow).
Only a legitimate copy: a library, a university's e-book access, or the publisher (IEEE Press / Wiley).

1. Copy `case9_published.TEMPLATE.csv` to `case9_published.csv` in this folder.
2. Type each bus's voltage magnitude (pu) and angle (degrees) exactly as printed, using the book's bus numbers
   (the `wscc_bus` column); the harness maps them to MATPOWER's numbering by load.
3. Run `python3 validation/run_validation.py` in `deliverables/LV12/connection-study`. C9-PUB-VM (0.001 pu) and
   C9-PUB-VA (0.05 degree) then appear in results/validation_results.json with PASS or FAIL.
4. Write in the task note the edition and page you typed it from.
