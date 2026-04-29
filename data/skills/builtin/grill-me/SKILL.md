---
name: grill-me
trigger: 帮我
category: requirements
when_to_use: 当用户需求不明确或太模糊时使用
examples:
  - "帮我写个排序"
  - "帮我做个登录"
description: 通过反问澄清用户需求，确保理解准确再开始实现
phases:
  - name: 澄清意图
    steps:
      - instruction: 询问具体的使用场景
        check: 用户提供了场景描述
      - instruction: 询问目标用户是谁
        check: 目标用户已明确
      - instruction: 询问成功标准是什么
        check: 验收条件已定义
    checklist:
      - 有具体的业务场景
      - 有明确的目标用户
      - 有可衡量的成功标准
---
