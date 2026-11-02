# 08-bildiri — 2026-11-03 fix evidence

The SSS answers were 13px `meta` grey under 16px questions and read as fine print. They are
16px `body` now, with a 72px row pitch (was 60) and the rule 16px under the answer's ink; the
board grew 2568 → 2632 and the footer docks to the last rule.

`fix-faq-1x.png` is the 1:1 crop of the Q/A block (board y 1920-2220): four one-line answers,
no wrap, no collision with the rules, questions still carry the weight difference.
