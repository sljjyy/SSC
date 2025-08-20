# 文学创作辅助工具

这是一个用于创作5万字以内短故事的Python工具，带有用户界面（UI）。用户可以通过选择故事类型、困境类型、投稿平台以及输入灵感，来生成故事的选题、人设、粗纲、细纲、正文、标题和导语。

## 功能特点

1. 提供故事类型、困境类型和投稿平台的选择
2. 根据用户输入的灵感生成故事内容
3. 允许用户在创作过程中暂停、重新输入或手动修改
4. 将不同部分的内容保存到不同的文件中
5. 每次创作的内容存放在单独的目录中，方便管理和投稿

## 使用说明

1. 确保已安装Python环境
2. 安装依赖：`pip install -r requirements.txt`
3. 运行工具：`python main.py`
4. 在UI界面中选择故事类型、困境类型、投稿平台
5. 在灵感输入框中输入您的创作灵感
6. 点击"生成"按钮开始创作
7. 工具将依次生成选题、人设、粗纲、细纲、正文、标题和导语
8. 每个步骤都可以确认或重新输入
9. 所有内容将自动保存到以时间戳命名的文件夹中

## 文件结构

每次生成的故事内容将保存在独立的文件夹中，包含以下文件：
- `topic.txt`：包含故事类型、困境类型、投稿平台、灵感和选题
- `characters.txt`：包含主角、反派、配角的人物设定
- `outline.txt`：包含故事的粗纲
- `detailed_outline.txt`：包含故事的细纲
- `content.txt`：包含完整的故事正文
- `title_intro.txt`：包含故事的标题和导语

此外，`prompts` 文件夹中包含了各个步骤使用的提示词文件：
- `topic.prompt`：用于生成选题
- `protagonist.prompt`、`antagonist.prompt`、`supporting.prompt`：分别用于生成主角、反派、配角的人物设定
- `outline.prompt`：用于生成粗纲
- `detailed_outline_first.prompt`、`detailed_outline_subsequent.prompt`：分别用于生成细纲的第一组和后续组
- `content_first.prompt`、`content_subsequent.prompt`：分别用于生成正文的第一段和后续段落
- `title.prompt`、`intro.prompt`：分别用于生成标题和导语

## 自定义指南

1. **修改选项**：在 `main.py` 的 `create_widgets` 方法中，可以修改故事类型、困境类型和投稿平台的下拉选项。
2. **配置API密钥**：在 `config.json` 文件中，将 `api_key` 的值修改为你的通义千问API密钥。
3. **自定义提示词**：每个步骤的提示词都存储在 `prompts` 文件夹下的单独 `.prompt` 文件中，可以直接修改这些文件来定制提示词。支持的变量包括：
   - `story_type`：故事类型
   - `dilemma_type`：困境类型
   - `inspiration`：灵感
   - `topic`：选题
   - `characters`：人物设定
   - `outline`：粗纲
   - `detailed_outline`：细纲
   - `content`：正文内容（在标题和导语生成中使用时会截取前500个字符）
   
   标题和导语现在使用独立的提示词文件 `title.prompt` 和 `intro.prompt`。
   
   人物设定现在将主角、反派、配角的提示词分开，分别使用 `protagonist.prompt`、`antagonist.prompt` 和 `supporting.prompt` 文件，并且在同一会话中分开调用各自的提示词。
   
   细纲是基于粗纲的内容进行生成，需要连续对话。粗纲是个数组，数组的0,-1,-2位置是单独1组，其他都是每次使用2个生成细纲。第一组使用 `detailed_outline_first.prompt` 提示词文件，后续组使用 `detailed_outline_subsequent.prompt` 提示词文件，并且在同一会话中分开调用各自的提示词。调用轮数根据粗纲返回的数组长度决定。
   
   正文是基于细纲的内容进行生成，需要连续对话。细纲是个数组，每次使用1个生成正文。第一段使用 `content_first.prompt` 提示词文件，后续段落使用 `content_subsequent.prompt` 提示词文件，并且在同一会话中分开调用各自的提示词。调用轮数根据细纲返回的数组长度决定。
4. **配置模型**：在 `config.json` 文件中，可以配置以下参数：
   - `api_key`：API密钥
   - `model`：选择使用的模型，可选值包括 `qwen-plus`、`deepseek`、`doubao`
   - `base_url`：API的基础URL
   
   例如，使用Deepseek模型的配置如下：
   ```json
   {
     "api_key": "your-deepseek-api-key",
     "model": "deepseek",
     "base_url": "https://api.deepseek.com/v1"
   }
   ```
   https://platform.deepseek.com/
   登录后，点击左侧菜单的“模型”，选择“Deepseek”模型，即可获取API密钥。
   点击“创建API密钥”，输入密钥名称，即可获取API密钥。
   点击“复制”，即可将API密钥复制到剪贴板。
   点击“关闭”，即可关闭弹窗。
   点击“保存”，即可将API密钥保存到 `config.json` 文件中。




4. **修改AI生成逻辑**：在 `main.py` 中找到对应的 `generate_xxx` 方法，修改其中的AI生成逻辑。目前使用的是通义千问API调用，可以根据需要调整提示词和参数。