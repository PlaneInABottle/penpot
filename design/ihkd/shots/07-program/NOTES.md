# 07-program — 2026-11-03 fix evidence

`sess card 2` and `sess card 8` were 128px tall with a 40px title→meta joint while their
row-mates read 104px / 16px (the build estimated two title lines, the render used one).
`lib.fitCards` now re-settles a card's meta on the title's measured ink before sizing the
card, so every card is its content.

`fix-sess-cards-1x.png` is the 1:1 crop of the two affected rows (board y 900-1400): both
repaired cards now match their neighbours' height and joint, and the accent bar keeps its
16px padding. Live geometry after the rebuild: all 19 `sess card *` boards have a 16px ink
joint; 2 and 8 are 104px.
