---
name: vertical-slice
trigger: 切片
category: development
when_to_use: 当功能太大需要分步交付时使用
examples:
  - "垂直切片实现这个功能"
  - "分切片做这个功能"
description: 端到端小步迭代，每切片包含完整功能闭环
phases:
  - name: 识别最小切片
    steps:
      - instruction: 确定最小可工作的功能
        check: 包含输入到输出的完整路径
      - instruction: 识别核心路径
        check: 用户能完成核心操作
    checklist:
      - 切片足够小（1-2天）
      - 有明确的用户价值
  - name: 实现端到端
    steps:
      - instruction: 实现数据模型
        check: 包含必要的字段
      - instruction: 实现业务逻辑
        check: 处理核心场景
      - instruction: 实现接口/UI
        check: 用户能实际使用
    checklist:
      - 数据层完成
      - 逻辑层完成
      - 接口/表现层完成
  - name: 验证切片
    steps:
      - instruction: 功能可实际运行
        check: 端到端可用
      - instruction: 记录未完成部分
        check: 有清晰的下一切片计划
    checklist:
      - 切片可演示
      - 下一部分有记录
---
