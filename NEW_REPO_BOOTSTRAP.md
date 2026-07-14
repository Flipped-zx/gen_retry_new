# 新仓库前置操作

以下以 `/root/private_data/agentic_image` 为父目录示例。

## 1. 创建全新目录

```bash
cd /root/private_data/agentic_image
mkdir -p gen-retry-v3
cd gen-retry-v3
```

## 2. 解压启动包到新目录

```bash
unzip /path/to/gen_retry_codex_starter_v0_3.zip -d /tmp/gen_retry_v3_bootstrap
cp -a /tmp/gen_retry_v3_bootstrap/gen_retry_codex_starter_v0_3/. .
```

如果你直接拿到的是目录，也可以：

```bash
cp -a /path/to/gen_retry_codex_starter_v0_3/. .
```

## 3. 初始化 Git

```bash
git init
git add .
git commit -m "chore: bootstrap verifier-grounded gen-retry v3"
```

若 Git 尚未配置身份：

```bash
git config user.name "Your Name"
git config user.email "you@example.com"
```

## 4. 配置外部只读源码路径

```bash
cp configs/paths/legacy_repos.example.yaml configs/paths/local.yaml
vim configs/paths/local.yaml
```

示例：

```yaml
legacy_gen_retry_root: /root/private_data/agentic_image/gen-retry-legacy
gen_searcher_root: /root/private_data/agentic_image/Gen-Searcher
gen_evolve_root: /root/private_data/agentic_image/GenEvolve
geneval2_root: /root/private_data/agentic_image/Geneval2
```

## 5. 配置模型与服务

```bash
cp configs/models/local.example.yaml configs/models/local.yaml
vim configs/models/local.yaml
```

密钥只使用环境变量，不写入 YAML。

## 6. 启动 Codex

```bash
cd /root/private_data/agentic_image/gen-retry-v3
codex --sandbox workspace-write --ask-for-approval on-request
```

进入后运行：

```text
/status
```

确认当前 workspace 是新仓库。旧仓库只能作为读取证据；任何写入旧目录的请求都应拒绝或要求人工批准。

然后粘贴 `CODEX_FIRST_PROMPT.md` 的内容。

## 7. 第一次 Codex 任务的成功标准

Codex 只写新仓库下的 `docs/architecture/` 与 `docs/SOURCE_LEDGER.md`，输出：

- 外部目录存在性与 commit/license 清单；
- 旧实现 reuse / migrate / retire 映射；
- v3 缺口分析；
- Phase 1 的精确文件计划；
- 不调用 API，不生图，不修改 Schema。
