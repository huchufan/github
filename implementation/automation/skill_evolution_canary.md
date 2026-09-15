# Skill evolution canary pipeline

目的：在应用 skill 演化补丁前，先在小规模 Canary 环境执行安全扫描、单元 + 集成测试、行为回放与监控指标检查；通过后再按批量向生产面发布。

阶段：
1) 收集补丁，生成变更包（patch bundle）
2) 在隔离容器/工作区应用补丁
3) 运行自动安全扫描（bandit/semgrep + 自定义 Lint）
4) 运行测试套件（unit + integration）
5) 运行演化回放（replay）与比对行为差异（Hindsight 差分）
6) 指标评估（错误率、延迟、外部调用成本）
7) Canary 通过后分批发布，并在每批后回退窗口内监控

CI skeleton: .github/workflows/canary-skill-evolution.yml

可配置参数：canary_size(默认 1), rollback_on_fail(true), scan_tools:[bandit,semgrep], test_timeout(300)
