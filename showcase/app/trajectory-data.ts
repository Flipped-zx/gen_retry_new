export type Attempt = {
  id: string;
  action: "generate" | "edit";
  parent: string | null;
  image: string;
  passed: number;
  score: number;
  note: string;
  fixed?: string;
  regressed?: string;
};

export type PromptDelta = {
  kind: "target" | "preserve" | "forbid" | "branch";
  text: string;
};

export type TrajectoryDimension =
  | "count"
  | "attribute"
  | "spatial"
  | "action"
  | "recovery";

export type Trajectory = {
  id: string;
  index: string;
  category: string;
  dimensions: TrajectoryDimension[];
  title: string;
  summary: string;
  originalPrompt: string;
  totalAtoms: number;
  initialInstruction: string;
  retryInstruction: string;
  promptDelta: PromptDelta[];
  attempts: Attempt[];
};

export const trajectories: Trajectory[] = [
  {
    id: "ep-056",
    index: "01",
    category: "COUNT + LAYOUT",
    dimensions: ["count", "spatial"],
    title: "把多余实例逐个清掉",
    summary:
      "三个对象组的身份、颜色和左右顺序都已经正确。Retry 没有重画整张图，而是把目标逐轮收窄到仍然超数的组，最后只清理多纳圈残影。",
    originalPrompt:
      "four checkered donuts to the right of seven yellow birds to the right of six croissants",
    totalAtoms: 10,
    initialInstruction:
      "Create a clean, front-facing image with three separated groups arranged left to right across the frame. On the left, show exactly six croissants total in a neat two-row grid, each fully visible and separated. In the center, to the right of the croissants, show exactly seven yellow birds total in a loose row or arc, each fully visible, separated, and clearly yellow. On the right, to the right of the birds, show exactly four checkered donuts total in a neat 2-by-2 grid, each fully visible, separated, ring-shaped, and covered with a clear checkerboard pattern. Keep the spatial order unambiguous: croissants on the left, yellow birds in the middle, checkered donuts on the right. Do not include extra, cropped, fused, hidden, reflected, background, or decorative copies of croissants, birds, or donuts.",
    retryInstruction:
      "Target operation: Edit attempt a_003 only in the donut area on the right: remove the entire lowest solid row of two checkered donuts and also erase the two faint ghost donut remnants below them, so the final image contains exactly four checkered ring donuts total.\n\nSpatial grounding: Keep only the upper two rows of donuts as a clean 2-by-2 grid to the right of the yellow birds; replace all removed lower donut shapes with plain white background matching the surrounding surface.\n\nPreservation lock: Preserve the six croissants on the left, the seven yellow birds in the center, the yellow bird color, the left-to-right order croissants then birds then donuts, the white background, top-down product style, and the orange-and-white checkered ring appearance of the four remaining donuts.\n\nForbidden changes: Do not add, duplicate, crop, blur, or move any croissants or birds; do not create new donuts; do not leave any lower donut fragments, faint circular shadows, ghost rings, reflections, or checkered marks; do not alter colors, object identities, or the composition outside the removed lower donut area.",
    promptDelta: [
      { kind: "target", text: "只编辑右侧 donut 区域" },
      { kind: "target", text: "留下 2 × 2，共 4 个" },
      { kind: "preserve", text: "锁定 6 个 croissants 与 7 只黄鸟" },
      { kind: "preserve", text: "锁定 left → right 空间顺序" },
      { kind: "forbid", text: "清除 ghost rings 与圆形残影" },
    ],
    attempts: [
      {
        id: "a_000",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-056/attempt-0.png",
        passed: 7,
        score: 0.0020921373,
        note: "三组身份与顺序正确，但三项计数失败。",
      },
      {
        id: "a_001",
        action: "edit",
        parent: "a_000",
        image: "/trajectories/ep-056/attempt-1.png",
        passed: 8,
        score: 0.0167784742,
        note: "croissant 数量修复；鸟与 donut 仍超数。",
        fixed: "croissant count",
      },
      {
        id: "a_002",
        action: "edit",
        parent: "a_001",
        image: "/trajectories/ep-056/attempt-2.png",
        passed: 9,
        score: 0.0742504617,
        note: "黄鸟数量修复；只剩 donut count。",
        fixed: "bird count",
      },
      {
        id: "a_003",
        action: "edit",
        parent: "a_002",
        image: "/trajectories/ep-056/attempt-3.png",
        passed: 9,
        score: 0.1423216825,
        note: "通过数持平，但 verifier 置信度改善。",
      },
      {
        id: "a_004",
        action: "edit",
        parent: "a_003",
        image: "/trajectories/ep-056/attempt-4.png",
        passed: 10,
        score: 0.9999896308,
        note: "清除底部实体与残影，全部通过。",
        fixed: "donut count",
      },
    ],
  },
  {
    id: "ep-012",
    index: "02",
    category: "ATTRIBUTE BINDING",
    dimensions: ["count", "attribute"],
    title: "从数量修复到材质强化",
    summary:
      "第一轮先补齐第七把吉他；第二轮只强化金属材质线索，同时锁住格纹、数量和四个背包。两次编辑各修复一个原子，没有回退。",
    originalPrompt: "seven metal checkered guitars and four backpacks",
    totalAtoms: 6,
    initialInstruction:
      "Create a clean studio scene showing exactly seven metal checkered guitars total and exactly four backpacks total. Arrange the seven guitars in a single separated row across the back, each fully visible with a recognizable guitar body, neck, headstock, strings, and tuning pegs; each guitar must be made of shiny reflective metal and must have a clear checkered pattern on the metal body and neck. Arrange the four backpacks in a separate row across the front, each fully visible with shoulder straps, zipper pockets, and soft fabric texture. Keep every guitar and every backpack separated with visible gaps, not touching or overlapping. Do not include extra guitars, extra backpacks, cropped objects, fused objects, reflections that look like additional countable objects, guitar cases, ukuleles, violins, or other instruments.",
    retryInstruction:
      "Target operation: Edit attempt a_001 only to make the seven guitars unmistakably metal. Strengthen each guitar with polished chrome or brushed stainless-steel material cues: bright specular highlights, mirror-like silver reflections, metallic rims, and reflective metal surfaces across the bodies, neck hardware, tuning pegs, bridges, and headstocks while keeping the black-and-silver checkered pattern visible on every guitar.\n\nSpatial grounding: Apply the metallic finish only to the seven guitars in the back row across the upper half of the image, from left to right. Keep all seven full guitar bodies, seven necks, and seven headstocks in the same positions behind the backpacks, with small gaps between adjacent guitars so the count remains clear.\n\nPreservation lock: Preserve exactly seven guitars total, their checkered pattern, recognizable acoustic guitar shapes, and full visibility. Preserve exactly four backpacks in the front row with their current colors, straps, zipper pockets, positions, and full visibility. Preserve the clean gray studio background, lighting direction, camera angle, and overall product-display layout.\n\nForbidden changes: Do not add, remove, crop, fuse, or hide any guitar or backpack. Do not create reflections that look like extra guitars. Do not change the guitars into wood, plastic, glass, cases, violins, ukuleles, or any other objects. Do not alter the backpack materials, counts, positions, or colors.",
    promptDelta: [
      { kind: "target", text: "只强化 metal 材质线索" },
      { kind: "target", text: "polished chrome + specular highlights" },
      { kind: "preserve", text: "锁定 7 把吉他与格纹" },
      { kind: "preserve", text: "锁定前排 4 个背包" },
      { kind: "forbid", text: "反射不能形成额外吉他" },
    ],
    attempts: [
      {
        id: "a_000",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-012/attempt-0.png",
        passed: 4,
        score: 0.0285552763,
        note: "格纹与背包正确；吉他只有 6 把，金属属性失败。",
      },
      {
        id: "a_001",
        action: "edit",
        parent: "a_000",
        image: "/trajectories/ep-012/attempt-1.png",
        passed: 5,
        score: 0.7787711486,
        note: "补齐第 7 把吉他；金属材质仍不确定。",
        fixed: "guitar count",
      },
      {
        id: "a_002",
        action: "edit",
        parent: "a_001",
        image: "/trajectories/ep-012/attempt-2.png",
        passed: 6,
        score: 0.9084421022,
        note: "强化 chrome 材质，6/6 全部通过。",
        fixed: "metal attribute",
      },
    ],
  },
  {
    id: "ep-079",
    index: "03",
    category: "ACTION + SPATIAL",
    dimensions: ["count", "spatial", "action"],
    title: "把对象移进正确的关系里",
    summary:
      "图里已经有黑狗、绿猫和卡车，但“追逐”与“在卡车下”没有同时成立。Retry 先修动作和数量，最后只移动猫群的深度与位置。",
    originalPrompt: "a black dog chasing seven green cats under four trucks",
    totalAtoms: 10,
    initialInstruction:
      "Create a clear static scene with exactly one black dog total chasing exactly seven green cats total under exactly four trucks total. Arrange the four trucks in a horizontal row across the scene, raised high enough that the space beneath each truck is visible. Place all seven green cats fully visible and separated in the spaces under the trucks, running from left to right in a loose row with gaps between them. Place the single black dog behind the cats on the left side, also fully visible, facing and running toward the cats with pursuit posture and aligned motion direction so the dog is visibly chasing them. Keep every cat green, keep the dog black, and keep all four trucks recognizable as trucks. Do not include extra dogs, cats, trucks, cropped bodies, fused animals, reflections, background duplicates, or hidden countable instances.",
    retryInstruction:
      "Target operation: Edit attempt a_002 by relocating the seven green cats so they are clearly under the four trucks, not in the open foreground. Keep exactly seven green cats total, each fully visible and separated, while keeping the single black dog chasing them from the left.\n\nSpatial grounding: Place the cat row inside the dark undercarriage space directly below the truck bodies and between the visible wheels, with truck bumpers, axles, wheel wells, and chassis visibly above the cats. Make the cats slightly smaller and farther back than the dog, with their paws on the road shadow beneath the trucks rather than on the bright foreground road. Keep the black dog just left of and slightly in front of the cat row, facing right in a running chase pose without overlapping or hiding any cat.\n\nPreservation lock: Preserve exactly one black dog, the dog’s black color and dog identity, the dog chasing the cats, exactly seven green cats, the cats’ green color and cat identity, exactly four trucks, truck recognizability, the road setting, front-facing truck arrangement, and the overall camera view.\n\nForbidden changes: Do not add or remove dogs, cats, or trucks. Do not create hidden, cropped, fused, reflected, or duplicate cats. Do not leave cats standing across the open foreground in front of the trucks. Do not recolor the animals, block the dog, remove the chase relation, alter the truck count, or redraw unrelated scene elements.",
    promptDelta: [
      { kind: "target", text: "只移动 7 只绿猫" },
      { kind: "target", text: "进入 truck undercarriage 阴影" },
      { kind: "target", text: "更小、更远，车体位于猫群上方" },
      { kind: "preserve", text: "锁定黑狗追逐姿态与 4 辆卡车" },
      { kind: "forbid", text: "猫不能停留在明亮前景" },
    ],
    attempts: [
      {
        id: "a_000",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-079/attempt-0.png",
        passed: 7,
        score: 0.131289531,
        note: "对象与颜色正确；追逐、猫数量和上下关系失败。",
      },
      {
        id: "a_001",
        action: "edit",
        parent: "a_000",
        image: "/trajectories/ep-079/attempt-1.png",
        passed: 8,
        score: 0.1779214209,
        note: "追逐关系修复；猫数量与卡车下方关系仍失败。",
        fixed: "chasing relation",
      },
      {
        id: "a_002",
        action: "edit",
        parent: "a_001",
        image: "/trajectories/ep-079/attempt-2.png",
        passed: 9,
        score: 0.872348677,
        note: "补齐 7 只猫；只剩空间关系。",
        fixed: "cat count",
      },
      {
        id: "a_003",
        action: "edit",
        parent: "a_002",
        image: "/trajectories/ep-079/attempt-3.png",
        passed: 10,
        score: 0.9573604259,
        note: "猫群进入底盘下方，10/10 全部通过。",
        fixed: "under-truck relation",
      },
    ],
  },
  {
    id: "ep-005",
    index: "04",
    category: "NON-MONOTONIC RECOVERY",
    dimensions: ["count", "spatial", "action", "recovery"],
    title: "一次失败编辑后，回到历史分支",
    summary:
      "a_001 把 6/9 降到 4/9。Agent 没有沿着坏结果继续编辑，而是回到 a_000 重新分支，先升到 8/9，再做一次局部清理达到 9/9。",
    originalPrompt: "a lion playing with five dogs under a yellow cow",
    totalAtoms: 9,
    initialInstruction:
      "Create a clear scene with exactly one lion total, exactly five dogs total, and exactly one cow total. The cow must be yellow and fully visible, standing or floating above the dogs in the upper center of the image. Place all five dogs directly under the yellow cow in a separated row or shallow arc, fully visible with gaps between them, so the relation dogs under the cow is obvious. Place the single lion beside and slightly in front of the five dogs, facing them and playing with them around one shared ball or toy, with the lion and dogs oriented toward the toy and each other to make the playing interaction visible. Keep every animal recognizable and uncropped. Do not include extra lions, extra dogs, extra cows, partial animals, fused animals, reflections, background duplicates, or any non-yellow cow.",
    retryInstruction:
      "Target operation: Edit attempt a_002 only in the dog group so there are exactly five dogs total. Keep five fully visible, clearly separated dogs under the cow: the left black-and-tan dog, the brown dog beside it, the center tan dog, the rear black-and-tan dog, and the small dog playing beside the lion. Remove or clean up any extra, ghosted, duplicated, fused, reflected, or ambiguous dog-like body parts that could be counted as a sixth dog, especially around the small dog and the lion.\n\nSpatial grounding: Keep all five dogs in the lower center area directly underneath the large yellow cow. Keep the small dog next to the lion and the colorful ball, facing the lion as part of the play interaction. Maintain clear gaps between each dog so the count reads unambiguously as five separate dogs.\n\nPreservation lock: Preserve the single maned lion at the lower right, the lion playing with the dogs and ball, the presence of dogs, the dogs-under-cow relationship, the single large yellow cow with horns and udder, the outdoor background, lighting, and the overall composition.\n\nForbidden changes: Do not add any dogs, do not leave more than five dogs, do not remove the lion, do not add a second lion, do not alter the cow count or yellow color, do not move dogs out from under the cow, do not crop, hide, fuse, or reflect any animals, and do not introduce unrelated new objects.",
    promptDelta: [
      { kind: "branch", text: "a_001 回退后，从 a_000 重新分支" },
      { kind: "target", text: "最终只清理 dog group" },
      { kind: "target", text: "明确枚举 5 只可数实例" },
      { kind: "preserve", text: "锁定 lion playing、dogs under cow" },
      { kind: "forbid", text: "清除 ghost / fused dog parts" },
    ],
    attempts: [
      {
        id: "a_000",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-005/attempt-0.png",
        passed: 6,
        score: 0.2888286778,
        note: "主要关系可见，但狮子、动作和狗数量失败。",
      },
      {
        id: "a_001",
        action: "edit",
        parent: "a_000",
        image: "/trajectories/ep-005/attempt-1.png",
        passed: 4,
        score: 0.0012852074,
        note: "编辑引入第二个牛状主体，多项回退。",
        regressed: "−2 atoms",
      },
      {
        id: "a_002",
        action: "edit",
        parent: "a_000",
        image: "/trajectories/ep-005/attempt-2.png",
        passed: 8,
        score: 0.8475803746,
        note: "从 a_000 重开分支；只剩狗数量。",
        fixed: "+2 vs initial",
      },
      {
        id: "a_003",
        action: "edit",
        parent: "a_002",
        image: "/trajectories/ep-005/attempt-3.png",
        passed: 9,
        score: 0.9078228545,
        note: "清理额外狗形残影，9/9 全部通过。",
        fixed: "dog count",
      },
    ],
  },
  {
    id: "ep-108",
    index: "05",
    category: "COUNT + ATTRIBUTE",
    dimensions: ["count", "attribute", "recovery"],
    title: "编辑无效后，切换为重新生成",
    summary:
      "局部编辑同时改数量与双色属性没有提升。Agent 保留失败证据，切换到结构更明确的 2 × 2 分组生成，一次从 3/6 提升到 6/6。",
    originalPrompt: "four yellow pink dogs and four rabbits",
    totalAtoms: 6,
    initialInstruction:
      "Create a clear scene with exactly four dogs total and exactly four rabbits total. Show the four dogs as clearly recognizable dogs with dog faces, ears, tails, and paws; make every dog visibly both yellow and pink, such as yellow-and-pink fur patches or yellow bodies with pink markings, with no dog lacking either color. Arrange the four dogs in a separated row on the left, each fully visible with gaps between them. Show the four rabbits as clearly recognizable rabbits with long ears, small noses, and hind legs, arranged in a separated row on the right, each fully visible with gaps between them. Do not include extra dogs, extra rabbits, cropped animals, fused animals, reflections, background animal copies, or animal-like decorations that could be counted.",
    retryInstruction:
      "Create a clean studio image on a plain white background with exactly four dogs total and exactly four rabbits total. Place the four dogs on the left side in a neat two-by-two grid, fully visible, separated by clear gaps, and recognizable as dogs with dog faces, ears, tails, legs, and paws. Every dog must have both yellow and pink fur clearly visible: use bright yellow fur with large pink patches on each dog, with no dog that is only pink or only yellow. Place the four rabbits on the right side in a neat two-by-two grid, fully visible, separated by clear gaps, and recognizable as rabbits with long upright ears, rabbit noses, paws, and natural brown-gray fur. Keep the dogs and rabbits in separate groups with no overlap. Do not include more than four dogs or more than four rabbits, and do not include cropped animals, fused animals, reflections, background animal copies, animal-shaped decorations, or any extra countable animals.",
    promptDelta: [
      { kind: "branch", text: "编辑无提升后切换为 regenerate" },
      { kind: "target", text: "dogs 与 rabbits 各用 2 × 2 网格" },
      { kind: "target", text: "每只 dog 同时显式包含 yellow + pink" },
      { kind: "preserve", text: "左右分组并保留清晰间隔" },
      { kind: "forbid", text: "排除反射与背景动物副本" },
    ],
    attempts: [
      {
        id: "a_000",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-108/attempt-0.png",
        passed: 3,
        score: 0.0007429025,
        note: "对象身份可见，但 dogs / rabbits 数量及双色绑定失败。",
      },
      {
        id: "a_001",
        action: "edit",
        parent: "a_000",
        image: "/trajectories/ep-108/attempt-1.png",
        passed: 3,
        score: 0.0003509779,
        note: "同时增狗、删兔、补颜色，3/6 没有提升。",
        regressed: "score down",
      },
      {
        id: "a_002",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-108/attempt-2.png",
        passed: 6,
        score: 0.9897163165,
        note: "改用严格双网格布局，数量和双色属性全部通过。",
        fixed: "+3 atoms",
      },
    ],
  },
  {
    id: "ep-157",
    index: "06",
    category: "HISTORY + STRATEGY",
    dimensions: ["count", "attribute", "recovery"],
    title: "两次编辑都无效，停止沿用坏策略",
    summary:
      "两次 edit 都从 a_000 分支，却始终停在 5/7。最终把十四个对象重构成七列配对布局，完整保留 spotted 与 pink stone 属性并达到 7/7。",
    originalPrompt: "seven spotted violins and seven pink stone cats",
    totalAtoms: 7,
    initialInstruction:
      "Create a clear static image with exactly seven spotted violins total and exactly seven pink stone cats total. Place the seven spotted violins in a neat row across the upper half of the image, each fully visible and separated, with recognizable violin bodies, necks, strings, bridges, and f-holes; every violin must have visible dark spots on its surface. Place the seven pink stone cats in a neat row across the lower half of the image, each fully visible and separated, with recognizable cat ears, faces, bodies, legs, and tails; every cat must be pink and look like carved stone with matte rocky texture, chiseled edges, and subtle stone cracks. Keep violins and cats visually distinct, with no overlap, no cropped instances, no fused instances, no reflections, no background duplicates, and no extra violins, cats, instruments, or animal figures.",
    retryInstruction:
      "Create a clean studio image containing exactly seven spotted violins and exactly seven pink stone cats. Arrange the scene as seven clearly separated vertical columns across the frame: in each column, place one full spotted violin in the upper row and one full pink stone cat directly below it in the lower row, for seven violins total and seven cats total. Make every violin recognizable with a body, neck, strings, bridge, f-holes, pegs, and visible dark spots on the violin wood. Make every cat recognizable as a seated cat, pink in color, carved from stone with matte rocky texture, chiseled edges, subtle cracks, ears, face, body, legs, paws, and tail. Keep all fourteen objects fully visible inside the frame, similar in size within each row, evenly spaced with clear gaps, not touching or overlapping. Use a simple dark neutral background. Do not include fewer or more than seven violins, fewer or more than seven cats, cropped objects, fused objects, hidden objects, mirrored reflections, duplicate-like shadows, extra instruments, extra animals, text, labels, or unrelated objects.",
    promptDelta: [
      { kind: "branch", text: "两次 edit 无提升后改为 regenerate" },
      { kind: "target", text: "十四个对象重构成 7 个垂直列" },
      { kind: "target", text: "每列一把 violin + 一只 cat" },
      { kind: "preserve", text: "锁定 spotted 与 pink stone 属性" },
      { kind: "forbid", text: "禁止裁切、重叠与副本阴影" },
    ],
    attempts: [
      {
        id: "a_000",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-157/attempt-0.png",
        passed: 5,
        score: 0.0024475192,
        note: "身份与属性正确，但 violins 和 cats 都只有 6 个。",
      },
      {
        id: "a_001",
        action: "edit",
        parent: "a_000",
        image: "/trajectories/ep-157/attempt-1.png",
        passed: 5,
        score: 0.0015390593,
        note: "尝试各补一个实例，通过数仍停在 5/7。",
        regressed: "score down",
      },
      {
        id: "a_002",
        action: "edit",
        parent: "a_000",
        image: "/trajectories/ep-157/attempt-2.png",
        passed: 5,
        score: 0.0018864687,
        note: "从原图重排七列，仍未修复两项数量。",
      },
      {
        id: "a_003",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-157/attempt-3.png",
        passed: 7,
        score: 0.9996790767,
        note: "用七列配对结构重新生成，7/7 全部通过。",
        fixed: "+2 atoms",
      },
    ],
  },
  {
    id: "ep-158",
    index: "07",
    category: "SPATIAL + COUNT",
    dimensions: ["count", "spatial", "recovery"],
    title: "先重建空间布局，再只补一个实例",
    summary:
      "首轮只有 5/8。重新生成先把自行车、鸟和两组空间关系修到 7/8，最后 edit 只在前景补一只猪并锁住其余布局。",
    originalPrompt: "six pigs in front of five bicycles to the left of four birds",
    totalAtoms: 8,
    initialInstruction:
      "Create a clear scene with exactly six pigs total, exactly five bicycles total, and exactly four birds total. Place the six pigs fully visible in the foreground in two rows of three, with gaps between every pig; make each pig recognizable with a pig body, snout, ears, and legs. Place the five bicycles fully visible behind the pigs in the middle ground on the viewer-left side, arranged in a neat row with visible wheels and frames; the pigs must be in front of the bicycles with depth separation and no bicycle hiding a pig. Place the four birds fully visible on the viewer-right side, to the right of all five bicycles, separated from each other and recognizable with beaks, wings, and bird bodies. Keep all objects uncropped and distinct. Do not include extra pigs, bicycles, or birds, and do not include fused, reflected, partial, background, or decorative duplicate instances.",
    retryInstruction:
      "Target operation: Edit attempt a_001 by adding exactly one additional fully visible pig so the scene contains exactly six pigs total. Make the new pig match the existing pigs in realism and scale, with a clear snout, ears, body, and four legs, and keep it distinct rather than fused with any existing pig.\n\nSpatial grounding: Place the added pig in the foreground pig group, in the small open foreground space between or beside the existing pigs, still clearly in front of the row of bicycles. Keep the five bicycles in the middle ground behind the pigs and keep the four birds on the right-side rail to the right of the bicycles.\n\nPreservation lock: Preserve the existing five visible pigs, the exact five bicycles, the exact four birds, the pigs-in-front-of-bicycles depth relation, the bicycles-left-of-birds relation, the fence rail, field background, lighting, camera angle, and overall composition.\n\nForbidden changes: Do not remove, crop, duplicate, merge, or hide any existing pig, bicycle, or bird. Do not add extra pigs beyond the single new pig, do not add extra bicycles or birds, do not redraw unrelated objects, and do not change the positions or counts of the bicycles or birds.",
    promptDelta: [
      { kind: "branch", text: "先 regenerate 解决整体布局" },
      { kind: "target", text: "最终 edit 只新增 1 只 pig" },
      { kind: "preserve", text: "锁定 5 辆 bicycles 与 4 只 birds" },
      { kind: "preserve", text: "锁定 pigs in front / bicycles left" },
      { kind: "forbid", text: "禁止改动其余对象数量和位置" },
    ],
    attempts: [
      {
        id: "a_000",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-158/attempt-0.png",
        passed: 5,
        score: 0.0017459555,
        note: "主要对象可见，但数量与空间组织多项失败。",
      },
      {
        id: "a_001",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-158/attempt-1.png",
        passed: 7,
        score: 0.1431269345,
        note: "重建前中后景后，只剩 pig count 未通过。",
        fixed: "+2 atoms",
      },
      {
        id: "a_002",
        action: "edit",
        parent: "a_001",
        image: "/trajectories/ep-158/attempt-2.png",
        passed: 8,
        score: 0.968647416,
        note: "只在前景补一只猪，其余关系保持，8/8 全通过。",
        fixed: "pig count",
      },
    ],
  },
  {
    id: "ep-176",
    index: "08",
    category: "LAYOUT RECOVERY",
    dimensions: ["count", "attribute", "spatial", "recovery"],
    title: "无效编辑后，用历史结果决定重生成",
    summary:
      "初始图已通过 8/10，只缺 suitcases 与 croissants 数量。一次 edit 没有改变通过数，Agent 随后重新生成完整分层布局并达到 10/10。",
    originalPrompt: "six yellow suitcases behind four spotted penguins under six croissants",
    totalAtoms: 10,
    initialInstruction:
      "Create a clear scene with exactly six yellow suitcases total in the background, arranged in a separated row behind the penguins; each suitcase must be fully visible, distinctly yellow, and not fused or cropped. Place exactly four spotted penguins total in the foreground/middle ground in front of the suitcases, fully visible and separated, with obvious dark spots on their bodies. Place exactly six croissants total above the penguins near the top of the image, arranged in a separated row or arc so the four spotted penguins are visibly under the croissants. Keep the depth relation clear: yellow suitcases behind the penguins, penguins below the croissants. Do not include any extra suitcases, penguins, or croissants, and avoid cropped, reflected, hidden, fused, or background duplicate instances.",
    retryInstruction:
      "Create a clear front-facing scene with exactly six yellow suitcases, exactly four spotted penguins, and exactly six croissants. Arrange the six yellow suitcases in a back row spanning left to right behind the penguins; make every suitcase fully visible enough to count, separated from the others, bright yellow, upright, and not cropped at the image edges. Place exactly four spotted penguins in the foreground in front of the suitcase row, fully visible from head to feet, separated, and with obvious black spots on their white bellies. Place exactly six croissants above the penguins near the top of the image in a separate left-to-right row or shallow arc, so the penguins are clearly under the croissants. Keep the depth clear: suitcases behind penguins, croissants above penguins. Do not include extra suitcases, extra penguins, extra croissants, fused duplicates, reflections, hidden instances, partial edge objects, or ambiguous pastries.",
    promptDelta: [
      { kind: "branch", text: "无效 edit 后切换为 regenerate" },
      { kind: "target", text: "6 suitcases / 4 penguins / 6 croissants" },
      { kind: "target", text: "三层对象全部可数且不裁切" },
      { kind: "preserve", text: "保留 yellow、spotted 与深度关系" },
      { kind: "forbid", text: "禁止隐藏实例与边缘残缺" },
    ],
    attempts: [
      {
        id: "a_000",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-176/attempt-0.png",
        passed: 8,
        score: 0.0165635586,
        note: "企鹅、属性与关系通过；两个对象组都只有 4 个。",
      },
      {
        id: "a_001",
        action: "edit",
        parent: "a_000",
        image: "/trajectories/ep-176/attempt-1.png",
        passed: 8,
        score: 0.0105767476,
        note: "尝试各补两个实例，但两项数量仍未通过。",
        regressed: "score down",
      },
      {
        id: "a_002",
        action: "generate",
        parent: null,
        image: "/trajectories/ep-176/attempt-2.png",
        passed: 10,
        score: 0.9583012906,
        note: "重生成完整三层布局，10/10 全部通过。",
        fixed: "+2 atoms",
      },
    ],
  },
];
