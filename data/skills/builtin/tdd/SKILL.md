---
name: tdd
trigger: 测试
category: development
when_to_use: 当需要实现新功能或修复bug时使用
examples:
  - "TDD 写个计算器"
  - "用测试驱动开发实现队列"
description: 红-绿-重构循环，先写失败测试，再写通过实现，最后重构改进
phases:
  - name: Red — 写失败测试
    steps:
      - instruction: 描述期望的行为
        check: 测试描述的是行为而非实现
      - instruction: 运行测试确认失败
        check: 测试失败信息清晰
      - instruction: 验证测试确实测了目标功能
        check: 测试覆盖了核心场景
    checklist:
      - 测试是描述性的
      - 失败信息有助于调试
  - name: Green — 写通过实现
    steps:
      - instruction: 用最简单的方式通过测试
        check: 所有测试通过
      - instruction: 避免提前优化
        check: 代码简洁
    checklist:
      - 最少量代码通过所有测试
      - 没有伪造实现
  - name: Refactor — 重构改进
    steps:
      - instruction: 消除重复代码
        check: 没有重复逻辑
      - instruction: 提升可读性
        check: 命名清晰，函数短小
      - instruction: 运行测试确认重构未破坏功能
        check: 所有测试仍然通过
    checklist:
      - 代码比重构前更干净
      - 没有引入新的问题
  - name: Repeat — 循环
    steps:
      - instruction: 对每个新需求重复 Red-Green-Refactor
        check: 测试覆盖持续增加
    checklist:
      - 持续小步前进
      - 每步都有测试保障
---
