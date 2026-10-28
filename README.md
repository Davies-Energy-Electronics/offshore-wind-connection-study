# Offshore wind connection study (400 MW, 220 kV export)

A self-directed power-systems study in four blocks, written so that every number reruns from a clean shell.

| Block | Question | Folder |
|---|---|---|
| LV12 | Does an independent Newton-Raphson solver agree with pandapower, and with a published textbook case? | `deliverables/LV12/` |
| LV13 | Do four operating cases of the 400 MW connection solve inside limits? | `deliverables/LV13/` |
| LV14 | What cable sizes, fault levels and overcurrent settings does it need? | `deliverables/LV14/` |
| LV15 | Which single outages can it ride through, and what does it curtail to? | `deliverables/LV15/` |

Each block has a `RESULT.md` with its answer, and the code and tests in `connection-study/`. The report covering all four is `deliverables/LV15/connection-study/results/LV15_connection_study_report.pdf`, and the single-line diagram is `deliverables/LV15/connection-study/results/sld.png`.

**Read this first.** Every input is either a design choice or a typical-order value written from general knowledge, marked ASSUMED. No standard (IEC 60287, IEC 60909, IEC 60255), grid code or SQSS was read, and nothing here claims compliance. It is not professional experience and has not been reviewed by a chartered engineer. What it shows is the method: criteria committed before the first run, independent checks, and every failure reported.

The LV12 nine-bus case is also compared with the published solution in Anderson and Fouad, *Power System Control and Stability*, 2nd edition, Fig. 2.19 (`inputs/LV12/case9_published.csv`).

## Run it

Python 3.10 or later.

    pip install -r requirements.txt
    cd deliverables/LV12/connection-study && python casefiles/fetch_data.py && python -m pytest -q && cd ../../..
    cd deliverables/LV13/connection-study && python -m pytest -q && cd ../../..
    cd deliverables/LV14/connection-study && sh run_all.sh && python -m pytest -q && cd ../../..
    cd deliverables/LV15/connection-study && sh run_all.sh && python -m pytest -q && cd ../../..

`fetch_data.py` downloads the MATPOWER 9-bus and 14-bus case files and checks them against pinned SHA-256 hashes.

## How it was made

Built with AI assistance (Claude, by Anthropic) to my specification. I set the questions and the decisions recorded in each block, and reviewed the results.

## Licence

GPL-3.0, see LICENSE.
