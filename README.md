# JFE v1.0 RC5 — RiderStats + Line Qualification

Preserves RC4 Identity, Entry, Result and RC3 Odds guards.

RiderStats READY requires every Entry rider to be row-bound and to have:
score, style, win rate, 2-place rate, 3-place rate.
Rates must satisfy win <= 2-place <= 3-place.

Line parsing is deliberately split:
- QUALIFIED_ORDER: all entrants are found exactly once in the published lineup order.
- group_boundaries_qualified remains false until structural group separators are independently proven.
This prevents JFE from inventing line boundaries from whitespace.

Reference 大宮10R:
line order 1,4,6,2,3,7,5.
Expected scores:
1 100.96 / 2 96.70 / 3 101.20 / 4 97.53 / 5 104.20 / 6 94.82 / 7 100.58.
