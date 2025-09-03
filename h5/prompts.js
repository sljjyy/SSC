// 提示词模板缓存
let promptTemplates = {};

// 提示词文件列表，与Python项目保持一致
const promptFiles = [
    'topic.prompt',
    'protagonist.prompt',
    'antagonist.prompt',
    'supporting.prompt',
    'outline.prompt',
    'detailed_outline_first.prompt',
    'detailed_outline_subsequent.prompt',
    'content_first.prompt',
    'content_subsequent.prompt',
    'title.prompt',
    'intro.prompt'
];

// 提示词别名映射
const promptAliases = {
    'detail_outline': 'detailed_outline_first',
    'content': 'content_first'
};

/**
 * 从文件加载单个提示词
 */
async function loadPromptFile(filename) {
    try {
        // 构造文件路径
        const filePath = `prompts/${filename}`;
        
        // 发送请求获取文件内容
        const response = await fetch(filePath, {
            method: 'GET',
            headers: {
                'Content-Type': 'text/plain'
            }
        });
        
        // 检查响应状态
        if (!response.ok) {
            throw new Error(`加载提示词文件失败: ${filename}, 状态码: ${response.status}`);
        }
        
        // 获取文件内容
        const content = await response.text();
        
        // 提取文件名（不含扩展名）作为键
        const key = filename.replace('.prompt', '');
        
        return { key, content };
    } catch (error) {
        console.error(`加载提示词文件 ${filename} 时出错:`, error);
        // 返回默认内容
        return { 
            key: filename.replace('.prompt', ''), 
            content: `生成${filename.replace('.prompt', '')}...` 
        };
    }
}

/**
 * 从文件加载所有提示词
 */
async function loadPromptsFromFiles() {
    try {
        // 并行加载所有提示词文件
        const results = await Promise.all(promptFiles.map(loadPromptFile));
        
        // 构建提示词模板对象
        const templates = {};
        results.forEach(({ key, content }) => {
            templates[key] = content;
        });
        
        // 添加别名
        Object.entries(promptAliases).forEach(([alias, original]) => {
            templates[alias] = templates[original];
        });
        
        return templates;
    } catch (error) {
        console.error('加载提示词文件时出错:', error);
        // 返回备用的模拟数据
        return {
            topic: "生成一个吸引人的故事选题...",
            protagonist: "生成主角设定...",
            antagonist: "生成反派设定...",
            supporting: "生成配角设定...",
            outline: "生成故事粗纲...",
            detailed_outline_first: "生成第一部分细纲...",
            detailed_outline_subsequent: "生成后续部分细纲...",
            content_first: "生成第一段正文...",
            content_subsequent: "生成后续段落正文...",
            title: "生成故事标题...",
            intro: "生成故事导语...",
            detail_outline: "生成第一部分细纲...",
            content: "生成第一段正文..."
        };
    }
}

/**
 * 格式化提示词
 */
function formatPrompt(templateName, params = {}) {
    // 处理别名
    const actualTemplateName = promptAliases[templateName] || templateName;
    
    // 获取提示词模板
    const template = promptTemplates[actualTemplateName];
    if (!template) {
        console.error(`未找到提示词模板: ${templateName} (${actualTemplateName})`);
        return '';
    }
    
    // 替换模板中的变量
    let formattedPrompt = template;
    for (const [key, value] of Object.entries(params)) {
        const placeholder = `\$\{${key}\\}`;
        formattedPrompt = formattedPrompt.replace(new RegExp(placeholder, 'g'), value || '');
    }
    
    return formattedPrompt;
}

/**
 * 加载提示词的主函数
 */
async function loadPrompts() {
    if (Object.keys(promptTemplates).length === 0) {
        promptTemplates = await loadPromptsFromFiles();
    }
    return promptTemplates;
}

// 导出到全局窗口对象，供app.js和api.js使用
window.prompts = promptTemplates;
window.loadPrompts = loadPrompts;
window.formatPrompt = formatPrompt;

// 初始化自动加载
loadPrompts().then(() => {
    window.prompts = promptTemplates;
    console.log('提示词加载完成');
}).catch(error => {
    console.error('自动加载提示词失败:', error);
});

// 导出为模块
export { loadPrompts, formatPrompt };
export default promptTemplates;