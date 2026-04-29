---
name: refactor
trigger: 重构
category: quality
when_to_use: 当需要改进现有代码质量时使用
examples:
  - "重构这段代码"
  - "帮我优化下这个模块"
description: 渐进式代码重构，小步改进，每次保持可运行状态
phases:
  - name: 理解现状
    steps:
      - instruction: 阅读代码理解当前结构
        check: 知道代码做什么
      - instruction: 识别问题区域
        check: 列出需要改进的地方
      - instruction: 确认测试覆盖
        check: 有测试保障重构
    checklist:
      - 理解代码意图
      - 有测试或手动验证方式
  - name: 小步改进
    steps:
      - instruction: 每次只改一件事
        check: 改动小且专注
      - instruction: 立即运行测试
        check: 测试仍然通过
    checklist:
      - 每次改动小（5-15分钟）
      - 每次都保持可运行
  - name: 清理
    steps:
      - instruction: 移除无用代码
        check: 没有死代码
      - instruction: 整理命名
        check: 命名一致且清晰
    checklist:
      - 代码比之前干净
      - 没有技术债增加
---
