<!-- APEX-COMMANDER-RULE:START -->
# High-Complexity Task Routing Rule (`apex-commander`)

Whenever a user request meets ANY of the following criteria, you MUST read and follow the `apex-commander` skill (`SKILL.md`) BEFORE writing implementation code:
1. Creating or refactoring **3 or more modules/files**, designing system architecture, building end-to-end multi-component features, or solving high-difficulty algorithmic/engineering tasks;
2. The user mentions `apex-commander`, "commander mode", "hierarchical agents", or Chinese triggers such as 「指挥官」「总指挥」「上强度」「多子代理」「并发开发」.

In these tasks, reserve the main flagship high-reasoning model strictly for architecture, shared contracts, conflict-free task sharding, and global evaluation — delegate parallel implementation waves to `flash` (1 tier weaker) and `flash_lite` (2 tiers weaker) subagents.
<!-- APEX-COMMANDER-RULE:END -->
