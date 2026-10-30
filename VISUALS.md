# CINDERSPIRE visual overhaul

100 concrete graphical improvements, all implemented in `cinderspire/ui.py`
and the new `cinderspire/visuals.py`.

## Palette and chrome

1. Expanded the 256-colour palette with 16 new hues (steel, rust, bone,
   crimson, lime, violet, ice, sand, blood, moss, brass, coal, parchment,
   arcane, poison and holy).
2. Added a primary accent per class and used it for borders, panels and rules.
3. Added a secondary accent per class for alternating header highlights.
4. Added a class emblem glyph used on cards, minions and the class picker.
5. Replaced the flat logo with a per-character gradient wordmark.
6. Added a flame glyph beside the wordmark.
7. Screen subtitles are now reverse-video chips in the class colour.
8. Section rules are gradient lines with a central star.
9. The header shows floor progress as filled/empty pips.
10. Daily and Ascension runs get explicit header badges.

## Header and status

11. Boss floors show a skull and the keeper's name in the header.
12. The HP rail starts with a heart glyph.
13. The HP bar is segmented with quarter ticks.
14. HP colour changes with health: green, gold, then red.
15. HP numbers are bold and switch to red when low.
16. Gold has a coin glyph that slowly cycles colour.
17. Gaining gold flashes the amount white.
18. Relics appear as compact tag chips.
19. Overflowing relic tags collapse into a `+N` counter.
20. The footer hint sits on a reverse-video band with an accent arrow.

## Depth and layout

21. Regular panels use rounded corners.
22. Emphasis panels use double borders.
23. Panels cast a stipple drop shadow.
24. Overlays cast a larger drop shadow.
25. Overlays have gold corner accents.
26. Selected list rows use a solid accent bar instead of plain reverse video.
27. List rows alternate between normal and faint zebra shading.
28. The footer arrow picks up the current class accent.
29. Damaged minions get a bright flash border.
30. Damaged minions shake horizontally for a few frames.

## Title and class select

31. The title screen has drifting ember particles.
32. The title screen has corner vignette brackets.
33. The logo uses a five-colour gradient across the banner font.
34. Flame glyphs flank both sides of the logo.
35. All five class emblems are shown above the menu.
36. The selected menu entry gets a reverse-video band and arrows.
37. The best run is shown in a framed stats plaque.
38. A rotating gameplay tip is shown at the bottom.
39. The version is shown as a small badge.
40. The class picker uses emblem panels with class-coloured borders.

## Class select and map

41. Class panels show the live card count for that class.
42. Class descriptions were rewritten for board combat.
43. The selected class gets a trailing arrow and accent border.
44. Map nodes use type-specific icons (sword, skull, ?, fire, coin, chest).
45. Visited nodes show a green tick.
46. The current node is shown in reverse video.
47. Available nodes pulse between accent and normal.
48. The selected node is flanked by arrows on both sides.
49. The travelled route is redrawn in ember colours.
50. A dotted vertical guide runs behind the map route.

## Map and enemy board

51. The boss node has a crown glyph.
52. The boss name is printed under the crown.
53. The map side panel is a rounded, shadowed panel.
54. Relics on the map are tag chips with names.
55. Potions on the map use flask/heart icons.
56. The map legend uses the same node icons as the route.
57. The enemy hero plaque shows an initial emblem, name, HP, mana and hand.
58. Enemy HP uses the same segmented colour-coded bar as the player.
59. Enemy mana is drawn as crystal pips.
60. Enemy hand size is shown as a compact `Hn` badge.

## Combat board

61. The enemy hero is highlighted when targeted or dragged onto.
62. Faint lane rails separate the five board slots.
63. Empty slots use dashed interiors and a centred `empty` label.
64. Minions show a sword glyph before Attack.
65. Minions show a heart glyph before Health.
66. Minion Health changes colour as it drops.
67. Minions show their keyword icons in the stat row.
68. Minion names are prefixed with a class/faction emblem.
69. Ready minions get a green arrow.
70. Divine Shield minions get a gold star.

## Combat feedback

71. Selected minions pulse between white and gold double borders.
72. Targeted minions get crosshair corners and a red double border.
73. Damage numbers float over the damaged minion.
74. Healing numbers float in green.
75. Divine Shield absorption shows a gold `SHIELD` popup.
76. A dotted attack arrow links the selected attacker to its target.
77. A red `LETHAL` badge appears when the board can kill the enemy hero.
78. The combo chain is shown as an orange `COMBO xN` badge.
79. Cards with an active combo show a `C` corner badge.
80. Turn changes display an animated `YOUR TURN` / `ENEMY TURN` banner.

## Combat and cards

81. Enemy turns show a blinking `thinking...` indicator.
82. END TURN dims while the enemy is acting.
83. Player mana is drawn as filled/empty diamond pips.
84. The turn number is a reverse-video chip.
85. Deck and graveyard counts get their own header labels.
86. Card cost is drawn as a gem on the card's top border.
87. Cards show a sword or sparkle type glyph.
88. Card frames use the class accent colour.
89. Upgraded cards show a cyan `+N` marker.
90. Card keyword strips use icons instead of raw flag names.

## Cards and shop

91. Card rarity is shown as a pip strip in the bottom corner.
92. The selected hand card shows a gold arrow on its frame.
93. The full-card overlay shows cost, stat gems and keyword labels.
94. The full-card overlay highlights the combo line.
95. Dragging shows the hovered enemy's name, stats and keywords in the hint.
96. The shop has a striped awning and a title chip.
97. Shop cards/relics/potions use type icons.
98. Prices use a coin glyph and right-aligned amounts.
99. Purchased rows are stamped `[SOLD]`.
100. The selected shop row gets an accent underline and the shopkeeper quote
     closes the screen.

## Also polished

- Victory screen: confetti, gradient banner, stat progress bars and framed
  action chips.
- Defeat screen: falling embers, red gradient banner and skull divider.
- Reward screen: victory stars, card fan with a raised centre card, rarity
  sparkles, selection stars, coin stacks and a SKIP chip.
- Campfire: animated three-colour fire, rising sparks, framed rest options and
  a live HP preview.
- Events: themed emblem, numbered choice chips, reverse-video selected row and
  coloured effect badges.
- Treasure: chest art with timed sparkles and reverse-video reward chips.
- Interlude: ember-boon cards with sparkle accents.
- Codex: tab chips, per-tab progress bar, zebra rows, seen dots, achievement
  ticks and keyword glyphs in the detail pane.
- Deck/picker: type icons, zebra rows, upgrade stars, column dividers and an
  accent selection bar.
- History: zebra rows, WIN/DIED chips, win stars and score column.
- Potions: flask icons next to each bottle.
- Combat log: coloured bullets and zebra rows.
- Pause: menu icons and a reverse-video selected row.
- Settings: coloured ON/OFF toggle chips.
- Help: icon rows, rewritten board-combat rules and two rows of keycap chips.
- Seed entry: blinking cursor, star header and keycap hints.
- Resize screen: framed art and the exact current/needed terminal size.
- Heart screen: side flame glyphs and red/gold ember accents.
