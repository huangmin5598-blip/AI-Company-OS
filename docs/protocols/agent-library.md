# Agent Library

**Purpose**: Define reusable agent templates to reduce the cost of building each new project from scratch.

## Why It Exists

Every new project shouldn't require creating agents from zero. We have proven agent patterns — they should be reusable.

Agent Library provides templates for common roles.

## Key Mechanism

```
New Project
  → Select Agent Templates from Library
    → Customize for Project
      → Deploy
```

## Template Categories

### Lead Roles
| Template | Purpose | Key Capabilities |
|----------|---------|-------------------|
| lead-novel | Novel project lead | 选题, 调度, 验收 |
| lead-hub | Web project lead | 规划, 架构 |
| lead-sticker | Tool project lead | 产品, 开发 |

### Execution Roles
| Template | Purpose | Key Capabilities |
|----------|---------|-------------------|
| story-editor | Structure design | 大纲, 章节规划 |
| writer | Content production | 正文, 场景, 对话 |
| review-editor | Quality control | 审核, PASS/REVISION |
| researcher | Market research | 扫描, 分析, 报告 |

### Support Roles
| Template | Purpose | Key Capabilities |
|----------|---------|-------------------|
| tiger-coder | System development | 代码, 架构 |
| content-manager | Content operations | 规划, 发布 |

## How It's Used

1. **Project Definition**: Determine what roles needed
2. **Template Selection**: Choose from library
3. **Customization**: Adjust capabilities for specific project
4. **Deployment**: Agents ready to execute

## Example / Application

**New project: AI课程平台**
- Need: lead, writer, designer
- Available templates: lead-novel (adaptable), writer (usable), tiger-coder (for system)
- Customization: writer trained on course content
- Deployment: 3 agents ready

## Current Limitations

- Limited agent types in library
- Customization requires manual config
- Not all templates fully tested

## Next Evolution

- Expand library with more proven patterns
- Automated template matching to project type
- Self-configuring templates
