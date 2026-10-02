# JFE IC1.4 DEV-B59.4.3

- Correct trifecta BT5 semantic axes: table=first, column=second, row=third.
- Add fail-closed same-container trifecta popularity cross-check.
- Trifecta cannot become AVAILABLE unless explicit popularity rows overlap and match the 210-coordinate market with zero mismatches.
- Preserve B59.4.2 wide odds lower-bound fix (1.0 is valid).
- Regression target: Beppu 2026-09-25 6R must map 4-5-2 to 157.9 and 4-2-5 to 109.6.
