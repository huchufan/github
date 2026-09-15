---
title: "短周期落地计划：扩展 MODULE_MANIFEST → 114，Weaviate PoC，GitHub Actions 基线，执行指南任务化"
date: 2026-09-11_22:19:04
status: draft
---

Goal

- 在最短时间内把设计指南的可交付项推进到可执行/可验证状态：
  1) 将 tools/MODULE_MANIFEST.json 扩展到 114 条并用现有生成器批量生成模块骨架；
  2) 做 Weaviate 本地 PoC（向量检索后端替换目前的内存嵌入）；
  3) 生成并验证 GitHub Actions 基线流水线模板；
  4) 把 12_设计方案落地执行指南.md 中的未完成事项逐条转为可执行任务（Trello/Jira 风格）并生成时间线与负责人建议。

Current context / assumptions

- 代码库位于 /Users/huchufan/Hermes；已有模块生成器 tools/generators/module_generator.py 与小规模 MODULE_MANIFEST.json（33 模块）。
- 已实现并测试的核心框架原型、单元测试与行为规则（85 个测试通过）。
- 实施团队可并行工作；Plan 目标优先最短时间完成 PoC/框架（不是全部生产化）。
- 你要求计划文档为可执行、可验证的细粒度任务（2–5 分钟级别），并保存为 .hermes/plans/<timestamp>-<slug>.md。

Architecture / proposed approach (2-3 sentences)

- 使用分阶段并行推进：第一阶段（自动生成）以 module_generator 批量扩展骨架到 114 模块并运行测试；第二阶段做 Weaviate 本地 PoC 替换内存索引（先在 agent/memory 加入适配层）；第三阶段在 repo 根添加 GitHub Actions 工作流模板（test/lint/build）；第四阶段把 12_设计方案落地执行指南.md 的未完成条目逐条拆成可执行任务并生成时间线与人力建议。
- 每一项都包含可复制的命令、失败/成功期望与最小可行验证步骤（TDD 风格：先写测试/检查，再实现 PoC，最后验证）。

Step-by-step tasks

Notes:
- 每一任务的命令和路径在本计划中给出；本计划只写入 .hermes/plans/... 文件（已保存）；实际实施前请审阅并批准每个阶段。

Phase A — 扩展 MODULE_MANIFEST -> 114，并批量生成

A.1 产出新的模块清单（非破坏）
- File: tools/MODULE_MANIFEST.json (existing)
- Task A.1.1 (2–5 min): 复制当前清单为工作副本
  - Command:
    cp tools/MODULE_MANIFEST.json tools/MODULE_MANIFEST.work.json
  - Expected: tools/MODULE_MANIFEST.work.json exists and differs from original only in `modules` array counts.

- Task A.1.2 (10–30 min): 构造 114 模块清单策略
  - Approach: 按框架 priority 扩充到文档目标比率（示例分配见下），保持模块名唯一并使用短命名。
  - Allocation (proposal): governance 12, orchestration 17, memory 20, automation 16, evolution 22, multiagent 27 → total 114.
  - Deliverable: replace `tools/MODULE_MANIFEST.work.json` "frameworks.*.modules" arrays with generated names (explicit list). Copy-paste-ready JSON generator snippet provided in notes below.

- Task A.1.3 (2 min): sanity check size
  - Command:
    python3 -c "import json;print(len(json.load(open('tools/MODULE_MANIFEST.work.json'))['frameworks']['governance']['modules']))"
  - Expected: printed 12 (for governance if follow allocation).

A.2 批量生成骨架（TDD：先生成测试文件名存在）
- Task A.2.1 (2 min): dry-run generator for one new module to ensure no side-effect
  - Command:
    python3 tools/generators/module_generator.py governance smoke_test
  - Expected: prints "✓ 模块生成完成: governance/smoke_test" and files under agent/governance/core/smoke_test.py and agent/governance/tests/test_smoke_test.py exist.

- Task A.2.2 (consecutive, 10–30 min): 批量生成所有 114 模块（工作副本清单）
  - Command (single-shot):
    python3 - <<'PY'
import json, subprocess, sys
m = json.load(open('tools/MODULE_MANIFEST.work.json'))
for fw,info in m['frameworks'].items():
  for mod in info['modules']:
    subprocess.run([sys.executable,'tools/generators/module_generator.py',fw,mod],check=False)
print('batch generation finished')
PY
  - Expected: generator prints success per module; agent/.. core/*.py and agent/*/tests/test_*.py created for new modules.

- Task A.2.3 (5 min): 运行测试（TDD 验证）
  - Command:
    pytest agent/ -q
  - Expected: tests pass (note: many generated tests are stubs -> pass by design or marked xfail; if failures arise, inspect failing tests and fix generator template to create minimal passing stubs).

Phase B — Weaviate 本地 PoC（向量检索后端）

Goal: 用 Weaviate 代替当前内存 SemanticIndex PoC（本地 Docker 或本机），并实现 small adapter 层 (agent/memory/core/weaviate_adapter.py)，不移除内存实现，提供切换配置。

B.1 环境准备（5–20 min）
- Task B.1.1: 本地 Weaviate 快速启动（Docker Compose）
  - Files: .hermes/poctools/weaviate/docker-compose.yml (create)
  - Command (manual instruction): docker compose -f .hermes/poctools/weaviate/docker-compose.yml up -d
  - Expected: weaviate container running (curl http://localhost:8080/v1/meta should return JSON)

- Provide exact docker-compose content in plan (YAML snippet included in appendix of plan file).

B.2 代码接口（15–60 min）
- File to add: agent/memory/core/weaviate_adapter.py
- Task B.2.1 (2–5 min): write adapter skeleton (code snippet below). Adapter must implement: add_document(id, text), search(query, top_k)->list[(id,score)].
- Verification command:
  python3 - <<'PY'
from agent.memory.core.weaviate_adapter import WeaviateAdapter
w=WeaviateAdapter('http://localhost:8080')
w.add_document('doc1','hello world')
print(w.search('hello',top_k=1))
PY
- Expected: prints list with ('doc1', similarity>0).

B.3 集成点（10–20 min）
- File: agent/memory/core/__init__.py — add optional import and factory get_vector_index(provider='local'|'weaviate')
- Task B.3.1: implement get_index_provider(config) to choose SemanticIndex (current) or WeaviateAdapter.
- Verify by running memory semantic_search path with config switch and expected hits.

Phase C — GitHub Actions 基线流水线模板（20–60 min）

C.1 Create workflow file (non-mutating plan only lists path and content)
- File: .github/workflows/ci.yml (template provided below).
- Workflow steps (exact): checkout, setup python 3.14, install deps (pip install -r requirements.txt if exists, otherwise pip install pytest), run pytest -q, run flake8/pylint optionally, upload junit report.
- Local verification: run the same commands locally: python3 -m pytest -q (expected: 85 passed).

C.2 Add smaller job for generator smoke-test (a job step to run tools/generators/module_generator.py for a single module and check created file exists) — include exit conditions and cleanup.

Phase D — 把 12_设计方案落地执行指南.md 中未完成事项逐条任务化（Trello/Jira 风格）

D.1 Parsing & task extraction (5–20 min)
- File: .hermes/plans/2026-09-11_221904-extract-tasks.md (this plan will create a task list file)
- Task D.1.1: Extract every unchecked/TO-DO item in that doc into one task with fields: id, title, description, estimate (hours), owner (suggested role), priority, acceptance criteria (commands to run/outputs expected).
- Example extracted tasks (explicit):
  - TASK-001: Generate remaining 81 modules
    - description: expand MODULE_MANIFEST.json & run generator batch (link to A.1/A.2)
    - estimate: 8h (generator run + fix templates + tests)
    - owner: infra/dev
    - acceptance: tools/MODULE_MANIFEST.json contains 114 modules; pytest agent/ passes.
  - TASK-002: Integrate Weaviate PoC
    - estimate: 3d
    - owner: infra/data
    - acceptance: weaviate_adapter.search(...) returns relevant results and pytest includes a weaviate integration test (skipped if no docker).
  - TASK-003: CI baseline
    - estimate: 1d
    - owner: ci/devops
    - acceptance: .github/workflows/ci.yml runs on PR and completes
  - TASK-004: Persist behavior rules to Obsidian doc
    - estimate: 30m
    - owner: doc
    - acceptance: governance doc updated with two rules.
  - ... (and so on for each to-do in doc; enumerate all)

D.2 Timeline & resource suggestion (10–30 min)
- Produce a 6–8 week phased timeline with parallel tracks:
  Week 0–1: Expand manifest → generate all modules → run tests → fix generator templates (team: 2 devs)
  Week 2: Weaviate PoC + adapter + integration tests (team: 1 data infra)
  Week 2–3: CI/CD baseline + code quality tooling (team: 1 DevOps)
  Week 3–6: Implement core module features prioritized by KPI (team: 3–6 engineers)
- Provide owner role mapping (Lead, Dev, Infra, QA, Doc)

Tests / validation (TDD cycle required per code task)

- For every code task that changes behavior:
  1) Write a failing test under agent/<framework>/tests/test_<module>.py that asserts the expected behavior.
 2) Run pytest to see the failing test (command + expected failure message must be recorded).
 3) Implement minimal code change that makes the test pass.
  4) Run pytest and confirm pass.
  5) Commit changes with descriptive message.

- Examples (copy-paste):
  - Add integration test for weaviate adapter: agent/memory/tests/test_weaviate_integration.py (contains a test that is skipped if WEAVIATE_URL not set; run locally when docker up).
  - For generator, tests assert generated files exist and contain class names (test_generator_smoke).

Risks, tradeoffs, open questions

- Risk: Generating 81 more modules creates maintenance burden. Tradeoff: Use generator templates to keep modules minimal and DRY; prioritize implementing a subset of high-value modules first.
- Risk: Weaviate introduces network/infra complexity (Docker required). Tradeoff: PoC only; keep existing memory fallback to avoid blocking.
- Open question: Who is the commit/PR owner for generated code? Decide PR policy (one bulk PR vs many per framework).
- Tradeoff: TDD for generated stubs produces many trivially passing tests; ensure tests exercise minimal integration (import, interface conformance) rather than empty pass.

Appendix A — JSON generator snippet to expand modules (copy-paste)

Use this Python snippet locally to expand modules in tools/MODULE_MANIFEST.work.json. It generates placeholder module names per allocation.

```python
import json
m = json.load(open('tools/MODULE_MANIFEST.work.json'))
alloc = {'governance':12,'orchestration':17,'memory':20,'automation':16,'evolution':22,'multiagent':27}
for fw,n in alloc.items():
  base = m['frameworks'][fw]['modules']
  curr = list(base)
  i = 0
  while len(curr) < n:
    candidate = f"mod_{i}"
    if candidate not in curr:
      curr.append(candidate)
    i+=1
  m['frameworks'][fw]['modules'] = curr
  m['frameworks'][fw]['total'] = n
m['total_modules']=sum(alloc.values())
open('tools/MODULE_MANIFEST.work.json','w').write(json.dumps(m,indent=2,ensure_ascii=False))
print('manifest expanded')
```

Appendix B — Docker Compose for Weaviate (copy-paste)

``yaml
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:1.18.1
    ports:
      - '8080:8080'
    environment:
      - QUERY_DEFAULTS_LIMIT=20
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
    volumes:
      - ./data/weaviate:/var/lib/weaviate
```

Saved plan path

- .hermes/plans/2026-09-11_221904-expand-manifest-weaviate-ci-plan.md

Next step (if approved)

- I will stop (plan-only). If you approve, I will execute Phase A (expand manifest & dry-run generator) or any single phase you pick. 

