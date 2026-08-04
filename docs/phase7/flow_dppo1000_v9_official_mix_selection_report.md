# Flow-DPPO Geneval2 1000-Prompt Selection

## Policy

- Selection method: `flow_dppo_geneval2_official_atom_balanced_deterministic_v1`
- Source: `Tencent-Hunyuan/UniRL@e1a814ff9de6de644b093c6ed0106869c1881e53`
- Dataset: `datasets/geneval2/synthetic/train.jsonl`
- Source rows: 20000
- Rows where `atom_count != len(vqa_list)`: 6007
- Official 800-row Geneval2 test set remains held out.
- Held-out boundary: exact prompt overlaps excluded=0; semantic-family overlaps excluded=9650.
- Local reporting tier mix (not official labels): easy=375, hard=250, medium=375
- Atom-count mix: 3=125, 4=125, 5=125, 6=125, 7=125, 8=125, 9=125, 10=125
- This mirrors the official 800-row atom-count distribution: 100 rows for each atom_count from 3 through 10.
- Prior selected source rows excluded: 220.
- Selection is deterministic and uses metadata/semantic diversity only; no live image result is used.

## Coverage

- Selected prompts: 1000
- Distinct entities: 40
- Relation/action phrases: behind, chasing, in front of, jumping over, on top of, playing with, to the left of, to the right of, under
- Constraint atoms: attribute=1518, count=2224, object=2224, position=863, verb=108
- Official-scaled skill soft targets: attribute=1517.5, count=2531.25, object=2531.25, position=827.5, verb=107.5
- Selected minus soft target: attribute=+0.5, count=-307.25, object=-307.25, position=+35.5, verb=+0.5
- Actual VQA-count histogram: 4=238, 5=36, 6=205, 7=59, 8=183, 9=92, 10=187

## Selected Rows

| Rank | Tier | Source line | Atoms/VQAs | Prompt |
|---:|---|---:|---:|---|
| 1 | easy | 2990 | 3/4 | a red wooden backpack |
| 2 | easy | 813 | 4/4 | five sparkling yellow clocks |
| 3 | easy | 342 | 5/7 | a red wooden bagel on top of a motorcycle |
| 4 | medium | 368 | 6/8 | a croissant behind six kangaroos to the left of a chair |
| 5 | medium | 3198 | 7/9 | a checkered turtle jumping over a pig in front of six umbrellas |
| 6 | medium | 2930 | 8/10 | a bear to the right of five bicycles under a metal wooden penguin |
| 7 | hard | 1270 | 9/10 | six checkered raccoons to the right of a suitcase to the left of four checkered zebras |
| 8 | hard | 947 | 10/10 | four koalas to the right of five metal checkered cats in front of five candles |
| 9 | easy | 3030 | 3/4 | a spotted white cow |
| 10 | easy | 1065 | 4/4 | six metal red rabbits |
| 11 | easy | 5322 | 5/6 | six birds and a plastic spotted cookie |
| 12 | medium | 1730 | 6/6 | seven white blue flowers and four dogs |
| 13 | medium | 5535 | 7/8 | four monkeys to the left of five lions to the right of a guitar |
| 14 | medium | 12207 | 8/8 | four sheeps playing with two flamingos in front of six donuts |
| 15 | hard | 13824 | 9/10 | a trumpet to the left of five black elephants to the left of six blue cars |
| 16 | hard | 7365 | 10/10 | two toys under six horses on top of six spotted black mushrooms |
| 17 | easy | 3310 | 3/4 | a glass purple violin |
| 18 | easy | 1238 | 4/4 | four striped blue giraffes |
| 19 | easy | 14261 | 5/6 | a pink stone truck and six cows |
| 20 | medium | 1826 | 6/6 | seven trumpets and seven blue brown bicycles |
| 21 | medium | 1078 | 7/8 | six flamingos on top of six bears on top of a monkey |
| 22 | medium | 1361 | 8/8 | five birds to the left of four kangaroos to the left of four turtles |
| 23 | hard | 1469 | 9/10 | six birds chasing four striped stone rabbits behind a turtle |
| 24 | hard | 704 | 10/10 | six white cows on top of five red bicycles under six raccoons |
| 25 | easy | 3099 | 3/4 | a sparkling green flower |
| 26 | easy | 825 | 4/4 | six plastic glass cows |
| 27 | easy | 4667 | 5/6 | a chair and five metal blue dogs |
| 28 | medium | 1839 | 6/6 | six trucks and four glass green cars |
| 29 | medium | 1128 | 7/8 | a guitar to the left of seven croissants in front of four trumpets |
| 30 | medium | 563 | 8/9 | a turtle on top of seven horses under five brown motorcycles |
| 31 | hard | 1157 | 9/9 | five white rabbits on top of seven chairs to the right of seven penguins |
| 32 | hard | 2192 | 10/10 | four plastic green lions playing with four horses under seven clocks |
| 33 | easy | 3361 | 3/4 | a striped plastic turtle |
| 34 | easy | 874 | 4/4 | five stone sparkling backpacks |
| 35 | easy | 4673 | 5/6 | four pigs and a red checkered cat |
| 36 | medium | 1881 | 6/6 | six bicycles and six white sparkling suitcases |
| 37 | medium | 1151 | 7/8 | six backpacks to the left of a suitcase behind four umbrellas |
| 38 | medium | 664 | 8/9 | five penguins to the left of four croissants under a white chair |
| 39 | hard | 1188 | 9/9 | five red chairs under five cookies on top of six flamingos |
| 40 | hard | 795 | 10/10 | five yellow sparkling lions on top of six croissants behind seven kangaroos |
| 41 | easy | 3399 | 3/4 | a metal plastic cow |
| 42 | easy | 9039 | 4/5 | four cats chasing a zebra |
| 43 | easy | 4788 | 5/6 | five pigs and a glass purple violin |
| 44 | medium | 1970 | 6/6 | four candles and five blue striped bears |
| 45 | medium | 532 | 7/7 | four blue penguins and five blue purple flamingos |
| 46 | medium | 1681 | 8/8 | seven sheeps under four trumpets in front of six cookies |
| 47 | hard | 1337 | 9/9 | seven lions in front of four backpacks behind four brown kangaroos |
| 48 | hard | 812 | 10/10 | four koalas on top of four brown blue umbrellas behind seven toys |
| 49 | easy | 3689 | 3/4 | a sparkling blue car |
| 50 | easy | 919 | 4/4 | four purple metal candles |
| 51 | easy | 5759 | 5/5 | six penguins chasing five giraffes |
| 52 | medium | 2144 | 6/6 | six giraffes and four yellow black trucks |
| 53 | medium | 542 | 7/7 | four metal green flamingos and five metal cookies |
| 54 | medium | 1751 | 8/8 | five trumpets behind five koalas in front of four donuts |
| 55 | hard | 1363 | 9/9 | five bicycles behind four penguins to the right of five white cookies |
| 56 | hard | 893 | 10/10 | six donuts on top of six candles to the right of six blue striped umbrellas |
| 57 | easy | 3733 | 3/4 | a red striped donut |
| 58 | easy | 1072 | 4/4 | five white stone lions |
| 59 | easy | 5095 | 5/6 | four chairs and a brown yellow sheep |
| 60 | medium | 6543 | 6/8 | five sheeps playing with a monkey under a car |
| 61 | medium | 700 | 7/7 | four wooden glass sheeps and five checkered giraffes |
| 62 | medium | 1758 | 8/8 | four cookies behind four horses to the right of five umbrellas |
| 63 | hard | 1311 | 9/10 | six plastic stone turtles to the right of six croissants to the left of a cat |
| 64 | hard | 918 | 10/10 | seven trumpets to the left of five brown raccoons to the left of six white clocks |
| 65 | easy | 3741 | 3/4 | a pink wooden dog |
| 66 | easy | 1121 | 4/4 | five brown red bagels |
| 67 | easy | 5351 | 5/6 | five pink striped flamingos and a turtle |
| 68 | medium | 2284 | 6/6 | four turtles and six white checkered flamingos |
| 69 | medium | 1152 | 7/8 | seven cows to the left of four backpacks to the left of a elephant |
| 70 | medium | 554 | 8/8 | five penguins under seven kangaroos chasing five sheeps |
| 71 | hard | 1760 | 9/10 | four red blue suitcases in front of a elephant to the left of six giraffes |
| 72 | hard | 925 | 10/10 | six violins to the left of seven striped pink sheeps behind four raccoons |
| 73 | easy | 3780 | 3/4 | a sparkling wooden cow |
| 74 | easy | 1199 | 4/4 | five pink stone motorcycles |
| 75 | easy | 5440 | 5/6 | six stone glass lions and a guitar |
| 76 | medium | 2293 | 6/6 | seven metal brown backpacks and five suitcases |
| 77 | medium | 1328 | 7/8 | seven pigs to the left of four giraffes on top of a toy |
| 78 | medium | 1843 | 8/8 | six cookies on top of five donuts to the right of four suitcases |
| 79 | hard | 1119 | 9/10 | six checkered cows jumping over six cats to the left of a black turtle |
| 80 | hard | 987 | 10/10 | seven green blue bears in front of seven cows to the right of seven penguins |
| 81 | easy | 3797 | 3/4 | a plastic red giraffe |
| 82 | easy | 1385 | 4/4 | four plastic brown candles |
| 83 | easy | 7009 | 5/6 | four raccoons and a striped sparkling bird |
| 84 | medium | 2451 | 6/6 | four birds and six striped blue dogs |
| 85 | medium | 1554 | 7/8 | five cookies behind six kangaroos to the right of a clock |
| 86 | medium | 737 | 8/9 | a cow in front of four umbrellas on top of seven white bicycles |
| 87 | hard | 1521 | 9/9 | seven green giraffes to the left of seven cookies under five flamingos |
| 88 | hard | 2319 | 10/10 | six dogs chasing four kangaroos to the left of four pink brown guitars |
| 89 | easy | 3800 | 3/4 | a sparkling metal violin |
| 90 | easy | 1390 | 4/4 | five brown sparkling raccoons |
| 91 | easy | 7069 | 5/6 | five backpacks and a brown sparkling sheep |
| 92 | medium | 2633 | 6/6 | seven plastic brown guitars and six croissants |
| 93 | medium | 1605 | 7/8 | six violins in front of four umbrellas in front of a penguin |
| 94 | medium | 807 | 8/9 | four yellow motorcycles in front of a candle behind five zebras |
| 95 | hard | 1525 | 9/9 | four red clocks to the left of five flamingos on top of four cars |
| 96 | hard | 1122 | 10/10 | seven stone violins in front of four green cars on top of seven trumpets |
| 97 | easy | 3835 | 3/4 | a purple brown pig |
| 98 | easy | 9111 | 4/5 | a horse chasing five koalas |
| 99 | easy | 7085 | 5/6 | a brown white suitcase and four toys |
| 100 | medium | 2639 | 6/6 | five blue striped candles and four trucks |
| 101 | medium | 846 | 7/7 | seven striped bagels and four checkered wooden clocks |
| 102 | medium | 1926 | 8/8 | four sheeps behind four cats behind six guitars |
| 103 | hard | 1768 | 9/9 | seven horses in front of five bagels behind five red clocks |
| 104 | hard | 1185 | 10/10 | four turtles on top of seven trumpets under six green purple trucks |
| 105 | easy | 3964 | 3/4 | a pink brown motorcycle |
| 106 | easy | 1476 | 4/4 | seven red brown koalas |
| 107 | easy | 7160 | 5/5 | four bears chasing five kangaroos |
| 108 | medium | 2741 | 6/6 | four spotted glass cookies and five backpacks |
| 109 | medium | 1002 | 7/7 | five white trucks and five white metal clocks |
| 110 | medium | 2119 | 8/8 | four dogs under four sheeps in front of four rabbits |
| 111 | hard | 1787 | 9/9 | six rabbits behind seven bicycles on top of seven pink cookies |
| 112 | hard | 1271 | 10/10 | seven checkered wooden dogs in front of four cookies behind four zebras |
| 113 | easy | 4228 | 3/4 | a stone wooden horse |
| 114 | easy | 1499 | 4/4 | five striped checkered horses |
| 115 | easy | 7231 | 5/6 | a bagel and five green sparkling penguins |
| 116 | medium | 7462 | 6/8 | a cookie to the left of a sheep jumping over seven turtles |
| 117 | medium | 1034 | 7/7 | five brown rabbits and six green red cows |
| 118 | medium | 2216 | 8/8 | seven toys to the left of seven cows on top of five suitcases |
| 119 | hard | 1834 | 9/10 | four birds to the right of seven sparkling blue trucks to the right of a bagel |
| 120 | hard | 1272 | 10/10 | seven bagels to the right of five black monkeys to the left of five purple koalas |
| 121 | easy | 4467 | 3/4 | a wooden checkered mushroom |
| 122 | easy | 1530 | 4/4 | seven sparkling black turtles |
| 123 | easy | 7401 | 5/6 | a violin and four sparkling black koalas |
| 124 | medium | 2755 | 6/6 | six elephants and four spotted checkered monkeys |
| 125 | medium | 1874 | 7/8 | a sheep playing with five zebras on top of six bears |
| 126 | medium | 2733 | 8/8 | five flowers behind six clocks behind six bagels |
| 127 | hard | 1860 | 9/10 | a bear to the right of seven red striped zebras under six bagels |
| 128 | hard | 1297 | 10/10 | six yellow flowers in front of seven bears to the left of six black sheeps |
| 129 | easy | 4842 | 3/4 | a metal spotted car |
| 130 | easy | 1580 | 4/4 | seven white red zebras |
| 131 | easy | 7860 | 5/6 | six guitars and a striped white zebra |
| 132 | medium | 3204 | 6/6 | seven croissants and seven white plastic umbrellas |
| 133 | medium | 1612 | 7/8 | six bears behind five kangaroos on top of a penguin |
| 134 | medium | 2766 | 8/8 | four toys in front of five birds under six candles |
| 135 | hard | 3387 | 9/10 | five kangaroos on top of a horse playing with seven striped sparkling koalas |
| 136 | hard | 1367 | 10/10 | five umbrellas on top of four sparkling wooden trumpets to the right of six cows |
| 137 | easy | 5076 | 3/4 | a checkered purple penguin |
| 138 | easy | 1740 | 4/4 | four wooden blue bears |
| 139 | easy | 8090 | 5/6 | a green pink raccoon and four backpacks |
| 140 | medium | 3309 | 6/6 | six plastic green lions and seven guitars |
| 141 | medium | 1742 | 7/8 | five candles in front of a truck on top of four horses |
| 142 | medium | 2789 | 8/8 | seven kangaroos to the left of four bagels behind four zebras |
| 143 | hard | 1894 | 9/10 | a white monkey behind five purple backpacks in front of four mushrooms |
| 144 | hard | 2406 | 10/10 | four penguins jumping over six striped cats on top of four blue giraffes |
| 145 | easy | 5289 | 3/4 | a stone striped bear |
| 146 | easy | 1782 | 4/4 | four sparkling red cats |
| 147 | easy | 8169 | 5/6 | a plastic stone raccoon and four mushrooms |
| 148 | medium | 3401 | 6/6 | six green plastic toys and five turtles |
| 149 | medium | 1921 | 7/8 | a dog to the right of six candles in front of seven croissants |
| 150 | medium | 974 | 8/9 | five spotted umbrellas under five zebras on top of a backpack |
| 151 | hard | 1822 | 9/9 | five striped bagels on top of four cars to the right of seven cows |
| 152 | hard | 1565 | 10/10 | five flowers behind seven donuts to the right of five brown red candles |
| 153 | easy | 5404 | 3/4 | a striped purple donut |
| 154 | easy | 16167 | 4/5 | six elephants chasing a horse |
| 155 | easy | 8183 | 5/6 | seven mushrooms and a pink glass zebra |
| 156 | medium | 3942 | 6/6 | four blue sparkling trucks and four penguins |
| 157 | medium | 1200 | 7/7 | six stone rabbits and six sparkling stone elephants |
| 158 | medium | 2862 | 8/8 | five guitars to the right of seven mushrooms under six cats |
| 159 | hard | 2017 | 9/9 | four checkered toys under six umbrellas on top of four cookies |
| 160 | hard | 1589 | 10/10 | four green flamingos in front of six white trumpets under four horses |
| 161 | easy | 5701 | 3/4 | a metal brown dog |
| 162 | easy | 1786 | 4/4 | five spotted wooden umbrellas |
| 163 | easy | 7506 | 5/5 | four raccoons chasing six dogs |
| 164 | medium | 3954 | 6/6 | five brown green horses and five motorcycles |
| 165 | medium | 1324 | 7/7 | four spotted red cows and seven metal giraffes |
| 166 | medium | 2935 | 8/8 | four cars behind five pigs behind six donuts |
| 167 | hard | 2080 | 9/9 | four pink elephants behind seven dogs in front of six clocks |
| 168 | hard | 1609 | 10/10 | five dogs under seven purple checkered trucks in front of six koalas |
| 169 | easy | 5784 | 3/4 | a glass green donut |
| 170 | easy | 1820 | 4/4 | five plastic yellow umbrellas |
| 171 | easy | 8277 | 5/6 | six pigs and a checkered red zebra |
| 172 | medium | 2629 | 6/8 | three koalas jumping over a cat in front of a pig |
| 173 | medium | 1327 | 7/7 | five brown bears and four green red turtles |
| 174 | medium | 3072 | 8/8 | seven trucks under six cows in front of five cars |
| 175 | hard | 1962 | 9/10 | four black mushrooms under four wooden flowers on top of a giraffe |
| 176 | hard | 1720 | 10/10 | six turtles in front of five motorcycles on top of four green wooden guitars |
| 177 | easy | 5802 | 3/4 | a metal striped bagel |
| 178 | easy | 1899 | 4/4 | four pink sparkling elephants |
| 179 | easy | 8279 | 5/6 | four sparkling wooden chairs and a raccoon |
| 180 | medium | 4017 | 6/6 | seven candles and four white checkered koalas |
| 181 | medium | 2307 | 7/8 | six croissants on top of a pig chasing six flamingos |
| 182 | medium | 3165 | 8/8 | six bagels to the right of four clocks under six guitars |
| 183 | hard | 2018 | 9/10 | six wooden cows behind a donut on top of seven wooden bicycles |
| 184 | hard | 1789 | 10/10 | four cookies under seven donuts on top of five brown striped motorcycles |
| 185 | easy | 5972 | 3/4 | a pink stone bird |
| 186 | easy | 1955 | 4/4 | seven red spotted cows |
| 187 | easy | 8600 | 5/6 | five plastic yellow birds and a penguin |
| 188 | medium | 4019 | 6/6 | four glass blue candles and five sheeps |
| 189 | medium | 1999 | 7/8 | six monkeys under a lion in front of five motorcycles |
| 190 | medium | 3222 | 8/8 | four suitcases in front of six zebras to the right of five cats |
| 191 | hard | 4347 | 9/10 | four yellow wooden bagels on top of four lions playing with a elephant |
| 192 | hard | 1852 | 10/10 | four cats behind seven spotted pink toys on top of four candles |
| 193 | easy | 6050 | 3/4 | a checkered black croissant |
| 194 | easy | 1975 | 4/4 | five yellow sparkling kangaroos |
| 195 | easy | 8641 | 5/6 | a clock and four wooden black penguins |
| 196 | medium | 4052 | 6/6 | five wooden metal lions and seven cookies |
| 197 | medium | 2014 | 7/8 | seven bagels under a pig in front of five cars |
| 198 | medium | 3318 | 8/8 | five kangaroos behind five rabbits under six violins |
| 199 | hard | 2054 | 9/10 | a bear behind six toys on top of four striped plastic monkeys |
| 200 | hard | 2435 | 10/10 | five toys in front of six monkeys chasing six sparkling white rabbits |
| 201 | easy | 6082 | 3/4 | a stone brown lion |
| 202 | easy | 1982 | 4/4 | six black sparkling chairs |
| 203 | easy | 8816 | 5/6 | four wooden white backpacks and a turtle |
| 204 | medium | 4187 | 6/6 | four white wooden backpacks and six penguins |
| 205 | medium | 2028 | 7/8 | four suitcases in front of a chair behind six cows |
| 206 | medium | 988 | 8/9 | a red giraffe under six birds in front of four toys |
| 207 | hard | 2099 | 9/9 | six mushrooms in front of five penguins to the left of seven metal koalas |
| 208 | hard | 1870 | 10/10 | four wooden penguins under six checkered birds to the right of four raccoons |
| 209 | easy | 6147 | 3/4 | a brown spotted cow |
| 210 | easy | 16312 | 4/5 | five lions chasing a sheep |
| 211 | easy | 9606 | 5/6 | four motorcycles and a black blue sheep |
| 212 | medium | 4372 | 6/6 | five pigs and five plastic brown croissants |
| 213 | medium | 1412 | 7/7 | four white horses and seven glass black trumpets |
| 214 | medium | 3400 | 8/8 | five donuts to the right of five motorcycles to the left of six backpacks |
| 215 | hard | 2350 | 9/9 | four cookies on top of six guitars to the left of six green clocks |
| 216 | hard | 1912 | 10/10 | five striped croissants on top of four metal dogs to the right of seven trumpets |
| 217 | easy | 6335 | 3/4 | a green brown sheep |
| 218 | easy | 1988 | 4/4 | four sparkling stone donuts |
| 219 | easy | 8941 | 5/5 | five horses chasing six elephants |
| 220 | medium | 4495 | 6/6 | seven pigs and six spotted blue guitars |
| 221 | medium | 1551 | 7/7 | five metal stone flamingos and four spotted raccoons |
| 222 | medium | 3434 | 8/8 | four croissants in front of six motorcycles on top of seven monkeys |
| 223 | hard | 2386 | 9/9 | six backpacks to the left of five black monkeys behind four donuts |
| 224 | hard | 1939 | 10/10 | four cookies to the right of five birds on top of four wooden glass dogs |
| 225 | easy | 6376 | 3/4 | a plastic wooden raccoon |
| 226 | easy | 2001 | 4/4 | five green plastic cows |
| 227 | easy | 9691 | 5/6 | a cookie and four stone green flamingos |
| 228 | medium | 6087 | 6/8 | a lion on top of a giraffe jumping over two penguins |
| 229 | medium | 1766 | 7/7 | seven stone cookies and six plastic black croissants |
| 230 | medium | 3466 | 8/8 | six trucks under six chairs under four backpacks |
| 231 | hard | 2096 | 9/10 | six black kangaroos on top of five backpacks to the right of a stone elephant |
| 232 | hard | 1987 | 10/10 | five white backpacks on top of four birds to the right of seven stone bagels |
| 233 | easy | 6410 | 3/4 | a glass sparkling chair |
| 234 | easy | 2025 | 4/4 | four pink wooden dogs |
| 235 | easy | 10130 | 5/6 | five horses and a plastic white bagel |
| 236 | medium | 4518 | 6/6 | six brown yellow horses and six kangaroos |
| 237 | medium | 2540 | 7/8 | four rabbits playing with five cows under a bird |
| 238 | medium | 3481 | 8/8 | seven guitars in front of seven penguins in front of four cookies |
| 239 | hard | 2171 | 9/10 | four birds to the left of a clock in front of four red sparkling suitcases |
| 240 | hard | 1994 | 10/10 | six red trucks in front of seven donuts behind five black cookies |
| 241 | easy | 6436 | 3/4 | a plastic black bagel |
| 242 | easy | 2090 | 4/4 | seven blue sparkling trucks |
| 243 | easy | 10261 | 5/6 | a pink spotted car and four cows |
| 244 | medium | 4557 | 6/6 | seven clocks and seven striped stone koalas |
| 245 | medium | 2201 | 7/8 | a dog under six cookies on top of six trumpets |
| 246 | medium | 683 | 8/8 | six guitars behind seven zebras playing with five rabbits |
| 247 | hard | 2236 | 9/10 | seven backpacks to the left of a stone metal violin to the right of four umbrellas |
| 248 | hard | 2050 | 10/10 | four black guitars under seven trucks on top of four red pigs |
| 249 | easy | 6466 | 3/4 | a metal purple suitcase |
| 250 | easy | 2124 | 4/4 | five purple black trumpets |
| 251 | easy | 10267 | 5/6 | six flamingos and a yellow wooden toy |
| 252 | medium | 4709 | 6/6 | six checkered wooden monkeys and five chairs |
| 253 | medium | 2329 | 7/8 | six candles on top of five mushrooms on top of a pig |
| 254 | medium | 3718 | 8/8 | six monkeys on top of six donuts on top of seven birds |
| 255 | hard | 2416 | 9/10 | a umbrella on top of seven blue sheeps to the left of six metal cookies |
| 256 | hard | 2549 | 10/10 | four stone plastic dogs chasing six bears behind four lions |
| 257 | easy | 6476 | 3/4 | a green metal bagel |
| 258 | easy | 2140 | 4/4 | five stone pink umbrellas |
| 259 | easy | 10720 | 5/6 | a blue striped suitcase and four clocks |
| 260 | medium | 4908 | 6/6 | four glass spotted flamingos and seven turtles |
| 261 | medium | 2387 | 7/8 | a rabbit behind seven cows to the right of five cars |
| 262 | medium | 1087 | 8/9 | a bagel in front of four dogs behind seven checkered suitcases |
| 263 | hard | 2433 | 9/9 | six dogs under four motorcycles to the left of seven striped violins |
| 264 | hard | 2131 | 10/10 | four umbrellas on top of six pink glass bicycles in front of five elephants |
| 265 | easy | 6504 | 3/4 | a striped stone koala |
| 266 | easy | 18135 | 4/5 | seven penguins chasing a dog |
| 267 | easy | 10962 | 5/6 | a bagel and seven sparkling checkered kangaroos |
| 268 | medium | 4941 | 6/6 | seven motorcycles and five green plastic flamingos |
| 269 | medium | 1827 | 7/7 | four metal violins and four green wooden bicycles |
| 270 | medium | 3777 | 8/8 | seven toys in front of six cows under seven violins |
| 271 | hard | 2439 | 9/9 | six brown mushrooms on top of five donuts under seven guitars |
| 272 | hard | 2197 | 10/10 | four plastic pigs on top of seven donuts under seven sparkling dogs |
| 273 | easy | 6532 | 3/4 | a wooden blue monkey |
| 274 | easy | 19932 | 4/5 | a monkey chasing four bears |
| 275 | easy | 11183 | 5/6 | a red black kangaroo and seven backpacks |
| 276 | medium | 4953 | 6/6 | seven metal yellow candles and seven croissants |
| 277 | medium | 2008 | 7/7 | five purple blue kangaroos and seven purple bicycles |
| 278 | medium | 3812 | 8/8 | seven bears under six umbrellas to the left of five clocks |
| 279 | hard | 2450 | 9/9 | seven rabbits in front of four glass koalas behind five zebras |
| 280 | hard | 2240 | 10/10 | four sparkling plastic trumpets to the left of seven cookies on top of four zebras |
| 281 | easy | 6707 | 3/4 | a spotted purple bicycle |
| 282 | easy | 2180 | 4/4 | five plastic black turtles |
| 283 | easy | 11189 | 5/6 | a glass white rabbit and six horses |
| 284 | medium | 6917 | 6/8 | a flamingo jumping over a bird in front of three violins |
| 285 | medium | 2097 | 7/7 | six striped umbrellas and four spotted white dogs |
| 286 | medium | 3830 | 8/8 | seven cats behind six croissants under seven kangaroos |
| 287 | hard | 2537 | 9/10 | six cars on top of five stone striped donuts under a sheep |
| 288 | hard | 2283 | 10/10 | five lions to the left of six pink metal cookies to the right of six monkeys |
| 289 | easy | 6740 | 3/4 | a striped glass backpack |
| 290 | easy | 2277 | 4/4 | seven metal sparkling violins |
| 291 | easy | 11497 | 5/6 | six cats and a blue wooden guitar |
| 292 | medium | 4998 | 6/6 | four plastic white croissants and five bicycles |
| 293 | medium | 2914 | 7/8 | six penguins playing with a pig in front of six elephants |
| 294 | medium | 3863 | 8/8 | four bagels under five bicycles under seven candles |
| 295 | hard | 2581 | 9/10 | a truck to the left of four checkered sheeps to the right of five black clocks |
| 296 | hard | 2332 | 10/10 | six croissants to the left of five purple bagels to the right of six plastic donuts |
| 297 | easy | 6931 | 3/4 | a white spotted violin |
| 298 | easy | 2306 | 4/4 | four yellow glass rabbits |
| 299 | easy | 12157 | 5/6 | a purple sparkling bear and six mushrooms |
| 300 | medium | 5022 | 6/6 | four birds and six black sparkling violins |
| 301 | medium | 2398 | 7/8 | seven penguins behind a guitar in front of five lions |
| 302 | medium | 837 | 8/8 | four umbrellas in front of four raccoons chasing six elephants |
| 303 | hard | 2831 | 9/10 | four plastic black bagels under seven pigs to the right of a elephant |
| 304 | hard | 2390 | 10/10 | six zebras to the right of four trumpets under seven brown white flowers |
| 305 | easy | 6949 | 3/4 | a wooden striped bird |
| 306 | easy | 2326 | 4/4 | six blue checkered elephants |
| 307 | easy | 12382 | 5/6 | six striped metal elephants and a horse |
| 308 | medium | 5173 | 6/6 | five glass striped toys and six flowers |
| 309 | medium | 2401 | 7/8 | four horses to the right of five candles to the right of a donut |
| 310 | medium | 3897 | 8/8 | seven trumpets to the right of four kangaroos in front of six mushrooms |
| 311 | hard | 2949 | 9/10 | a rabbit under seven trumpets to the right of seven stone sparkling sheeps |
| 312 | hard | 2809 | 10/10 | six stone kangaroos behind seven spotted koalas jumping over four elephants |
| 313 | easy | 7081 | 3/4 | a purple black donut |
| 314 | easy | 2365 | 4/4 | four purple yellow penguins |
| 315 | easy | 12458 | 5/6 | a red green koala and six bagels |
| 316 | medium | 5240 | 6/6 | four violins and seven red pink turtles |
| 317 | medium | 2423 | 7/8 | a horse to the left of six candles under four violins |
| 318 | medium | 1333 | 8/9 | five flowers to the left of a umbrella to the left of six checkered flamingos |
| 319 | hard | 2709 | 9/9 | six birds on top of seven blue guitars on top of four candles |
| 320 | hard | 2424 | 10/10 | four trumpets behind five plastic elephants in front of six checkered chairs |
| 321 | easy | 7091 | 3/4 | a pink glass bear |
| 322 | easy | 3437 | 4/5 | three flamingos chasing a penguin |
| 323 | easy | 12727 | 5/6 | four glass brown flamingos and a croissant |
| 324 | medium | 5316 | 6/6 | four wooden pink koalas and four lions |
| 325 | medium | 2104 | 7/7 | five yellow guitars and four striped green croissants |
| 326 | medium | 3912 | 8/8 | seven flamingos to the left of six cats to the right of six horses |
| 327 | hard | 2725 | 9/9 | five green donuts under four suitcases to the right of six penguins |
| 328 | hard | 2425 | 10/10 | seven bears to the right of seven blue glass toys on top of four sheeps |
| 329 | easy | 7151 | 3/4 | a blue green pig |
| 330 | easy | 4153 | 4/5 | two dogs chasing a elephant |
| 331 | easy | 12761 | 5/6 | five cows and a white blue croissant |
| 332 | medium | 5491 | 6/6 | five cars and five red stone motorcycles |
| 333 | medium | 2242 | 7/7 | four stone glass turtles and seven blue koalas |
| 334 | medium | 4285 | 8/8 | six lions behind five kangaroos to the left of four candles |
| 335 | hard | 2798 | 9/9 | four glass sheeps to the left of four toys on top of six birds |
| 336 | hard | 2525 | 10/10 | seven toys to the left of six horses behind seven stone wooden zebras |
| 337 | easy | 7306 | 3/4 | a black wooden giraffe |
| 338 | easy | 2412 | 4/4 | four black sparkling koalas |
| 339 | easy | 13284 | 5/6 | a purple green kangaroo and six suitcases |
| 340 | medium | 7568 | 6/8 | a flower on top of a zebra playing with three kangaroos |
| 341 | medium | 2331 | 7/7 | five checkered cookies and four yellow wooden cats |
| 342 | medium | 4515 | 8/8 | five birds under four turtles to the right of four penguins |
| 343 | hard | 3264 | 9/10 | six white flamingos to the left of a rabbit on top of five blue violins |
| 344 | hard | 2547 | 10/10 | six sparkling monkeys behind seven plastic guitars under five toys |
| 345 | easy | 7310 | 3/4 | a purple black motorcycle |
| 346 | easy | 2427 | 4/4 | six metal checkered flowers |
| 347 | easy | 13459 | 5/6 | five metal blue pigs and a monkey |
| 348 | medium | 5675 | 6/6 | seven red black zebras and five kangaroos |
| 349 | medium | 4160 | 7/8 | a flamingo chasing four rabbits to the left of five chairs |
| 350 | medium | 4523 | 8/8 | six mushrooms under five cats to the right of four bicycles |
| 351 | hard | 3266 | 9/10 | six monkeys to the left of four spotted plastic donuts in front of a toy |
| 352 | hard | 2563 | 10/10 | four spotted cookies in front of seven donuts in front of seven white rabbits |
| 353 | easy | 7749 | 3/4 | a spotted brown cow |
| 354 | easy | 2570 | 4/4 | five wooden purple flamingos |
| 355 | easy | 13822 | 5/6 | a yellow plastic suitcase and seven cats |
| 356 | medium | 5712 | 6/6 | five black purple toys and five trumpets |
| 357 | medium | 2825 | 7/8 | four mushrooms on top of six pigs on top of a bicycle |
| 358 | medium | 1005 | 8/8 | seven penguins playing with six elephants to the right of seven cars |
| 359 | hard | 3321 | 9/10 | five brown donuts to the left of six bears to the right of a checkered toy |
| 360 | hard | 2573 | 10/10 | four cars in front of four flamingos in front of seven blue white giraffes |
| 361 | easy | 7947 | 3/4 | a metal red chair |
| 362 | easy | 2587 | 4/4 | four sparkling wooden turtles |
| 363 | easy | 13981 | 5/6 | four giraffes and a blue glass toy |
| 364 | medium | 5761 | 6/6 | six giraffes and four pink spotted flamingos |
| 365 | medium | 3018 | 7/8 | seven cookies in front of six flamingos under a croissant |
| 366 | medium | 4546 | 8/8 | seven backpacks in front of five cats to the left of four violins |
| 367 | hard | 4612 | 9/10 | a lion jumping over five koalas behind six red stone guitars |
| 368 | hard | 2722 | 10/10 | five checkered sheeps on top of six motorcycles in front of six checkered trucks |
| 369 | easy | 8208 | 3/4 | a purple red mushroom |
| 370 | easy | 2600 | 4/4 | seven sparkling blue monkeys |
| 371 | easy | 14044 | 5/6 | a brown stone clock and seven rabbits |
| 372 | medium | 5768 | 6/6 | four flamingos and four wooden plastic trumpets |
| 373 | medium | 3056 | 7/8 | a flower behind four candles to the right of five giraffes |
| 374 | medium | 1433 | 8/9 | a giraffe behind seven purple flowers behind four bears |
| 375 | hard | 2861 | 9/9 | seven raccoons in front of seven sparkling candles on top of four sheeps |
| 376 | hard | 3008 | 10/10 | five cows to the right of five plastic spotted rabbits to the right of five guitars |
| 377 | easy | 8289 | 3/4 | a black plastic elephant |
| 378 | easy | 6096 | 4/5 | a cat chasing two horses |
| 379 | easy | 14294 | 5/6 | a wooden blue pig and five violins |
| 380 | medium | 6067 | 6/6 | six glass wooden bagels and seven flamingos |
| 381 | medium | 2571 | 7/7 | six white rabbits and five spotted wooden suitcases |
| 382 | medium | 4807 | 8/8 | seven trumpets to the right of seven motorcycles under five rabbits |
| 383 | hard | 2876 | 9/9 | four guitars to the left of five koalas under seven striped mushrooms |
| 384 | hard | 3016 | 10/10 | seven bicycles to the left of four purple penguins to the right of five brown violins |
| 385 | easy | 8343 | 3/4 | a black brown mushroom |
| 386 | easy | 13689 | 4/5 | a cow chasing two horses |
| 387 | easy | 14816 | 5/6 | a spotted striped truck and five mushrooms |
| 388 | medium | 6114 | 6/6 | seven zebras and six pink plastic sheeps |
| 389 | medium | 2710 | 7/7 | four white yellow rabbits and seven spotted flowers |
| 390 | medium | 4871 | 8/8 | seven elephants to the left of seven trumpets to the right of five donuts |
| 391 | hard | 3028 | 9/9 | four pigs on top of four checkered candles under six clocks |
| 392 | hard | 3161 | 10/10 | seven sparkling cookies on top of six bears under four blue clocks |
| 393 | easy | 8411 | 3/4 | a red glass candle |
| 394 | easy | 2696 | 4/4 | five pink green dogs |
| 395 | easy | 9493 | 5/5 | four lions chasing four turtles |
| 396 | medium | 6141 | 6/6 | seven spotted checkered koalas and six chairs |
| 397 | medium | 2714 | 7/7 | four metal turtles and four brown purple penguins |
| 398 | medium | 4923 | 8/8 | four bagels in front of four cookies in front of six birds |
| 399 | hard | 3042 | 9/9 | four backpacks in front of five brown mushrooms in front of five bagels |
| 400 | hard | 3276 | 10/10 | five pigs behind seven purple pink sheeps in front of six toys |
| 401 | easy | 8449 | 3/4 | a blue yellow flamingo |
| 402 | easy | 2720 | 4/4 | six striped spotted rabbits |
| 403 | easy | 15672 | 5/6 | a clock and seven purple glass cows |
| 404 | medium | 6189 | 6/6 | five blue yellow motorcycles and six flowers |
| 405 | medium | 4329 | 7/8 | seven pigs to the right of a koala jumping over four elephants |
| 406 | medium | 1445 | 8/9 | seven purple penguins under five bagels on top of a elephant |
| 407 | hard | 3486 | 9/10 | five trucks on top of four clocks to the left of a metal blue sheep |
| 408 | hard | 3336 | 10/10 | seven koalas on top of four chairs to the left of five brown striped candles |
| 409 | easy | 8476 | 3/4 | a striped stone croissant |
| 410 | easy | 2782 | 4/4 | six glass yellow rabbits |
| 411 | easy | 15856 | 5/6 | six trucks and a pink white flamingo |
| 412 | medium | 6197 | 6/6 | four metal red cookies and five lions |
| 413 | medium | 3257 | 7/8 | a koala on top of four flamingos to the right of six guitars |
| 414 | medium | 1509 | 8/8 | seven rabbits to the right of four pigs chasing seven giraffes |
| 415 | hard | 3681 | 9/10 | four cars under a red yellow cow on top of six birds |
| 416 | hard | 3386 | 10/10 | seven purple glass trucks on top of seven umbrellas to the right of seven cows |
| 417 | easy | 8629 | 3/4 | a white brown truck |
| 418 | easy | 2883 | 4/4 | seven striped white dogs |
| 419 | easy | 16123 | 5/6 | a green wooden guitar and five trucks |
| 420 | medium | 6385 | 6/6 | seven turtles and five pink blue trumpets |
| 421 | medium | 3474 | 7/8 | four clocks under seven giraffes under a kangaroo |
| 422 | medium | 5119 | 8/8 | five turtles on top of seven croissants to the right of four candles |
| 423 | hard | 5098 | 9/10 | six lions to the right of a penguin playing with six sparkling blue turtles |
| 424 | hard | 3392 | 10/10 | five trucks under five brown spotted candles to the right of five motorcycles |
| 425 | easy | 8865 | 3/4 | a black wooden bear |
| 426 | easy | 2942 | 4/4 | six brown sparkling trumpets |
| 427 | easy | 16877 | 5/6 | a blue plastic truck and four giraffes |
| 428 | medium | 6432 | 6/6 | seven metal stone horses and five trucks |
| 429 | medium | 3483 | 7/8 | five bears on top of five umbrellas to the right of a cat |
| 430 | medium | 1890 | 8/9 | six bears to the right of four trumpets to the left of a glass car |
| 431 | hard | 3092 | 9/9 | six suitcases to the right of four black penguins to the right of five motorcycles |
| 432 | hard | 2874 | 10/10 | seven pink monkeys chasing six lions behind five checkered cows |
| 433 | easy | 8869 | 3/4 | a black green raccoon |
| 434 | easy | 2972 | 4/4 | five brown metal flamingos |
| 435 | easy | 17488 | 5/6 | a wooden brown candle and five violins |
| 436 | medium | 6445 | 6/6 | seven spotted checkered clocks and six cookies |
| 437 | medium | 3559 | 7/8 | seven cookies behind a rabbit under seven mushrooms |
| 438 | medium | 1976 | 8/9 | a yellow cookie to the right of five kangaroos in front of seven guitars |
| 439 | hard | 3182 | 9/9 | five brown violins to the left of six lions to the right of five raccoons |
| 440 | hard | 3432 | 10/10 | six dogs to the right of six yellow plastic violins to the right of seven sheeps |
| 441 | easy | 8907 | 3/4 | a yellow pink raccoon |
| 442 | easy | 14504 | 4/5 | two raccoons chasing a pig |
| 443 | easy | 17774 | 5/6 | a metal green cat and six bagels |
| 444 | medium | 6582 | 6/6 | four chairs and six blue green toys |
| 445 | medium | 2774 | 7/7 | five glass striped umbrellas and four glass flowers |
| 446 | medium | 5343 | 8/8 | seven pigs in front of six violins behind five trucks |
| 447 | hard | 3248 | 9/9 | four brown flamingos on top of four mushrooms under five sheeps |
| 448 | hard | 3522 | 10/10 | four sparkling trumpets behind five horses to the right of four purple backpacks |
| 449 | easy | 9030 | 3/4 | a purple spotted candle |
| 450 | easy | 3064 | 4/4 | six wooden white cows |
| 451 | easy | 9563 | 5/5 | four koalas chasing five dogs |
| 452 | medium | 6671 | 6/6 | five purple striped clocks and six flowers |
| 453 | medium | 2792 | 7/7 | seven brown sparkling koalas and five black lions |
| 454 | medium | 5363 | 8/8 | six clocks under five kangaroos to the left of four koalas |
| 455 | hard | 3304 | 9/9 | seven cookies to the left of four trucks to the left of five green elephants |
| 456 | hard | 3573 | 10/10 | four pigs to the left of seven giraffes on top of five white red dogs |
| 457 | easy | 9107 | 3/4 | a metal wooden backpack |
| 458 | easy | 3150 | 4/4 | four pink striped violins |
| 459 | easy | 17921 | 5/6 | four flowers and a green sparkling umbrella |
| 460 | medium | 6793 | 6/6 | four birds and five plastic white chairs |
| 461 | medium | 4403 | 7/8 | seven birds playing with a koala to the left of seven trucks |
| 462 | medium | 1977 | 8/9 | a cow to the left of seven suitcases to the left of four green clocks |
| 463 | hard | 3868 | 9/10 | four mushrooms to the left of a white suitcase to the right of five stone kangaroos |
| 464 | hard | 3594 | 10/10 | six candles under six red sparkling horses under five flamingos |
| 465 | easy | 9396 | 3/4 | a checkered glass motorcycle |
| 466 | easy | 3173 | 4/4 | six plastic red koalas |
| 467 | easy | 17951 | 5/6 | seven trucks and a blue black cat |
| 468 | medium | 6815 | 6/6 | seven black plastic toys and four flowers |
| 469 | medium | 3590 | 7/8 | a toy behind six kangaroos under four trucks |
| 470 | medium | 3001 | 8/8 | seven bicycles behind six bears playing with seven giraffes |
| 471 | hard | 3981 | 9/10 | a white yellow dog to the left of six umbrellas to the right of six turtles |
| 472 | hard | 3713 | 10/10 | seven mushrooms to the right of seven plastic black bagels under four umbrellas |
| 473 | easy | 9776 | 3/4 | a wooden metal horse |
| 474 | easy | 3256 | 4/4 | seven blue yellow giraffes |
| 475 | easy | 19376 | 5/6 | a flower and six pink wooden clocks |
| 476 | medium | 6876 | 6/6 | five turtles and seven plastic brown donuts |
| 477 | medium | 3829 | 7/8 | six koalas behind a donut behind seven flowers |
| 478 | medium | 5451 | 8/8 | four trucks to the right of four clocks to the left of seven candles |
| 479 | hard | 5347 | 9/10 | four purple pigs to the right of four rabbits jumping over a checkered penguin |
| 480 | hard | 3755 | 10/10 | six green checkered cookies in front of six kangaroos in front of six flamingos |
| 481 | easy | 9886 | 3/4 | a white purple umbrella |
| 482 | easy | 3377 | 4/4 | five glass metal raccoons |
| 483 | easy | 19388 | 5/6 | a truck and six spotted yellow clocks |
| 484 | medium | 6889 | 6/6 | six spotted striped motorcycles and four umbrellas |
| 485 | medium | 3879 | 7/8 | five trumpets in front of a bear on top of five chairs |
| 486 | medium | 2172 | 8/9 | a blue zebra behind four chairs to the left of five giraffes |
| 487 | hard | 3456 | 9/9 | five red trumpets under six candles behind four cars |
| 488 | hard | 3034 | 10/10 | six striped spotted raccoons on top of five pigs jumping over five giraffes |
| 489 | easy | 9943 | 3/4 | a blue brown giraffe |
| 490 | easy | 3405 | 4/4 | five pink yellow turtles |
| 491 | easy | 19757 | 5/6 | seven donuts and a white checkered candle |
| 492 | medium | 6944 | 6/6 | four penguins and five white glass toys |
| 493 | medium | 3913 | 7/8 | a flamingo under five turtles on top of five mushrooms |
| 494 | medium | 2250 | 8/9 | five spotted cars under six dogs on top of a cow |
| 495 | hard | 3605 | 9/9 | seven blue toys behind five trumpets in front of seven birds |
| 496 | hard | 3784 | 10/10 | six violins behind six plastic glass bears to the right of seven mushrooms |
| 497 | easy | 9975 | 3/4 | a glass white flower |
| 498 | easy | 14977 | 4/5 | a pig chasing two zebras |
| 499 | easy | 19897 | 5/6 | five brown metal candles and a croissant |
| 500 | medium | 6947 | 6/6 | six turtles and six pink stone sheeps |
| 501 | medium | 2899 | 7/7 | seven blue glass giraffes and six purple cookies |
| 502 | medium | 5483 | 8/8 | five cats behind six sheeps to the left of four toys |
| 503 | hard | 3637 | 9/9 | four stone penguins in front of six birds on top of four cows |
| 504 | hard | 3848 | 10/10 | five white backpacks behind six wooden donuts under six monkeys |
| 505 | easy | 10260 | 3/4 | a stone checkered violin |
| 506 | easy | 3570 | 4/4 | six plastic white trucks |
| 507 | easy | 10729 | 5/5 | four elephants chasing four bears |
| 508 | medium | 6971 | 6/6 | six black sparkling birds and six cookies |
| 509 | medium | 2952 | 7/7 | seven black red croissants and five metal bagels |
| 510 | medium | 5566 | 8/8 | five flowers under five clocks under seven horses |
| 511 | hard | 3652 | 9/9 | seven cookies to the right of five white violins on top of seven backpacks |
| 512 | hard | 3891 | 10/10 | four metal blue suitcases behind four clocks to the left of seven guitars |
| 513 | easy | 10276 | 3/4 | a blue wooden rabbit |
| 514 | easy | 3582 | 4/4 | seven wooden black zebras |
| 515 | easy | 713 | 5/6 | a checkered blue truck and two cookies |
| 516 | medium | 9588 | 6/8 | two lions chasing a zebra to the right of a bicycle |
| 517 | medium | 3117 | 7/7 | five spotted purple backpacks and five glass chairs |
| 518 | medium | 5580 | 8/8 | five cows under seven backpacks in front of five cars |
| 519 | hard | 4024 | 9/10 | four monkeys on top of seven yellow black bears to the right of a bagel |
| 520 | hard | 3896 | 10/10 | six striped spotted suitcases to the left of five cookies in front of seven lions |
| 521 | easy | 10331 | 3/4 | a purple striped cat |
| 522 | easy | 3633 | 4/4 | four sparkling white chairs |
| 523 | easy | 1101 | 5/6 | a checkered brown donut and two bears |
| 524 | medium | 7134 | 6/6 | five violins and four wooden black koalas |
| 525 | medium | 4543 | 7/8 | four sheeps to the left of a bird chasing seven horses |
| 526 | medium | 5590 | 8/8 | six chairs to the left of five croissants behind five trumpets |
| 527 | hard | 4044 | 9/10 | four stone mushrooms behind seven monkeys on top of a spotted bagel |
| 528 | hard | 3991 | 10/10 | seven blue raccoons behind seven birds to the right of six spotted flamingos |
| 529 | easy | 10686 | 3/4 | a green sparkling penguin |
| 530 | easy | 3720 | 4/4 | four striped brown raccoons |
| 531 | easy | 1227 | 5/6 | three red checkered violins and a chair |
| 532 | medium | 7290 | 6/6 | six flamingos and five sparkling red pigs |
| 533 | medium | 4033 | 7/8 | a croissant behind six koalas behind four mushrooms |
| 534 | medium | 5688 | 8/8 | five trucks on top of six guitars on top of seven rabbits |
| 535 | hard | 6287 | 9/10 | six mushrooms to the left of four striped red dogs jumping over a elephant |
| 536 | hard | 4095 | 10/10 | seven purple raccoons to the left of seven checkered dogs on top of four bicycles |
| 537 | easy | 10692 | 3/4 | a green brown penguin |
| 538 | easy | 3749 | 4/4 | six plastic white trumpets |
| 539 | easy | 1365 | 5/6 | three purple stone elephants and a turtle |
| 540 | medium | 7291 | 6/6 | six black plastic horses and five cats |
| 541 | medium | 4182 | 7/8 | six elephants to the right of five cookies under a horse |
| 542 | medium | 5730 | 8/8 | four cars under six cats under five chairs |
| 543 | hard | 4060 | 9/10 | a car to the left of six bicycles under six wooden spotted cows |
| 544 | hard | 3316 | 10/10 | six birds playing with seven penguins in front of seven purple red bears |
| 545 | easy | 10714 | 3/4 | a plastic glass kangaroo |
| 546 | easy | 3876 | 4/4 | four wooden white zebras |
| 547 | easy | 1371 | 5/6 | two black stone flowers and a zebra |
| 548 | medium | 7293 | 6/6 | five blue plastic cookies and seven bagels |
| 549 | medium | 4268 | 7/8 | six flowers behind five dogs in front of a bird |
| 550 | medium | 2287 | 8/9 | six toys on top of a purple guitar to the right of seven candles |
| 551 | hard | 3721 | 9/9 | four stone flowers to the left of five cats to the left of four elephants |
| 552 | hard | 4142 | 10/10 | six raccoons to the left of seven birds under five black plastic penguins |
| 553 | easy | 10807 | 3/4 | a purple brown truck |
| 554 | easy | 3898 | 4/4 | six yellow black raccoons |
| 555 | easy | 14502 | 5/5 | six sheeps chasing seven birds |
| 556 | medium | 7363 | 6/6 | six plastic pink bears and four croissants |
| 557 | medium | 3462 | 7/7 | seven red trucks and five yellow red raccoons |
| 558 | medium | 5750 | 8/8 | six rabbits behind four trucks on top of six kangaroos |
| 559 | hard | 3803 | 9/9 | five metal bicycles behind five umbrellas under seven penguins |
| 560 | hard | 4203 | 10/10 | five green giraffes under seven red donuts on top of seven bears |
| 561 | easy | 11038 | 3/4 | a glass metal car |
| 562 | easy | 3946 | 4/4 | six glass pink violins |
| 563 | easy | 16766 | 5/5 | seven penguins chasing six cows |
| 564 | medium | 7473 | 6/6 | six violins and four spotted brown sheeps |
| 565 | medium | 3499 | 7/7 | four brown mushrooms and four glass stone pigs |
| 566 | medium | 5763 | 8/8 | six croissants behind six violins to the right of four trumpets |
| 567 | hard | 3836 | 9/9 | six croissants in front of four checkered pigs under six trucks |
| 568 | hard | 4255 | 10/10 | five monkeys on top of five flamingos behind seven brown glass sheeps |
| 569 | easy | 11116 | 3/4 | a blue brown guitar |
| 570 | easy | 3997 | 4/4 | seven black sparkling violins |
| 571 | easy | 2265 | 5/6 | a striped checkered cow and two clocks |
| 572 | medium | 15688 | 6/8 | a cookie behind a turtle playing with two birds |
| 573 | medium | 3614 | 7/7 | six spotted suitcases and five spotted checkered backpacks |
| 574 | medium | 5991 | 8/8 | five croissants under six giraffes in front of six candles |
| 575 | hard | 4068 | 9/10 | seven sparkling cats to the left of four trumpets to the right of a checkered bear |
| 576 | hard | 4258 | 10/10 | seven umbrellas under four zebras under four spotted black candles |
| 577 | easy | 11372 | 3/4 | a green purple penguin |
| 578 | easy | 4005 | 4/4 | seven stone brown flowers |
| 579 | easy | 2658 | 5/6 | two stone green croissants and a flower |
| 580 | medium | 7605 | 6/6 | seven bagels and seven black wooden trumpets |
| 581 | medium | 5713 | 7/8 | five croissants behind seven lions playing with a elephant |
| 582 | medium | 6018 | 8/8 | four backpacks to the left of four croissants under seven flowers |
| 583 | hard | 4094 | 9/10 | a umbrella to the right of six motorcycles in front of seven green black trucks |
| 584 | hard | 4337 | 10/10 | four sparkling bagels to the left of five metal monkeys to the left of seven rabbits |
| 585 | easy | 11551 | 3/4 | a green brown clock |
| 586 | easy | 4049 | 4/4 | seven striped green pigs |
| 587 | easy | 2769 | 5/6 | a sparkling pink car and three birds |
| 588 | medium | 7973 | 6/6 | four koalas and four striped stone sheeps |
| 589 | medium | 4293 | 7/8 | seven umbrellas on top of a cow to the right of six cats |
| 590 | medium | 6110 | 8/8 | seven violins on top of seven mushrooms to the right of five flamingos |
| 591 | hard | 6501 | 9/10 | a pink zebra chasing five flamingos on top of seven stone guitars |
| 592 | hard | 4362 | 10/10 | four sheeps behind four trucks to the right of four glass black candles |
| 593 | easy | 11595 | 3/4 | a brown yellow cat |
| 594 | easy | 4152 | 4/4 | seven green brown zebras |
| 595 | easy | 3243 | 5/6 | three sparkling plastic kangaroos and a cow |
| 596 | medium | 8037 | 6/6 | five monkeys and four purple sparkling cookies |
| 597 | medium | 4635 | 7/8 | six koalas under seven mushrooms to the left of a guitar |
| 598 | medium | 6159 | 8/8 | seven elephants in front of five suitcases to the right of four cats |
| 599 | hard | 4128 | 9/10 | seven white croissants on top of a donut in front of seven brown kangaroos |
| 600 | hard | 3612 | 10/10 | seven suitcases on top of five metal plastic zebras jumping over seven cats |
| 601 | easy | 11691 | 3/4 | a glass checkered lion |
| 602 | easy | 4178 | 4/4 | six green yellow bagels |
| 603 | easy | 4276 | 5/6 | a striped brown candle and three koalas |
| 604 | medium | 8050 | 6/6 | seven red spotted bagels and seven elephants |
| 605 | medium | 4856 | 7/8 | a car under six trumpets on top of four penguins |
| 606 | medium | 2321 | 8/9 | a monkey on top of seven cows to the left of four yellow bicycles |
| 607 | hard | 3875 | 9/9 | six wooden elephants under six rabbits behind five birds |
| 608 | hard | 4366 | 10/10 | four red green turtles on top of six motorcycles to the right of four horses |
| 609 | easy | 12212 | 3/4 | a plastic red bagel |
| 610 | easy | 4216 | 4/4 | five spotted checkered mushrooms |
| 611 | easy | 16889 | 5/5 | five sheeps chasing six horses |
| 612 | medium | 8056 | 6/6 | six pink white guitars and four clocks |
| 613 | medium | 3804 | 7/7 | four brown violins and five white sparkling birds |
| 614 | medium | 6201 | 8/8 | five cookies under four trumpets to the right of five cows |
| 615 | hard | 3877 | 9/9 | four lions in front of six giraffes on top of five spotted trumpets |
| 616 | hard | 4483 | 10/10 | seven chairs to the left of four pink blue bicycles behind seven koalas |
| 617 | easy | 12319 | 3/4 | a black stone backpack |
| 618 | easy | 4233 | 4/4 | five plastic red turtles |
| 619 | easy | 17150 | 5/5 | seven horses chasing six pigs |
| 620 | medium | 8224 | 6/6 | seven purple striped sheeps and five flamingos |
| 621 | medium | 4089 | 7/7 | four stone green kangaroos and four brown turtles |
| 622 | medium | 6243 | 8/8 | four kangaroos to the left of seven monkeys under four trumpets |
| 623 | hard | 3878 | 9/9 | six clocks to the left of five cats in front of seven checkered trumpets |
| 624 | hard | 4530 | 10/10 | six metal wooden elephants to the left of seven trucks on top of six motorcycles |
| 625 | easy | 12360 | 3/4 | a checkered striped violin |
| 626 | easy | 4259 | 4/4 | six wooden purple suitcases |
| 627 | easy | 5315 | 5/6 | a glass stone motorcycle and three turtles |
| 628 | medium | 17435 | 6/8 | a turtle playing with two penguins in front of a guitar |
| 629 | medium | 4146 | 7/7 | five plastic croissants and six stone brown rabbits |
| 630 | medium | 6333 | 8/8 | five kangaroos in front of five birds in front of seven guitars |
| 631 | hard | 4181 | 9/10 | a stone cow behind seven backpacks on top of four white koalas |
| 632 | hard | 4550 | 10/10 | seven black bagels in front of seven wooden clocks behind six sheeps |
| 633 | easy | 12464 | 3/4 | a glass spotted backpack |
| 634 | easy | 4311 | 4/4 | seven glass blue rabbits |
| 635 | easy | 5615 | 5/6 | a trumpet and three stone yellow monkeys |
| 636 | medium | 8254 | 6/6 | seven donuts and seven yellow metal elephants |
| 637 | medium | 6160 | 7/8 | seven turtles playing with a raccoon under seven chairs |
| 638 | medium | 6386 | 8/8 | five guitars behind five dogs to the right of four motorcycles |
| 639 | hard | 4298 | 9/10 | five giraffes in front of five striped white zebras in front of a cookie |
| 640 | hard | 4681 | 10/10 | six backpacks behind five stone black cows behind seven birds |
| 641 | easy | 12608 | 3/4 | a brown red candle |
| 642 | easy | 4396 | 4/4 | five black glass zebras |
| 643 | easy | 5885 | 5/6 | a green glass lion and three umbrellas |
| 644 | medium | 8271 | 6/6 | four pink white birds and six rabbits |
| 645 | medium | 4907 | 7/8 | a giraffe behind four penguins on top of seven cars |
| 646 | medium | 3885 | 8/8 | six pigs behind four lions playing with four turtles |
| 647 | hard | 4339 | 9/10 | four pigs under a red white cookie to the right of five sheeps |
| 648 | hard | 4831 | 10/10 | five yellow zebras on top of five suitcases to the right of six checkered horses |
| 649 | easy | 12829 | 3/4 | a glass yellow donut |
| 650 | easy | 4535 | 4/4 | five striped purple lions |
| 651 | easy | 6226 | 5/6 | two yellow stone clocks and a penguin |
| 652 | medium | 8380 | 6/6 | seven blue plastic flowers and six chairs |
| 653 | medium | 5144 | 7/8 | five dogs to the left of a guitar on top of five turtles |
| 654 | medium | 6397 | 8/8 | four giraffes in front of six toys to the right of seven sheeps |
| 655 | hard | 4415 | 9/10 | a cow on top of seven trumpets on top of four yellow checkered giraffes |
| 656 | hard | 3820 | 10/10 | four cows chasing six turtles to the left of four black blue trucks |
| 657 | easy | 13107 | 3/4 | a blue plastic monkey |
| 658 | easy | 4737 | 4/4 | seven wooden checkered bicycles |
| 659 | easy | 8881 | 5/6 | a chair and two brown striped dogs |
| 660 | medium | 8388 | 6/6 | six spotted pink clocks and seven chairs |
| 661 | medium | 5169 | 7/8 | seven motorcycles under seven zebras under a umbrella |
| 662 | medium | 2340 | 8/9 | a cat in front of four white trumpets to the left of five sheeps |
| 663 | hard | 3957 | 9/9 | four lions behind seven plastic umbrellas behind seven guitars |
| 664 | hard | 4833 | 10/10 | five flowers behind five wooden candles under six brown dogs |
| 665 | easy | 13141 | 3/4 | a brown glass pig |
| 666 | easy | 4836 | 4/4 | six black pink donuts |
| 667 | easy | 17168 | 5/5 | seven sheeps chasing seven cows |
| 668 | medium | 8440 | 6/6 | seven sparkling wooden raccoons and six giraffes |
| 669 | medium | 4169 | 7/7 | seven stone sparkling bears and four red raccoons |
| 670 | medium | 6406 | 8/8 | seven motorcycles to the left of six cats to the left of five toys |
| 671 | hard | 3985 | 9/9 | four glass cars under six elephants behind seven trumpets |
| 672 | hard | 4905 | 10/10 | seven candles behind five plastic bicycles to the right of seven plastic croissants |
| 673 | easy | 13420 | 3/4 | a metal stone guitar |
| 674 | easy | 4849 | 4/4 | four pink glass backpacks |
| 675 | easy | 18582 | 5/5 | five rabbits chasing six raccoons |
| 676 | medium | 8452 | 6/6 | seven elephants and five glass checkered violins |
| 677 | medium | 4241 | 7/7 | six wooden striped cookies and seven blue bicycles |
| 678 | medium | 6447 | 8/8 | six motorcycles to the right of five lions to the right of four trucks |
| 679 | hard | 4014 | 9/9 | four trucks to the right of four blue chairs on top of six candles |
| 680 | hard | 4909 | 10/10 | five mushrooms to the right of four dogs in front of seven wooden spotted horses |
| 681 | easy | 13538 | 3/4 | a white red backpack |
| 682 | easy | 4933 | 4/4 | seven brown green bears |
| 683 | easy | 9045 | 5/6 | a candle and three brown red bears |
| 684 | medium | 1816 | 6/6 | seven bears playing with six plastic monkeys |
| 685 | medium | 4286 | 7/7 | six yellow wooden cookies and four spotted rabbits |
| 686 | medium | 6489 | 8/8 | six pigs to the left of seven guitars under seven monkeys |
| 687 | hard | 4211 | 9/9 | five giraffes in front of five violins under five purple toys |
| 688 | hard | 4925 | 10/10 | seven croissants under seven suitcases on top of seven green white cookies |
| 689 | easy | 13576 | 3/4 | a black spotted monkey |
| 690 | easy | 4937 | 4/4 | seven blue metal birds |
| 691 | easy | 11320 | 5/6 | a bear and three plastic metal umbrellas |
| 692 | medium | 8480 | 6/6 | four plastic blue turtles and six raccoons |
| 693 | medium | 7632 | 7/8 | six koalas playing with seven turtles to the left of a monkey |
| 694 | medium | 6526 | 8/8 | seven toys behind five flamingos in front of four trucks |
| 695 | hard | 4450 | 9/10 | five metal cookies behind five checkered umbrellas under a penguin |
| 696 | hard | 4952 | 10/10 | five trucks in front of four stone blue lions on top of four elephants |
| 697 | easy | 14039 | 3/4 | a plastic white elephant |
| 698 | easy | 4982 | 4/4 | four green spotted flowers |
| 699 | easy | 11781 | 5/6 | a croissant and two plastic sparkling kangaroos |
| 700 | medium | 8486 | 6/6 | six zebras and five green checkered rabbits |
| 701 | medium | 5309 | 7/8 | a bagel to the left of five flamingos to the right of five chairs |
| 702 | medium | 4412 | 8/8 | five croissants to the right of seven bears chasing seven elephants |
| 703 | hard | 4528 | 9/10 | four brown green mushrooms on top of six monkeys on top of a clock |
| 704 | hard | 4963 | 10/10 | six wooden giraffes in front of five blue umbrellas behind seven cows |
| 705 | easy | 14120 | 3/4 | a yellow black bird |
| 706 | easy | 5111 | 4/4 | six green yellow flamingos |
| 707 | easy | 12595 | 5/6 | two glass green giraffes and a violin |
| 708 | medium | 8524 | 6/6 | five flamingos and six pink glass horses |
| 709 | medium | 5365 | 7/8 | five mushrooms to the right of five birds under a monkey |
| 710 | medium | 6548 | 8/8 | five kangaroos behind six turtles behind five clocks |
| 711 | hard | 4533 | 9/10 | five black koalas to the left of seven green backpacks on top of a trumpet |
| 712 | hard | 3960 | 10/10 | five sheeps to the left of five pink rabbits chasing seven striped elephants |
| 713 | easy | 14137 | 3/4 | a green spotted toy |
| 714 | easy | 5182 | 4/4 | four black red lions |
| 715 | easy | 12927 | 5/6 | a sheep and three metal yellow candles |
| 716 | medium | 8562 | 6/6 | seven umbrellas and seven blue brown cows |
| 717 | medium | 5392 | 7/8 | a zebra on top of six motorcycles on top of seven bicycles |
| 718 | medium | 2442 | 8/9 | four bagels to the left of five yellow flowers under a truck |
| 719 | hard | 4238 | 9/9 | six spotted donuts on top of six lions to the right of five flamingos |
| 720 | hard | 4967 | 10/10 | seven striped sheeps on top of seven cookies to the right of five wooden zebras |
| 721 | easy | 14164 | 3/4 | a striped glass rabbit |
| 722 | easy | 5183 | 4/4 | six green purple dogs |
| 723 | easy | 19672 | 5/5 | four monkeys chasing six birds |
| 724 | medium | 8741 | 6/6 | four green brown horses and six monkeys |
| 725 | medium | 4735 | 7/7 | five plastic mushrooms and four pink green dogs |
| 726 | medium | 6598 | 8/8 | five backpacks to the right of five giraffes on top of seven raccoons |
| 727 | hard | 4316 | 9/9 | seven violins to the left of four cars under four plastic motorcycles |
| 728 | hard | 5206 | 10/10 | seven green flamingos under four trumpets to the left of four brown giraffes |
| 729 | easy | 14365 | 3/4 | a wooden white monkey |
| 730 | easy | 5223 | 4/4 | four stone red mushrooms |
| 731 | easy | 2198 | 5/5 | two rabbits chasing four elephants |
| 732 | medium | 8746 | 6/6 | seven bears and five checkered white flamingos |
| 733 | medium | 4775 | 7/7 | six white turtles and five yellow pink violins |
| 734 | medium | 6749 | 8/8 | five mushrooms on top of five backpacks under four violins |
| 735 | hard | 4437 | 9/9 | seven giraffes to the left of five black candles under seven bears |
| 736 | hard | 5215 | 10/10 | six pigs under five violins behind seven spotted checkered rabbits |
| 737 | easy | 14419 | 3/4 | a glass red monkey |
| 738 | easy | 5256 | 4/4 | six wooden purple flowers |
| 739 | easy | 13267 | 5/6 | a flamingo and two glass red flowers |
| 740 | medium | 5053 | 6/6 | four horses chasing six spotted giraffes |
| 741 | medium | 4865 | 7/7 | four checkered elephants and seven brown black donuts |
| 742 | medium | 6930 | 8/8 | six backpacks behind four raccoons to the right of five sheeps |
| 743 | hard | 4488 | 9/9 | six purple croissants to the left of six candles under four umbrellas |
| 744 | hard | 5254 | 10/10 | four bicycles to the left of four violins behind five purple yellow turtles |
| 745 | easy | 14522 | 3/4 | a stone metal koala |
| 746 | easy | 5331 | 4/4 | four sparkling pink clocks |
| 747 | easy | 13807 | 5/6 | two red blue rabbits and a bird |
| 748 | medium | 8806 | 6/6 | five mushrooms and four black white donuts |
| 749 | medium | 8076 | 7/8 | five backpacks to the left of four dogs chasing a flamingo |
| 750 | medium | 6994 | 8/8 | five cars to the right of seven motorcycles to the right of seven monkeys |
| 751 | hard | 4554 | 9/10 | five trucks under seven wooden blue bicycles behind a flamingo |
| 752 | hard | 5338 | 10/10 | five flowers in front of four sheeps under five wooden stone giraffes |
| 753 | easy | 14543 | 3/4 | a pink stone raccoon |
| 754 | easy | 5337 | 4/4 | seven green striped guitars |
| 755 | easy | 13900 | 5/6 | three violins and a green pink backpack |
| 756 | medium | 8843 | 6/6 | six bagels and four metal pink turtles |
| 757 | medium | 5684 | 7/8 | five mushrooms to the right of seven flamingos in front of a dog |
| 758 | medium | 5040 | 8/8 | four birds on top of four turtles playing with seven dogs |
| 759 | hard | 4653 | 9/10 | six glass wooden cookies to the right of a elephant to the right of six suitcases |
| 760 | hard | 5476 | 10/10 | seven white black candles behind five lions under five bagels |
| 761 | easy | 14670 | 3/4 | a yellow red mushroom |
| 762 | easy | 5460 | 4/4 | five wooden black mushrooms |
| 763 | easy | 14192 | 5/6 | three spotted checkered chairs and a donut |
| 764 | medium | 8846 | 6/6 | four croissants and six red yellow backpacks |
| 765 | medium | 5738 | 7/8 | six cars under a candle in front of six guitars |
| 766 | medium | 7032 | 8/8 | six donuts behind seven bears on top of six birds |
| 767 | hard | 6982 | 9/10 | six horses playing with a checkered rabbit behind five black trumpets |
| 768 | hard | 5504 | 10/10 | five lions behind four bicycles to the right of six plastic stone kangaroos |
| 769 | easy | 14725 | 3/4 | a stone checkered horse |
| 770 | easy | 5512 | 4/4 | six white black bagels |
| 771 | easy | 14218 | 5/6 | a sparkling purple monkey and two clocks |
| 772 | medium | 8885 | 6/6 | four mushrooms and four pink checkered horses |
| 773 | medium | 5805 | 7/8 | five sheeps to the left of five turtles to the right of a flamingo |
| 774 | medium | 2532 | 8/9 | six dogs on top of four penguins under a yellow bicycle |
| 775 | hard | 4512 | 9/9 | four mushrooms to the right of five wooden bicycles under seven umbrellas |
| 776 | hard | 5542 | 10/10 | four checkered dogs under four zebras on top of six green trumpets |
| 777 | easy | 14945 | 3/4 | a spotted striped dog |
| 778 | easy | 5524 | 4/4 | five sparkling stone cows |
| 779 | easy | 3045 | 5/5 | three elephants chasing five raccoons |
| 780 | medium | 9027 | 6/6 | seven metal yellow cows and four toys |
| 781 | medium | 4885 | 7/7 | six spotted wooden mushrooms and four blue umbrellas |
| 782 | medium | 7036 | 8/8 | four clocks in front of six mushrooms on top of four cows |
| 783 | hard | 4526 | 9/9 | seven plastic pigs in front of seven umbrellas in front of six candles |
| 784 | hard | 5556 | 10/10 | six trumpets on top of six wooden brown cars on top of six giraffes |
| 785 | easy | 14958 | 3/4 | a spotted brown donut |
| 786 | easy | 5798 | 4/4 | four wooden striped flamingos |
| 787 | easy | 3130 | 5/5 | four raccoons chasing three pigs |
| 788 | medium | 9103 | 6/6 | seven bears and four green striped umbrellas |
| 789 | medium | 5087 | 7/7 | seven wooden backpacks and five white plastic horses |
| 790 | medium | 7088 | 8/8 | six zebras on top of four giraffes on top of five koalas |
| 791 | hard | 4614 | 9/9 | seven checkered turtles in front of four trumpets behind seven cookies |
| 792 | hard | 5596 | 10/10 | seven flowers to the left of seven plastic red sheeps behind seven birds |
| 793 | easy | 15070 | 3/4 | a purple pink elephant |
| 794 | easy | 5951 | 4/4 | five red wooden cars |
| 795 | easy | 4559 | 5/5 | seven kangaroos chasing three cows |
| 796 | medium | 9126 | 6/6 | four koalas and six metal plastic clocks |
| 797 | medium | 5155 | 7/7 | six wooden plastic zebras and four blue flamingos |
| 798 | medium | 7100 | 8/8 | six mushrooms under four koalas in front of seven trumpets |
| 799 | hard | 4682 | 9/9 | four metal mushrooms under five kangaroos on top of seven donuts |
| 800 | hard | 5598 | 10/10 | six striped blue zebras to the left of seven turtles under six cookies |
| 801 | easy | 15517 | 3/4 | a stone white chair |
| 802 | easy | 6072 | 4/4 | five black purple umbrellas |
| 803 | easy | 14266 | 5/6 | a spotted purple flamingo and three motorcycles |
| 804 | medium | 9161 | 6/6 | seven metal spotted elephants and six lions |
| 805 | medium | 8711 | 7/8 | seven donuts to the left of six kangaroos chasing a bird |
| 806 | medium | 2589 | 8/9 | a candle to the right of six croissants to the left of four yellow turtles |
| 807 | hard | 4710 | 9/10 | five elephants behind a blue red chair under six monkeys |
| 808 | hard | 5677 | 10/10 | six green suitcases on top of four bicycles under four blue horses |
| 809 | easy | 15539 | 3/4 | a stone blue trumpet |
| 810 | easy | 6073 | 4/4 | five glass checkered mushrooms |
| 811 | easy | 14431 | 5/6 | a checkered wooden kangaroo and three cars |
| 812 | medium | 9745 | 6/6 | five bears and seven striped purple kangaroos |
| 813 | medium | 5845 | 7/8 | a clock to the right of four cookies to the left of five turtles |
| 814 | medium | 6358 | 8/8 | four chairs in front of four rabbits playing with seven kangaroos |
| 815 | hard | 4884 | 9/10 | seven croissants under a striped chair under seven blue cars |
| 816 | hard | 5767 | 10/10 | six metal guitars on top of seven zebras to the right of six black lions |
| 817 | easy | 15553 | 3/4 | a black sparkling bird |
| 818 | easy | 6092 | 4/4 | four metal pink pigs |
| 819 | easy | 15236 | 5/6 | a zebra and three checkered blue toys |
| 820 | medium | 9868 | 6/6 | seven penguins and six yellow red sheeps |
| 821 | medium | 5920 | 7/8 | six cookies to the right of a turtle under five candles |
| 822 | medium | 7180 | 8/8 | five motorcycles behind seven toys in front of seven clocks |
| 823 | hard | 7565 | 9/10 | five giraffes chasing five white raccoons on top of a green pig |
| 824 | hard | 5803 | 10/10 | five trucks behind six yellow checkered candles to the right of six donuts |
| 825 | easy | 15852 | 3/4 | a sparkling yellow car |
| 826 | easy | 6122 | 4/4 | five striped metal mushrooms |
| 827 | easy | 15732 | 5/6 | two spotted white koalas and a pig |
| 828 | medium | 9979 | 6/6 | four elephants and five black wooden turtles |
| 829 | medium | 6101 | 7/8 | a horse to the right of six mushrooms to the right of six flamingos |
| 830 | medium | 2795 | 8/9 | five glass cars under a cookie to the right of six sheeps |
| 831 | hard | 4778 | 9/9 | five green horses on top of seven trucks under five chairs |
| 832 | hard | 3977 | 10/10 | seven rabbits playing with seven pigs to the right of four black wooden backpacks |
| 833 | easy | 16028 | 3/4 | a black stone lion |
| 834 | easy | 6150 | 4/4 | six blue brown croissants |
| 835 | easy | 15808 | 5/6 | three red white zebras and a bagel |
| 836 | medium | 9989 | 6/6 | four pink stone kangaroos and six zebras |
| 837 | medium | 6154 | 7/8 | a umbrella behind six sheeps in front of five penguins |
| 838 | medium | 3111 | 8/9 | four pink raccoons to the right of a mushroom to the left of six elephants |
| 839 | hard | 4779 | 9/9 | seven backpacks in front of seven glass cows on top of four bagels |
| 840 | hard | 5867 | 10/10 | six mushrooms to the left of six candles to the left of four black brown donuts |
| 841 | easy | 16386 | 3/4 | a checkered striped cookie |
| 842 | easy | 6171 | 4/4 | four sparkling plastic flowers |
| 843 | easy | 8890 | 5/5 | three zebras chasing six turtles |
| 844 | medium | 9997 | 6/6 | seven black spotted umbrellas and four pigs |
| 845 | medium | 5237 | 7/7 | four stone giraffes and seven yellow green toys |
| 846 | medium | 7267 | 8/8 | six monkeys to the left of seven penguins in front of six cows |
| 847 | hard | 4872 | 9/9 | five plastic kangaroos to the left of six flowers to the right of five motorcycles |
| 848 | hard | 5875 | 10/10 | seven blue stone trucks under six koalas in front of six bears |
| 849 | easy | 16497 | 3/4 | a metal black truck |
| 850 | easy | 6190 | 4/4 | six checkered spotted rabbits |
| 851 | easy | 10216 | 5/5 | four cats chasing three giraffes |
| 852 | medium | 10147 | 6/6 | five turtles and seven green spotted motorcycles |
| 853 | medium | 5273 | 7/7 | five spotted monkeys and four stone white horses |
| 854 | medium | 7433 | 8/8 | four giraffes to the left of four cookies on top of five trumpets |
| 855 | hard | 4912 | 9/9 | four cats behind seven koalas to the left of five green pigs |
| 856 | hard | 5975 | 10/10 | seven striped bicycles on top of five white kangaroos in front of seven horses |
| 857 | easy | 16603 | 3/4 | a metal yellow chair |
| 858 | easy | 6225 | 4/4 | seven checkered green cows |
| 859 | easy | 16934 | 5/6 | three glass plastic lions and a umbrella |
| 860 | medium | 10206 | 6/6 | four donuts and seven purple sparkling cookies |
| 861 | medium | 8850 | 7/8 | a horse jumping over six raccoons to the right of four flowers |
| 862 | medium | 3124 | 8/9 | seven glass cars under seven elephants to the right of a truck |
| 863 | hard | 4918 | 9/10 | a brown croissant to the right of seven striped donuts to the left of four penguins |
| 864 | hard | 5987 | 10/10 | four plastic spotted cars to the right of seven cows to the left of five flowers |
| 865 | easy | 16689 | 3/4 | a brown white sheep |
| 866 | easy | 6280 | 4/4 | six blue red birds |
| 867 | easy | 17640 | 5/6 | three checkered stone umbrellas and a guitar |
| 868 | medium | 10337 | 6/6 | four brown metal cars and seven croissants |
| 869 | medium | 6170 | 7/8 | a violin behind four monkeys on top of seven guitars |
| 870 | medium | 6636 | 8/8 | five penguins jumping over five turtles to the left of six pigs |
| 871 | hard | 4942 | 9/10 | six spotted candles to the left of four green bears under a umbrella |
| 872 | hard | 6151 | 10/10 | seven spotted pink elephants under four cows under four giraffes |
| 873 | easy | 16723 | 3/4 | a red striped truck |
| 874 | easy | 6340 | 4/4 | seven wooden green cars |
| 875 | easy | 18090 | 5/6 | three stone purple zebras and a sheep |
| 876 | medium | 10458 | 6/6 | seven yellow red clocks and six kangaroos |
| 877 | medium | 6209 | 7/8 | seven umbrellas in front of seven cats on top of a elephant |
| 878 | medium | 7501 | 8/8 | four koalas behind five flowers on top of seven pigs |
| 879 | hard | 7692 | 9/10 | a flamingo playing with seven blue green birds behind five umbrellas |
| 880 | hard | 6235 | 10/10 | seven elephants behind four green motorcycles under five pink turtles |
| 881 | easy | 16751 | 3/4 | a spotted striped mushroom |
| 882 | easy | 6360 | 4/4 | four striped sparkling zebras |
| 883 | easy | 18869 | 5/6 | two red green suitcases and a umbrella |
| 884 | medium | 10562 | 6/6 | five pigs and four green black flowers |
| 885 | medium | 6281 | 7/8 | a bicycle behind four rabbits in front of four flowers |
| 886 | medium | 3180 | 8/9 | a flower in front of six striped mushrooms under six dogs |
| 887 | hard | 4932 | 9/9 | six brown penguins to the left of seven dogs under four motorcycles |
| 888 | hard | 4252 | 10/10 | six raccoons chasing four glass blue lions to the right of six cars |
| 889 | easy | 16800 | 3/4 | a striped spotted donut |
| 890 | easy | 6387 | 4/4 | seven metal blue motorcycles |
| 891 | easy | 144 | 5/7 | a blue glass guitar and a brown cow |
| 892 | medium | 10603 | 6/6 | six violins and six striped brown cats |
| 893 | medium | 6437 | 7/8 | seven mushrooms on top of a clock under six trucks |
| 894 | medium | 7536 | 8/8 | five flamingos to the right of six zebras to the left of five cats |
| 895 | hard | 5023 | 9/9 | five chairs behind six motorcycles in front of five blue croissants |
| 896 | hard | 6292 | 10/10 | four croissants in front of five checkered backpacks behind six white raccoons |
| 897 | easy | 16852 | 3/4 | a yellow stone raccoon |
| 898 | easy | 6416 | 4/4 | seven blue stone koalas |
| 899 | easy | 11433 | 5/5 | five koalas chasing three monkeys |
| 900 | medium | 10793 | 6/6 | six cookies and four spotted glass bicycles |
| 901 | medium | 5503 | 7/7 | seven red brown cars and four black flowers |
| 902 | medium | 7726 | 8/8 | five elephants to the left of seven raccoons to the left of seven violins |
| 903 | hard | 5086 | 9/9 | four pink mushrooms on top of four candles in front of seven penguins |
| 904 | hard | 6310 | 10/10 | five horses to the left of seven blue clocks behind five blue pigs |
| 905 | easy | 17141 | 3/4 | a blue yellow candle |
| 906 | easy | 6453 | 4/4 | seven red checkered giraffes |
| 907 | easy | 12543 | 5/5 | two horses chasing five zebras |
| 908 | medium | 10847 | 6/6 | seven bicycles and six sparkling checkered cookies |
| 909 | medium | 5792 | 7/7 | four striped dogs and six green glass mushrooms |
| 910 | medium | 7779 | 8/8 | seven flamingos in front of five donuts to the right of seven elephants |
| 911 | hard | 5175 | 9/9 | five blue clocks to the right of five bagels to the left of five suitcases |
| 912 | hard | 6336 | 10/10 | seven turtles in front of four wooden black backpacks behind six motorcycles |
| 913 | easy | 17167 | 3/4 | a red checkered bicycle |
| 914 | easy | 6459 | 4/4 | six black brown suitcases |
| 915 | easy | 282 | 5/7 | a striped plastic cookie and a white clock |
| 916 | medium | 6751 | 6/6 | five turtles chasing four spotted birds |
| 917 | medium | 6589 | 7/8 | seven candles in front of four chairs behind a cookie |
| 918 | medium | 3208 | 8/9 | a candle to the right of six trumpets behind four red clocks |
| 919 | hard | 5103 | 9/10 | a brown black bird on top of seven cars in front of five umbrellas |
| 920 | hard | 6343 | 10/10 | seven white rabbits behind four flowers on top of seven black birds |
| 921 | easy | 17276 | 3/4 | a wooden black clock |
| 922 | easy | 6473 | 4/4 | seven brown red koalas |
| 923 | easy | 11619 | 5/7 | a blue car and a pink stone penguin |
| 924 | medium | 10872 | 6/6 | five pink checkered guitars and six cookies |
| 925 | medium | 9508 | 7/8 | four sheeps jumping over a dog under five elephants |
| 926 | medium | 8031 | 8/8 | five bicycles to the right of seven cows to the right of four raccoons |
| 927 | hard | 5257 | 9/9 | seven checkered raccoons behind seven dogs on top of seven horses |
| 928 | hard | 6438 | 10/10 | six turtles to the right of six stone flowers in front of four sparkling mushrooms |
| 929 | easy | 17499 | 3/4 | a metal checkered rabbit |
| 930 | easy | 6482 | 4/4 | five spotted checkered croissants |
| 931 | easy | 16821 | 5/7 | a wooden yellow cookie and a plastic sheep |
| 932 | medium | 10873 | 6/6 | six flowers and five sparkling spotted donuts |
| 933 | medium | 6665 | 7/8 | five penguins to the left of seven backpacks to the left of a lion |
| 934 | medium | 8092 | 8/8 | four croissants in front of four cars behind four candles |
| 935 | hard | 155 | 9/9 | seven raccoons chasing five striped monkeys in front of five cookies |
| 936 | hard | 6452 | 10/10 | six glass trumpets in front of four blue cats in front of four backpacks |
| 937 | easy | 17524 | 3/4 | a sparkling checkered turtle |
| 938 | easy | 6490 | 4/4 | six pink metal dogs |
| 939 | easy | 4826 | 5/7 | a glass yellow motorcycle in front of a umbrella |
| 940 | medium | 10970 | 6/6 | seven kangaroos and six metal pink bagels |
| 941 | medium | 6781 | 7/8 | five umbrellas in front of a zebra to the left of five monkeys |
| 942 | medium | 8093 | 8/8 | four monkeys to the right of five violins in front of six sheeps |
| 943 | hard | 5115 | 9/10 | five plastic mushrooms under a car on top of seven striped lions |
| 944 | hard | 4605 | 10/10 | four cows playing with six raccoons on top of five pink wooden chairs |
| 945 | easy | 17648 | 3/4 | a checkered wooden clock |
| 946 | easy | 6516 | 4/4 | five metal sparkling candles |
| 947 | easy | 7904 | 5/7 | a pig under a green wooden cow |
| 948 | medium | 10977 | 6/6 | six monkeys and seven white pink croissants |
| 949 | medium | 7106 | 7/8 | a backpack on top of four cows under seven guitars |
| 950 | medium | 3448 | 8/9 | four kangaroos to the right of seven candles to the left of a wooden sheep |
| 951 | hard | 5275 | 9/9 | four dogs on top of seven bagels to the left of six stone guitars |
| 952 | hard | 6471 | 10/10 | six candles under five checkered elephants on top of five blue rabbits |
| 953 | easy | 17679 | 3/4 | a black metal violin |
| 954 | easy | 6568 | 4/4 | seven sparkling wooden violins |
| 955 | easy | 13399 | 5/5 | three cats chasing five sheeps |
| 956 | medium | 11280 | 6/6 | five cars and six striped red rabbits |
| 957 | medium | 5962 | 7/7 | five metal yellow sheeps and five metal cars |
| 958 | medium | 8206 | 8/8 | five monkeys under four lions to the left of four suitcases |
| 959 | hard | 5329 | 9/9 | five elephants behind six blue rabbits behind five birds |
| 960 | hard | 6592 | 10/10 | seven spotted candles on top of four metal trumpets on top of four backpacks |
| 961 | easy | 17793 | 3/4 | a white red koala |
| 962 | easy | 6691 | 4/4 | five stone plastic trumpets |
| 963 | easy | 13800 | 5/5 | two giraffes chasing five lions |
| 964 | medium | 11299 | 6/6 | seven yellow plastic koalas and four monkeys |
| 965 | medium | 5974 | 7/7 | seven metal cows and four pink stone chairs |
| 966 | medium | 8232 | 8/8 | four cows to the left of five trumpets behind seven elephants |
| 967 | hard | 5419 | 9/9 | six cows to the left of five spotted monkeys in front of six trucks |
| 968 | hard | 6597 | 10/10 | six spotted suitcases behind seven glass pigs behind five penguins |
| 969 | easy | 18024 | 3/4 | a brown striped cookie |
| 970 | easy | 6874 | 4/4 | seven metal yellow croissants |
| 971 | easy | 10357 | 5/7 | a white pink clock in front of a truck |
| 972 | medium | 9335 | 6/6 | seven lions playing with four purple giraffes |
| 973 | medium | 5988 | 7/7 | seven sparkling wooden trumpets and seven red toys |
| 974 | medium | 8262 | 8/8 | four cows on top of six dogs on top of four trucks |
| 975 | hard | 5485 | 9/9 | seven suitcases in front of six brown cats to the left of four flowers |
| 976 | hard | 6633 | 10/10 | six sparkling yellow violins behind four suitcases behind seven birds |
| 977 | easy | 18092 | 3/4 | a red plastic umbrella |
| 978 | easy | 6887 | 4/4 | four metal checkered chairs |
| 979 | easy | 11662 | 5/7 | a white metal kangaroo on top of a cookie |
| 980 | medium | 11306 | 6/6 | five raccoons and five green yellow lions |
| 981 | medium | 10249 | 7/8 | six raccoons playing with five kangaroos on top of a flower |
| 982 | medium | 8344 | 8/8 | seven turtles in front of seven cars behind seven koalas |
| 983 | hard | 5133 | 9/10 | a motorcycle to the right of seven plastic clocks in front of four sparkling sheeps |
| 984 | hard | 6679 | 10/10 | seven black donuts behind four red chairs in front of six horses |
| 985 | easy | 18295 | 3/4 | a wooden stone flamingo |
| 986 | easy | 6896 | 4/4 | five plastic purple sheeps |
| 987 | easy | 15202 | 5/7 | a stone red backpack behind a suitcase |
| 988 | medium | 11353 | 6/6 | seven koalas and five pink plastic bears |
| 989 | medium | 7114 | 7/8 | a chair in front of four motorcycles to the left of four turtles |
| 990 | medium | 8368 | 8/8 | four zebras in front of six birds behind five rabbits |
| 991 | hard | 7773 | 9/10 | a wooden horse chasing four elephants to the right of six green cars |
| 992 | hard | 6698 | 10/10 | six flamingos to the right of five yellow umbrellas in front of seven yellow bears |
| 993 | easy | 18623 | 3/4 | a striped checkered lion |
| 994 | easy | 6996 | 4/4 | five black checkered backpacks |
| 995 | easy | 18499 | 5/7 | a kangaroo behind a red glass motorcycle |
| 996 | medium | 11486 | 6/6 | six striped plastic cars and five turtles |
| 997 | medium | 7166 | 7/8 | a croissant behind seven trumpets on top of seven pigs |
| 998 | medium | 8383 | 8/8 | six horses under six clocks on top of seven chairs |
| 999 | hard | 5194 | 9/10 | a zebra under seven wooden dogs in front of four red suitcases |
| 1000 | hard | 4763 | 10/10 | five suitcases behind five plastic sheeps chasing six spotted dogs |

Each selected record in the JSON artifact retains the original `vqa_list`, `skills`, normalized atomic constraints, score components, source line, row hash, and dataset hash.
