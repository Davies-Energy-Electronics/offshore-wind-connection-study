| Check | Case | Compared against | Quantity | Tolerance | Worst deviation | Unit | Verdict |
|---|---|---|---|---|---|---|---|
| X-VM | case9 | independent solver | bus voltage magnitude | 1e-06 | 4.44e-16 | pu | PASS |
| X-VA | case9 | independent solver | bus voltage angle | 0.0001 | 8.88e-15 | degree | PASS |
| X-FLOW | case9 | independent solver | branch active and reactive flow, both ends | 0.0001 | 6.24e-13 | MW or MVAr | PASS |
| X-LOSS | case9 | independent solver | total active loss | 0.0001 | 2.13e-14 | MW | PASS |
| D-BUNDLED | case9 | pandapower bundled case | bus voltage magnitude and angle after solving | 1e-06 pu, 0.0001 deg | 0.389 | degree | FAIL |
| C9-CHOW-QG | case9 | case file generator table (Chow 1982 via MATPOWER) | generator reactive output | 0.15 | 0.114 | MVAr | INFORMATIONAL |
| C9-CHOW-PG1 | case9 | case file generator table (Chow 1982 via MATPOWER) | slack active output | 0.1 | 0.659 | MW | INFORMATIONAL |
| C9-PUB-VM | case9 | published solution table | bus voltage magnitude | 0.001 | 0.000369 | pu | PASS |
| C9-PUB-VA | case9 | published solution table | bus voltage angle | 0.05 | 0.0352 | degree | PASS |
| X-VM | case14 | independent solver | bus voltage magnitude | 1e-06 | 4.44e-16 | pu | PASS |
| X-VA | case14 | independent solver | bus voltage angle | 0.0001 | 2.66e-14 | degree | PASS |
| X-FLOW | case14 | independent solver | branch active and reactive flow, both ends | 0.0001 | 8.42e-13 | MW or MVAr | PASS |
| X-LOSS | case14 | independent solver | total active loss | 0.0001 | 1.05e-13 | MW | PASS |
| D-BUNDLED | case14 | pandapower bundled case | bus voltage magnitude and angle after solving | 1e-06 pu, 0.0001 deg | 2.13e-14 | degree | PASS |
| C14-PUB-VM | case14 | published | bus voltage magnitude | 0.001 | 0.00133 | pu | FAIL |
| C14-PUB-VA | case14 | published | bus voltage angle | 0.05 | 0.0171 | degree | PASS |
| C14-PUB-QG | case14 | published | generator reactive output | 0.1 | 1.68 | MVAr | FAIL |
| C14-PUB-PG | case14 | published | slack generator active output | 0.1 | 0.00673 | MW | PASS |
| C14-PUB-LOSS | case14 | published | total active loss, sum of Pg minus sum of Pd | 0.1 | 0.00673 | MW | PASS |
