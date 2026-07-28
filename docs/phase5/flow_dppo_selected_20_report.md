# Flow-DPPO Geneval2 20-Prompt Selection

## Policy

- Source: `Tencent-Hunyuan/UniRL@e1a814ff9de6de644b093c6ed0106869c1881e53`
- Dataset: `datasets/geneval2/synthetic/train.jsonl`
- Source rows: 20000
- Rows where `atom_count != len(vqa_list)`: 6007
- Official 800-row Geneval2 test set remains held out.
- Held-out boundary: exact prompt overlaps excluded=0; semantic-family overlaps excluded=9650.
- Tier mix: hard=12, medium=5, easy=3
- Selection is deterministic and uses metadata/semantic diversity only; no live image result is used.

## Coverage

- Selected prompts: 20
- Distinct entities: 40
- Relation/action phrases: behind, chasing, in front of, jumping over, on top of, playing with, to the left of, to the right of, under
- Constraint atoms: attribute=49, count=57, object=57, position=22, verb=15

## Selected Rows

| Rank | Tier | Source line | Atoms/VQAs | Prompt |
|---:|---|---:|---:|---|
| 1 | hard | 427 | 10/11 | a bird playing with six blue white cows under seven spotted suitcases |
| 2 | hard | 2900 | 10/11 | five striped flamingos chasing seven pink stone dogs on top of a bicycle |
| 3 | hard | 5150 | 10/11 | four clocks to the left of a metal pink bear jumping over seven wooden koalas |
| 4 | hard | 1173 | 10/12 | a stone turtle in front of a green motorcycle to the right of six purple spotted umbrellas |
| 5 | hard | 10274 | 10/11 | six plastic sparkling raccoons playing with six lions behind a metal truck |
| 6 | hard | 14624 | 10/12 | a blue red giraffe playing with seven sheeps chasing a brown wooden penguin |
| 7 | hard | 6349 | 10/11 | a sparkling backpack to the right of five pink green zebras jumping over five monkeys |
| 8 | hard | 13028 | 10/11 | five spotted donuts under a red metal horse chasing six cats |
| 9 | hard | 9438 | 10/10 | four elephants jumping over four rabbits in front of seven purple stone croissants |
| 10 | hard | 728 | 10/11 | six sparkling purple bagels to the right of six plastic kangaroos behind a car |
| 11 | hard | 791 | 10/11 | a pink checkered cookie in front of four flowers under four metal pigs |
| 12 | hard | 17729 | 10/11 | a checkered toy in front of five sparkling checkered chairs on top of seven candles |
| 13 | medium | 5362 | 8/9 | a monkey in front of four pink trumpets behind six violins |
| 14 | medium | 12142 | 8/9 | seven mushrooms in front of a backpack on top of seven spotted guitars |
| 15 | medium | 1389 | 8/10 | a chair behind six zebras jumping over a pink stone koala |
| 16 | medium | 6723 | 8/10 | a dog on top of a striped zebra chasing four striped pigs |
| 17 | medium | 7221 | 8/10 | a koala playing with seven green pigs in front of a sparkling cow |
| 18 | easy | 11436 | 5/7 | a checkered brown lion chasing a kangaroo |
| 19 | easy | 4947 | 5/6 | four elephants playing with a green cat |
| 20 | easy | 10910 | 5/6 | five rabbits chasing a sparkling elephant |

Each selected record in the JSON artifact retains the original `vqa_list`, `skills`, normalized atomic constraints, score components, source line, row hash, and dataset hash.
