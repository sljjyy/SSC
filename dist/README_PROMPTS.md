# 故事类型特定提示词使用指南

## 概述

本项目支持为不同的故事类型提供特定的提示词文件，以生成更符合该类型风格的内容。当用户在应用中选择某种故事类型时，系统会优先加载该类型对应的提示词文件。

## 故事类型目录结构

项目已为以下故事类型创建了专用提示词目录：

- `prompts/世情`
- `prompts/穿越`
- `prompts/悬疑`
- `prompts/修仙`
- `prompts/科幻`
- `prompts/奇幻`
- `prompts/都市`
- `prompts/历史`
- `prompts/军事`
- `prompts/游戏`
- `prompts/体育`

## 如何为特定故事类型创建提示词

1. 在对应的故事类型目录中创建与默认目录中相同名称的提示词文件
2. 修改文件内容以适应该故事类型的特点和要求

### 必需的提示词文件

以下是项目使用的所有提示词文件列表，请确保为每种类型创建这些文件：

- `topic.prompt` - 选题生成提示词
- `outline.prompt` - 粗纲生成提示词
- `detailed_outline_first.prompt` - 第一个细纲生成提示词
- `detailed_outline_subsequent.prompt` - 后续细纲生成提示词
- `content_first.prompt` - 第一个正文生成提示词
- `content_subsequent.prompt` - 后续正文生成提示词
- `content_last.prompt` - 最后一部分正文生成提示词（用于结尾）
- `title.prompt` - 标题生成提示词
- `intro.prompt` - 导语生成提示词
- `protagonist.prompt` - 主角生成提示词
- `antagonist.prompt` - 反派生成提示词
- `supporting.prompt` - 配角生成提示词

## 回退机制

如果某个故事类型的目录中缺少某个提示词文件，系统会自动回退使用`prompts`根目录中的同名文件。这意味着：

1. 您只需为需要自定义的故事类型创建相应的提示词文件
2. 不需要自定义的文件会自动使用默认版本
3. 新添加的故事类型不需要立即创建所有提示词文件

## 使用示例

例如，要为"悬疑"类型创建特定的正文生成提示词：

1. 复制`prompts/content_first.prompt`到`prompts/悬疑/content_first.prompt`
2. 编辑`prompts/悬疑/content_first.prompt`，添加悬疑故事特有的风格要求
3. 当用户在应用中选择"悬疑"类型时，系统会自动使用这个自定义的提示词

## 最佳实践

- 为每种故事类型至少创建最关键的提示词文件（如content_first.prompt、content_subsequent.prompt、content_last.prompt）
- 在特定类型的提示词中强调该类型的独特风格、结构和元素
- 保持提示词中的变量格式一致，确保能够正确替换内容
- 定期更新和优化提示词以获得更好的生成效果

## 注意事项

- 提示词文件必须使用UTF-8编码
- 文件名必须与默认目录中的文件完全一致
- 自定义提示词中包含的变量（如`{topic}`, `{characters}`, `{selected_detailed_outline}`等）必须保持不变
- 为了获得最佳效果，建议至少对`content_first.prompt`、`content_subsequent.prompt`和`content_last.prompt`进行类型特定的优化