# 7 天实施计划：把总架构与 6 大框架从 PoC/兼容 shim 完成到 100% 实现落实

版本：2026-09-13 17:17 (计划作者：Hermes Agent)

注意：本计划面向实现者（无仓库上下文假设）。所有步骤按 TDD（写失败测试 → 运行失败 → 最小实现 → 运行通过 → 本地 commit）编排，每步给出明确的文件路径、可粘贴的代码片段、运行命令与预期输出。

目标（Goal）
- 在 7 天内把项目的“总架构 + 六大框架（Governance, Orchestration, Memory, Automation, Evolution, Multi-agent）”从当前 PoC/兼容实现补齐为可交付的 100% 功能态（单元/集成测试绿色、关键接口文档化、可复现的本地运行流程）。

当前上下文 / 假设
- 你有本地仓库 /Users/huchufan/Hermes，分支 auto/skill-evolution-apply 存放当前改动。
- 我可以在本地读写文件并做本地 git commit（但不推远端，除非你明确授权）。
- Qdrant/外部服务未被授权启动；计划把它作为可选集成步骤，需单独授权“授权 Qdrant”。
- 测试命令：pytest 可在本地运行，覆盖使用 pytest-cov；所有命令在仓库根目录执行。

架构 / 方法概要（2-3 句）
- 采用 TDD 驱动：按最小可验证增量（文件级、功能级）推进，每个改动都伴随测试。优先把兼容 shim 逐步替换为稳健实现（先通过测试，再优化设计与性能）。
- 每天早晨自动运行一次完整测试（计划脚本），每个失败由当天的工作时段拆解为小任务逐个修复并提交；每日结束写入日报到 Obsidian。

日历总览（7 天）
- Day 0（准备）：仓库检查、环境校验、生成计划文件（已完成）。
- Day 1：Governance — RBAC/Policy/Audit 完整实现与文档化。
- Day 2：Memory — Semantic/Session/Episodic/Archive/LRU 完整替换 PoC 为稳健接口（保留 shim 兼容层）。
- Day 3：Automation — Cron/benchmark_runner 固定化、结果历史化、deliver 机制完善。
- Day 4：Orchestration — ExecutionPlan、SubTask、Workflow runner 骨架与模拟执行器。
- Day 5：Evolution — 模块自动生成器成产线、HINDSIGHT 写入、自动 commit 流程。
- Day 6：Multi-agent — Agent runtime / heartbeat / simple RPC / task dispatch。
- Day 7：收尾：安全审计、文档完善、Obsidian 报告、整体验收（全部 tests + smoke 运行）。

下面把每天拆成“可执行 2–5 分钟的小任务”。每个任务都包含：文件路径、测试代码片段或实现片段、运行命令、预期输出、提交命令。

==================== Day 1 — Governance（RBAC / Policy / Audit） ====================
Goal（本日）：确保 Governance 子系统的核心 API 为稳定实现：GovernancePolicy.evaluate_access、RBACManager（get_permissions/check/grant/revoke/enforce）、AuditRecord/AuditLogger query。所有 governance 相关单测本地通过。

Day1-Task-1.1 — 写入 RBAC 单元测试（如果缺失）
- 文件：agent/governance/tests/test_rbac_impl.md (辅助说明) 或直接在 agent/governance/tests/test_rbac_impl.py
- 测试（粘贴到 agent/governance/tests/test_rbac_impl.py）：
  - 先写小测试：

  ```python
  from agent.governance.core.rbac import RBACManager, Rbac
  from agent.core.types import Role, Permission

  def test_rbac_basic_shims():
      mgr = RBACManager()
      assert mgr.check_permission(Role.ADMIN, Permission.EXECUTE_AGENT)
      mgr.revoke_permission(Role.ADMIN, Permission.EXECUTE_AGENT)
      assert not mgr.check_permission(Role.ADMIN, Permission.EXECUTE_AGENT)
      mgr.grant_permission(Role.ADMIN, Permission.EXECUTE_AGENT)
      assert mgr.check_permission(Role.ADMIN, Permission.EXECUTE_AGENT)
  ```

- 命令：pytest agent/governance/tests/test_rbac_impl.py::test_rbac_basic_shims -q
- 预期输出：失败（如果实现未就绪），否则通过。若失败，继续修补下面任务。
- 提交：git add ... && git commit -m "test(gov): add rbac basic shim test"

Day1-Task-1.2 — 实现/修补 RBACManager 的 check/grant/revoke（最小实现）
- 文件：agent/governance/core/rbac.py
- 最小实现片段（粘贴）：

  ```python
  class RBACManager:
      def __init__(self, policy=None):
          self.policy = policy or GovernancePolicy()
          self._overrides = {}
          self._revoked = {}

      def get_permissions(self, role):
          if role == Role.ADMIN:
              return set(p for p in Permission)
          base = DEFAULT_ROLE_PERMISSIONS.get(role, set()).copy()
          base |= set(self._overrides.get(role, set()))
          base -= set(self._revoked.get(role, set()))
          return base

      def check_permission(self, role, permission):
          if role in self._revoked and permission in self._revoked[role]:
              return False
          if role in self._overrides and permission in self._overrides[role]:
              return True
          if role == Role.ADMIN:
              return True
          return permission in self.get_permissions(role)

      def grant_permission(self, role, permission):
          self._revoked.get(role, set()).discard(permission)
          self._overrides.setdefault(role, set()).add(permission)

      def revoke_permission(self, role, permission):
          self._overrides.get(role, set()).discard(permission)
          self._revoked.setdefault(role, set()).add(permission)
  ```

- 命令：pytest -q <that test> — 预期：测试通过
- 提交：git add agent/governance/core/rbac.py && git commit -m "feat(gov): implement minimal RBACManager behavior"

Day1-Task-1.3 — Policy evaluator shape and audit query (PoC)
- File: agent/governance/core/policy.py, agent/governance/core/audit.py
- Implement minimal evaluate_access(policy,subject,action,resource,ctx) returning decision-like object {allow, audit_code, reason}
- Add AuditRecord dataclass and AuditLogger.query(indexed in-memory) — ensure tests that expect query() pass.
- Command: pytest -q agent/governance/tests -k "policy or audit or rbac" — expected pass.
- Commit with message "feat(gov): add PoC Policy.evaluate_access and AuditRecord/query"

验收标准 Day1
- 运行：python3 -m pytest agent/governance/tests -q → 全部通过
- 关键文件有 docstring 注释说明接口（agent/governance/core/rbac.py、policy.py、audit.py）

==================== Day 2 — Memory（Semantic / Session / Episodic / Archive / LRU） ====================
Goal：把 Memory 层从 PoC shim 完成到稳定、可测试、并有期望的接口（semantic_search 、archive_session/retrieve、LRUCache、Immediate/Session/Episodic）。

Day2-Task-2.1 — LRUCache 完整兼容（size= / put/get / __contains__）
- File: agent/memory/core/lru.py
- Minimal code (paste to implementer):
  ```python
  from collections import OrderedDict
  class LRUCache:
      def __init__(self, capacity=None, size=None):
          self.capacity = int(size or capacity or 1024)
          self._store = OrderedDict()
      def put(self, k,v):
          if k in self._store:
              self._store.pop(k)
          self._store[k]=v
          while len(self._store) > self.capacity:
              self._store.popitem(last=False)
      def get(self,k,default=None):
          if k not in self._store:
              return default
          v = self._store.pop(k)
          self._store[k]=v
          return v
      def __contains__(self,k):
          return k in self._store
  ```
- Test: pytest agent/memory/tests/test_layers_cover_more.py::test_lru_cache_eviction_and_contains -q
- Expected: pass
- Commit: git add && git commit -m "feat(memory): LRUCache compat implementation"

Day2-Task-2.2 — SemanticMemory: index & search fallback
- File: agent/memory/core/layers.py (SemanticMemory)
- Provide: index_item, store_knowledge_item, semantic_search(query, top_k, threshold=0.0) that first searches index payload content, then falls back to storage; provide semantic_index shim + embedding stub.
- Test: pytest agent/memory/tests/test_layers_edges.py::test_semantic_store_search_and_missing_index_item -q → pass

Day2-Task-2.3 — ArchiveMemory robust archive/retrieve & corruption detection
- File: agent/memory/core/layers.py (ArchiveMemory)
- Implement archive_session to write session and data marker; retrieve_archived_session must:
  - return None for unknown id
  - if data marker missing → raise ArchiveCorruptedError
  - if data marker is bytes → raise ArchiveCorruptedError
- Test: pytest agent/memory/tests/test_layers_gap2.py::test_archive_retrieve_corruption_detection_and_checksum -q → pass

Day2-Task-2.4 — EpisodicMemory event recording + pattern extraction
- Implement record_event to return EventRef (event_id, timestamp) and register created_at; implement extract_learned_patterns with permissive fallback.
- Test: pytest agent/memory/tests/test_layers_more2.py::test_episdodic_record_and_patterns -q → pass

验收 Day2
- python3 -m pytest agent/memory/tests -q → 全部 memory 相关 tests pass

==================== Day 3 — Automation（cron/benchmark） ====================
Goal：保证 benchmark runner 定时可运行、结果历史化到 implementation/automation/benchmarks，并有 cron job 模板。

Day3-Task-3.1 — benchmark_runner PoC check
- File: implementation/automation/benchmark_runner.py — 确保 runner 有 CLI: `python -m implementation.automation.benchmark_runner run --out path`。
- Test: Run `python3 implementation/automation/benchmark_runner.py --help` or `python3 -m implementation.automation.benchmark_runner run --out /tmp/bench.json` → 产生 JSON（iterations, monitor_avg_s 等）。
- Commit change if needed.

Day3-Task-3.2 — cron job template
- File: tools/cronjobs/benchmark_weekly.json (template)
- Provide example cron create command (hermes cronjob_manage create …) or local launch script: implementation/automation/benchmark_weekly.sh
- Verification: `bash implementation/automation/benchmark_weekly.sh` writes JSON to implementation/automation/benchmarks/bench_$(date).json

验收 Day3
- benchmark JSON 产物存在；cron 脚本能本地执行并产生产物。

==================== Day 4 — Orchestration（ExecutionPlan / Runner） ====================
Goal：提供可测试的 ExecutionPlan、SubTask、简单 runner 能模拟执行并回报 OperationResult。

Day4 tasks: (each 2–5 min)
- Add types in agent/core/types.py if missing: SubTask, ExecutionPlan, OperationResult (paths already exist; extend if needed).
- Implement simple runner: agent/orchestration/runner.py with function `run_plan(plan)` that executes subtasks sequentially, returns ExecutionResult.
- Test: write a unit test under agent/orchestration/tests/test_runner.py that constructs a plan with 2 dummy subtasks (function stubs) and asserts ExecutionResult.status == SUCCESS.

验收 Day4
- pytest agent/orchestration/tests -q -> pass

==================== Day 5 — Evolution（generator / HINDSIGHT） ====================
Goal：把模块自动生成器做成可用命令，且每次自动修补记录 HINDSIGHT（事件/决策）写入 Obsidian 目录。

Day5 tasks
- Ensure tools/generators/module_generator.py has CLI (argparse) producing a module file under agent/<framework>/core/<name>.py with template header.
- HINDSIGHT: .hermes/hindsight/HINDSIGHT.md template; after each automated fix run, append an entry (timestamp, file, reason, test name, commit id).
- Test: run `python3 tools/generators/module_generator.py --name test_mod --dest agent/temp` -> verify created file.

验收 Day5
- generator 能生成模块并通过 lint / 导入测试（pytest -q tests that import generated module）

==================== Day 6 — Multi-agent（Agent runtime / heartbeat / RPC） ====================
Goal：提供 AgentConfig/Agent runtime shim：心跳、简单 RPC（in-process stub），并能在本地模拟两个 agent 交互。

Day6 tasks
- Implement agent/agent_runtime.py with Agent class (start/stop/heartbeat), simple in-memory message bus.
- Write unit tests: agent/agent/tests/test_runtime.py - create two agents, send a message, expect delivery
- Verify: pytest agent/agent/tests -q → pass.

验收 Day6
- agent runtime tests通过；heartbeat 写入 .hermes/state/ 或日志文件。

==================== Day 7 — 收尾、文档、验收 ====================
Goal：整理所有 PoC -> 标注为 TODO 的 shim、生成 HINDSIGHT.md、写 Obsidian DAILY_PROGRESS，做最终全量测试与 smoke run。

Day7 tasks
- Produce TODOs list: scan repo for markers like "AUTO-SHIM", "PoC", "TODO"；保存到 .hermes/TO_REPLACE.md
- Generate HINDSIGHT.md：把本 7 天的每日日志和所有 commits 摘要写入 Obsidian 路径（/Users/huchufan/Documents/obsidian/obsidian_mac/INBOX_收集箱/Hermes/DAILY_PROGRESS_YYYYMMDD_HHMM.md）
  - 内容要包含：每日变更列表（文件+commit），失败 & 修复一览，下一步建议
- Full verification: run `python3 -m pytest -q --maxfail=1` expecting all green; then run the smoke script: `python3 -m agent.scripts.smoke` (implement simple smoke if missing) expecting `{"ok": true}`.

验收 Day7（最终验收标准）
- 本地 `pytest` 全绿（exit 0）；覆盖目录已保存（路径在 /Users/huchufan/Hermes/implementation/automation/coverage*）。
- Obsidian 已写入日报（文件路径按上面给出），本地 commit 完成。
- README.md 或 .hermes/README_EXECUTION.md 描述如何在本地重放这 7 天自动化循环（命令列举）。

风险、折中与未决问题
- Qdrant / 向量索引：需要独立授权与资源；当前使用 embedding stub。若要上线需授权“授权 Qdrant”并补充集成测试。
- PoC shim 的长期维护：计划把所有带注释的 AUTO-SHIM/PoC 转成 TODO 列表 Day7，建议逐条评估优先级替换。
- 自动化修补风险：自动 inject shim 有潜在隐藏问题（覆盖真实设计）——已把所有自动变更提交到本地分支，保留回滚点。

交付物
- .hermes/plans/YYYY-MM-DD_HHMMSS-7day-complete-implementation.md（本次计划文件）
- 每日 Obsidian 报告（Day7 汇总）
- 本地分支 auto/skill-evolution-apply 上的多次 commit（实现代码与测试）

下一步
- 你选：
  - "写入 Obsidian 并提交" → 我把最终 DAILY_PROGRESS 写入并做本地 commit（我会说明文件路径并提交）。
  - "授权 Qdrant" → 我在本地启动 qdrant 容器并把 SemanticMemory 集成到真实向量索引（需要确认资源与时长）。
  - "继续自动循环" → 我会持续监控并在未来失败时自动补丁并 commit（默认行为）。

结束。