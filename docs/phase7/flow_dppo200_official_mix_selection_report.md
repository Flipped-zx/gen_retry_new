# Flow-DPPO Geneval2 200-Prompt Selection

## Policy

- Selection method: `flow_dppo_geneval2_official_atom_balanced_deterministic_v1`
- Source: `Tencent-Hunyuan/UniRL@e1a814ff9de6de644b093c6ed0106869c1881e53`
- Dataset: `datasets/geneval2/synthetic/train.jsonl`
- Source rows: 20000
- Rows where `atom_count != len(vqa_list)`: 6007
- Official 800-row Geneval2 test set remains held out.
- Held-out boundary: exact prompt overlaps excluded=0; semantic-family overlaps excluded=9650.
- Local reporting tier mix (not official labels): easy=75, hard=50, medium=75
- Atom-count mix: 3=25, 4=25, 5=25, 6=25, 7=25, 8=25, 9=25, 10=25
- This mirrors the official 800-row atom-count distribution: 100 rows for each atom_count from 3 through 10.
- Prior selected source rows excluded: 20.
- Selection is deterministic and uses metadata/semantic diversity only; no live image result is used.

## Coverage

- Selected prompts: 200
- Distinct entities: 40
- Relation/action phrases: behind, chasing, in front of, jumping over, on top of, playing with, to the left of, to the right of, under
- Constraint atoms: attribute=304, count=459, object=459, position=175, verb=22
- Official-scaled skill soft targets: attribute=303.5, count=506.25, object=506.25, position=165.5, verb=21.5
- Selected minus soft target: attribute=+0.5, count=-47.25, object=-47.25, position=+9.5, verb=+0.5
- Actual VQA-count histogram: 4=36, 5=6, 6=53, 7=10, 8=38, 9=17, 10=40

## Selected Rows

| Rank | Tier | Source line | Atoms/VQAs | Prompt |
|---:|---|---:|---:|---|
| 1 | easy | 69 | 3/4 | a blue spotted kangaroo |
| 2 | easy | 2680 | 4/6 | a koala and a purple pink turtle |
| 3 | easy | 19207 | 5/8 | a turtle in front of a trumpet on top of a pig |
| 4 | medium | 457 | 6/7 | seven green pink horses to the right of a cookie |
| 5 | medium | 1075 | 7/9 | a lion playing with five dogs under a yellow cow |
| 6 | medium | 1806 | 8/10 | a mushroom to the left of a spotted candle behind five glass sheeps |
| 7 | hard | 242 | 9/10 | five plastic zebras in front of a wooden violin in front of five donuts |
| 8 | hard | 56 | 10/10 | five green raccoons on top of four trucks in front of six red bears |
| 9 | easy | 72 | 3/4 | a purple sparkling chair |
| 10 | easy | 4028 | 4/6 | a black stone bird and a penguin |
| 11 | easy | 37 | 5/6 | six elephants and a purple black flower |
| 12 | medium | 114 | 6/6 | seven metal checkered guitars and four backpacks |
| 13 | medium | 2664 | 7/8 | six giraffes behind a toy on top of seven clocks |
| 14 | medium | 6277 | 8/8 | four suitcases in front of five giraffes chasing seven monkeys |
| 15 | hard | 19992 | 9/10 | six spotted flamingos under four umbrellas to the left of a metal bagel |
| 16 | hard | 5543 | 10/10 | three croissants in front of four rabbits behind five blue pink bicycles |
| 17 | easy | 294 | 3/4 | a pink black motorcycle |
| 18 | easy | 7560 | 4/6 | a clock and a white pink cat |
| 19 | easy | 98 | 5/6 | seven monkeys and a purple white car |
| 20 | medium | 6 | 6/6 | six purple checkered raccoons and five flowers |
| 21 | medium | 35 | 7/8 | six guitars to the right of six donuts in front of a penguin |
| 22 | medium | 153 | 8/8 | six trumpets under four mushrooms on top of four lions |
| 23 | hard | 344 | 9/10 | four candles to the left of seven spotted stone cats jumping over a monkey |
| 24 | hard | 80 | 10/10 | six bicycles to the right of five motorcycles to the right of six wooden purple bears |
| 25 | easy | 225 | 3/4 | a purple pink dog |
| 26 | easy | 4803 | 4/6 | a mushroom and a pink yellow lion |
| 27 | easy | 36 | 5/6 | five green striped birds and a toy |
| 28 | medium | 26 | 6/6 | four blue brown bicycles and six flowers |
| 29 | medium | 149 | 7/8 | a dog under four turtles in front of six zebras |
| 30 | medium | 92 | 8/9 | four brown motorcycles behind four mushrooms to the right of a lion |
| 31 | hard | 109 | 9/9 | six spotted raccoons in front of seven trucks on top of five cookies |
| 32 | hard | 167 | 10/10 | seven yellow kangaroos jumping over five red zebras under five lions |
| 33 | easy | 231 | 3/4 | a glass purple cow |
| 34 | easy | 9076 | 4/6 | a bird and a metal red candle |
| 35 | easy | 395 | 5/6 | five striped black elephants and a cow |
| 36 | medium | 87 | 6/6 | six cookies and five metal white flowers |
| 37 | medium | 208 | 7/8 | four pigs to the left of a giraffe to the right of seven birds |
| 38 | medium | 210 | 8/9 | four violins to the right of four spotted birds on top of a toy |
| 39 | hard | 299 | 9/9 | five bagels behind six motorcycles to the left of four glass monkeys |
| 40 | hard | 154 | 10/10 | four toys on top of six penguins to the left of four green plastic cows |
| 41 | easy | 576 | 3/4 | a brown checkered bear |
| 42 | easy | 2778 | 4/5 | a horse chasing five pigs |
| 43 | easy | 454 | 5/6 | four bears and a yellow green turtle |
| 44 | medium | 327 | 6/6 | seven candles and six yellow striped donuts |
| 45 | medium | 7 | 7/7 | seven pink wooden cats and four striped trumpets |
| 46 | medium | 176 | 8/8 | four elephants behind five toys on top of four croissants |
| 47 | hard | 347 | 9/9 | four giraffes to the right of seven wooden koalas on top of five chairs |
| 48 | hard | 165 | 10/10 | seven striped backpacks to the left of five wooden birds in front of five croissants |
| 49 | easy | 654 | 3/4 | a yellow metal rabbit |
| 50 | easy | 10493 | 4/6 | a bird and a metal sparkling guitar |
| 51 | easy | 57 | 5/5 | five koalas chasing seven raccoons |
| 52 | medium | 519 | 6/6 | six plastic red clocks and six mushrooms |
| 53 | medium | 24 | 7/7 | four stone raccoons and six white metal clocks |
| 54 | medium | 198 | 8/8 | four cookies to the right of five monkeys under five violins |
| 55 | hard | 407 | 9/9 | six mushrooms on top of five red motorcycles in front of six birds |
| 56 | hard | 192 | 10/10 | four checkered donuts to the right of seven yellow birds to the right of six croissants |
| 57 | easy | 927 | 3/4 | a white metal motorcycle |
| 58 | easy | 13076 | 4/6 | a violin and a plastic black bicycle |
| 59 | easy | 749 | 5/6 | five checkered striped bagels and a donut |
| 60 | medium | 2963 | 6/8 | a penguin playing with five rabbits in front of a turtle |
| 61 | medium | 38 | 7/7 | four brown purple trucks and five pink horses |
| 62 | medium | 228 | 8/8 | four koalas to the left of six mushrooms on top of four flamingos |
| 63 | hard | 52 | 9/10 | a motorcycle on top of five penguins behind six brown blue horses |
| 64 | hard | 276 | 10/10 | five kangaroos to the right of five checkered black mushrooms behind four koalas |
| 65 | easy | 1159 | 3/4 | a checkered stone bear |
| 66 | easy | 14548 | 4/6 | a pink white flamingo and a zebra |
| 67 | easy | 772 | 5/6 | six penguins and a white wooden umbrella |
| 68 | medium | 597 | 6/6 | five trumpets and six metal red cookies |
| 69 | medium | 261 | 7/8 | a sheep under four motorcycles to the right of six pigs |
| 70 | medium | 463 | 8/8 | four cats playing with seven koalas under four bicycles |
| 71 | hard | 577 | 9/10 | a kangaroo on top of six glass metal cars on top of four dogs |
| 72 | hard | 325 | 10/10 | four motorcycles to the right of six black turtles in front of seven red violins |
| 73 | easy | 1197 | 3/4 | a red checkered cookie |
| 74 | easy | 17155 | 4/6 | a croissant and a stone sparkling candle |
| 75 | easy | 915 | 5/6 | five horses and a black purple elephant |
| 76 | medium | 743 | 6/6 | six dogs and five pink red pigs |
| 77 | medium | 303 | 7/8 | five flamingos behind six bagels to the left of a turtle |
| 78 | medium | 277 | 8/8 | six monkeys to the right of seven penguins under five umbrellas |
| 79 | hard | 295 | 9/10 | a black dog chasing seven green cats under four trucks |
| 80 | hard | 333 | 10/10 | four bagels in front of five clocks to the right of seven sparkling striped trucks |
| 81 | easy | 1201 | 3/4 | a sparkling pink clock |
| 82 | easy | 18671 | 4/6 | a suitcase and a pink red cat |
| 83 | easy | 969 | 5/6 | five glass green motorcycles and a rabbit |
| 84 | medium | 826 | 6/6 | four yellow stone flowers and six donuts |
| 85 | medium | 381 | 7/8 | five croissants in front of five chairs in front of a pig |
| 86 | medium | 360 | 8/9 | six suitcases to the right of a brown monkey on top of seven trumpets |
| 87 | hard | 560 | 9/9 | five suitcases on top of four birds to the left of five checkered backpacks |
| 88 | hard | 241 | 10/10 | six black red cars behind six cows jumping over five cats |
| 89 | easy | 1346 | 3/4 | a red glass horse |
| 90 | easy | 18924 | 4/6 | a striped purple croissant and a monkey |
| 91 | easy | 1247 | 5/6 | six green glass kangaroos and a trumpet |
| 92 | medium | 862 | 6/6 | four guitars and six yellow metal cookies |
| 93 | medium | 677 | 7/8 | six turtles behind five suitcases to the right of a elephant |
| 94 | medium | 490 | 8/9 | a horse behind six trumpets to the right of four red giraffes |
| 95 | hard | 757 | 9/9 | seven cookies in front of four motorcycles to the left of four glass flowers |
| 96 | hard | 337 | 10/10 | four trucks to the left of five wooden pink guitars to the left of four pigs |
| 97 | easy | 1566 | 3/4 | a spotted white bicycle |
| 98 | easy | 6012 | 4/5 | a dog chasing four kangaroos |
| 99 | easy | 1655 | 5/6 | a cookie and four red spotted zebras |
| 100 | medium | 870 | 6/6 | four toys and four blue green motorcycles |
| 101 | medium | 45 | 7/7 | five striped green cars and four sparkling mushrooms |
| 102 | medium | 340 | 8/8 | five birds to the left of six raccoons under five backpacks |
| 103 | hard | 788 | 9/9 | six kangaroos on top of four green birds under five flamingos |
| 104 | hard | 343 | 10/10 | six purple striped cows in front of four horses in front of five croissants |
| 105 | easy | 1590 | 3/4 | a brown glass flamingo |
| 106 | easy | 2 | 4/4 | six stone yellow cars |
| 107 | easy | 1664 | 5/5 | seven sheeps chasing seven monkeys |
| 108 | medium | 1118 | 6/6 | four yellow pink dogs and four rabbits |
| 109 | medium | 47 | 7/7 | six glass raccoons and six blue black koalas |
| 110 | medium | 380 | 8/8 | six croissants behind four cars behind five sheeps |
| 111 | hard | 861 | 9/9 | six rabbits to the left of five cookies to the left of five blue motorcycles |
| 112 | hard | 376 | 10/10 | five rabbits on top of six glass checkered suitcases in front of seven toys |
| 113 | easy | 1683 | 3/4 | a yellow black clock |
| 114 | easy | 163 | 4/4 | four stone black pigs |
| 115 | easy | 1764 | 5/6 | five metal sparkling monkeys and a candle |
| 116 | medium | 4119 | 6/8 | a horse chasing a kangaroo to the right of five penguins |
| 117 | medium | 58 | 7/7 | six plastic giraffes and four white metal cats |
| 118 | medium | 404 | 8/8 | five mushrooms to the right of five candles to the left of four trumpets |
| 119 | hard | 586 | 9/10 | six stone black pigs under four motorcycles behind a cat |
| 120 | hard | 377 | 10/10 | four horses to the left of six sparkling blue trucks under five clocks |
| 121 | easy | 1841 | 3/4 | a white glass zebra |
| 122 | easy | 217 | 4/4 | six plastic striped flamingos |
| 123 | easy | 1784 | 5/6 | five cookies and a white yellow sheep |
| 124 | medium | 1161 | 6/6 | four bears and five striped spotted horses |
| 125 | medium | 610 | 7/8 | five dogs playing with five kangaroos on top of a cookie |
| 126 | medium | 415 | 8/8 | four donuts behind seven clocks under six birds |
| 127 | hard | 672 | 9/10 | six green white flowers to the right of a suitcase to the left of five bagels |
| 128 | hard | 385 | 10/10 | five sparkling red trumpets in front of four mushrooms to the right of seven turtles |
| 129 | easy | 2138 | 3/4 | a white stone bird |
| 130 | easy | 237 | 4/4 | five red blue kangaroos |
| 131 | easy | 1957 | 5/6 | seven checkered glass horses and a pig |
| 132 | medium | 1249 | 6/6 | six guitars and six purple pink flamingos |
| 133 | medium | 733 | 7/8 | seven elephants behind seven cats to the left of a raccoon |
| 134 | medium | 468 | 8/8 | six bagels in front of seven guitars under four cows |
| 135 | hard | 354 | 9/10 | a kangaroo to the right of six checkered green penguins playing with five raccoons |
| 136 | hard | 390 | 10/10 | four purple cows under seven candles to the right of six sparkling koalas |
| 137 | easy | 2377 | 3/4 | a wooden blue penguin |
| 138 | easy | 439 | 4/4 | seven red black penguins |
| 139 | easy | 2227 | 5/6 | a pig and five sparkling checkered monkeys |
| 140 | medium | 1263 | 6/6 | five glass green cats and four motorcycles |
| 141 | medium | 827 | 7/8 | a violin under six flowers on top of six toys |
| 142 | medium | 526 | 8/8 | seven koalas to the left of four cars to the right of seven zebras |
| 143 | hard | 863 | 9/10 | four croissants in front of four mushrooms behind a spotted blue elephant |
| 144 | hard | 722 | 10/10 | six glass white trumpets to the right of five cows jumping over six birds |
| 145 | easy | 2517 | 3/4 | a black spotted cat |
| 146 | easy | 450 | 4/4 | four green wooden backpacks |
| 147 | easy | 2235 | 5/6 | a plastic striped horse and six elephants |
| 148 | medium | 1378 | 6/6 | six suitcases and four blue green flowers |
| 149 | medium | 973 | 7/8 | four flowers to the left of seven penguins to the right of a bagel |
| 150 | medium | 547 | 8/9 | a motorcycle to the right of seven bicycles in front of four stone rabbits |
| 151 | hard | 896 | 9/9 | four brown umbrellas behind four giraffes to the left of four flowers |
| 152 | hard | 475 | 10/10 | four guitars in front of four plastic wooden violins to the left of five backpacks |
| 153 | easy | 2548 | 3/4 | a red glass penguin |
| 154 | easy | 6025 | 4/5 | a kangaroo chasing four elephants |
| 155 | easy | 2593 | 5/6 | a monkey and four red white donuts |
| 156 | medium | 1401 | 6/6 | four plastic spotted cats and five motorcycles |
| 157 | medium | 76 | 7/7 | seven spotted violins and seven pink stone cats |
| 158 | medium | 584 | 8/8 | six pigs in front of five bicycles to the left of four birds |
| 159 | hard | 1105 | 9/9 | five striped guitars on top of six turtles behind five umbrellas |
| 160 | hard | 571 | 10/10 | four cows in front of seven striped sheeps on top of six green turtles |
| 161 | easy | 2701 | 3/4 | a glass black turtle |
| 162 | easy | 612 | 4/4 | seven yellow red umbrellas |
| 163 | easy | 5415 | 5/5 | six turtles chasing four raccoons |
| 164 | medium | 1468 | 6/6 | four white purple trumpets and seven cows |
| 165 | medium | 502 | 7/7 | four blue yellow pigs and seven striped donuts |
| 166 | medium | 599 | 8/8 | six motorcycles under seven penguins to the right of four violins |
| 167 | hard | 1154 | 9/9 | five cars behind five guitars to the left of five pink koalas |
| 168 | hard | 583 | 10/10 | seven blue trumpets to the right of four suitcases in front of six plastic motorcycles |
| 169 | easy | 2737 | 3/4 | a plastic brown bird |
| 170 | easy | 642 | 4/4 | five yellow red backpacks |
| 171 | easy | 3294 | 5/6 | six croissants and a purple red pig |
| 172 | medium | 5029 | 6/8 | a penguin playing with seven turtles in front of a kangaroo |
| 173 | medium | 530 | 7/7 | four green pink guitars and four yellow turtles |
| 174 | medium | 680 | 8/8 | five clocks to the right of six bagels to the left of six zebras |
| 175 | hard | 934 | 9/10 | a white sparkling bicycle under seven flamingos to the left of four flowers |
| 176 | hard | 633 | 10/10 | six yellow suitcases behind four spotted penguins under six croissants |
| 177 | easy | 2749 | 3/4 | a purple plastic dog |
| 178 | easy | 669 | 4/4 | six blue yellow candles |
| 179 | easy | 3842 | 5/6 | five lions and a blue glass trumpet |
| 180 | medium | 1502 | 6/6 | seven green black monkeys and seven cars |
| 181 | medium | 1487 | 7/8 | a rabbit chasing four horses behind seven suitcases |
| 182 | medium | 962 | 8/8 | seven violins to the right of five bears to the right of seven bagels |
| 183 | hard | 1036 | 9/10 | five white metal cows to the right of six penguins behind a giraffe |
| 184 | hard | 668 | 10/10 | seven black red motorcycles on top of four bagels under seven lions |
| 185 | easy | 2756 | 3/4 | a sparkling glass flower |
| 186 | easy | 684 | 4/4 | six purple plastic pigs |
| 187 | easy | 4076 | 5/6 | six monkeys and a yellow metal zebra |
| 188 | medium | 1682 | 6/6 | five sparkling blue bears and five cats |
| 189 | medium | 982 | 7/8 | four rabbits under a sheep behind six flamingos |
| 190 | medium | 1017 | 8/8 | seven motorcycles in front of seven kangaroos in front of seven bagels |
| 191 | hard | 386 | 9/10 | a pink clock to the right of six yellow penguins chasing five giraffes |
| 192 | hard | 701 | 10/10 | five flamingos under seven white sparkling cars on top of four trumpets |
| 193 | easy | 2866 | 3/4 | a brown yellow violin |
| 194 | easy | 709 | 4/4 | seven pink glass bicycles |
| 195 | easy | 4141 | 5/6 | seven black blue guitars and a violin |
| 196 | medium | 1694 | 6/6 | seven horses and six blue wooden motorcycles |
| 197 | medium | 1053 | 7/8 | a flower behind four violins under four flamingos |
| 198 | medium | 1262 | 8/8 | four flamingos to the left of four candles to the left of four toys |
| 199 | hard | 1148 | 9/10 | four dogs behind seven purple candles in front of a wooden sheep |
| 200 | hard | 834 | 10/10 | seven backpacks to the left of four stone plastic flamingos chasing six cats |

Each selected record in the JSON artifact retains the original `vqa_list`, `skills`, normalized atomic constraints, score components, source line, row hash, and dataset hash.
