// API调用封装模块

// 格式化提示词函数 - 现在直接使用window.formatPrompt
function formatPrompt(templateName, params = {}) {
    if (typeof window !== 'undefined' && window.formatPrompt) {
        return window.formatPrompt(templateName, params);
    } else {
        throw new Error('window.formatPrompt函数不可用');
    }
}

// 全局配置
let apiConfig = {
    platform: 'siliconflow', // 默认平台
    model: '', // 默认模型（根据步骤设置）
    apiKeys: {
        openai: '',
        siliconflow: '',
        deepseek: ''
    },
    baseUrls: {
        openai: 'https://api.openai.com/v1',
        siliconflow: 'https://api.siliconflow.cn/v1',
        deepseek: 'https://api.deepseek.com/v1'
    }
};

// 步骤特定的平台模型配置
const platformModelConfigs = {
    step1: {
        platform: 'siliconflow',
        model: '[16]千问'
    },
    step2: {
        platform: 'siliconflow',
        model: '[16]千问'
    },
    step3: {
        platform: 'siliconflow',
        model: '[16]千问'
    },
    step4: {
        platform: 'siliconflow',
        model: '[4]腾讯混元'
    },
    step5: {
        platform: 'siliconflow',
        model: '[4]千问长文'
    },
    step6: {
        platform: 'siliconflow',
        model: '[4]千问长文'
    },
    step7: {
        platform: 'siliconflow',
        model: '[16]千问'
    }
};

// 实际模型ID映射
const modelIdMap = {
    // 硅基流动平台模型
    '[16]千问': 'qwen/qwen1.5-14b-chat',
    '[4]千问长文': 'qwen/qwen1.5-72b-chat-longcontext',
    '[4]腾讯混元': 'hunyuan/hunyuan-4b-chat',
    
    // Deepseek平台模型
    'deepseek-chat': 'deepseek-chat',
    'deepseek-code': 'deepseek-coder',
    
    // OpenAI平台模型
    'gpt-4o': 'gpt-4o',
    'gpt-3.5-turbo': 'gpt-3.5-turbo'
};

// 设置API配置
export function setApiConfig(config) {
    apiConfig = { ...apiConfig, ...config };
    return apiConfig;
}

// 获取当前API配置
export function getApiConfig() {
    return apiConfig;
}

// 根据步骤获取平台和模型配置
export function getConfigForStep(step) {
    return platformModelConfigs[step] || platformModelConfigs.step1;
}

// 初始化API客户端（根据平台）
function initClient(platform) {
    switch (platform) {
        case 'openai':
            return {
                apiKey: apiConfig.apiKeys.openai,
                baseUrl: apiConfig.baseUrls.openai
            };
        case 'siliconflow':
            return {
                apiKey: apiConfig.apiKeys.siliconflow,
                baseUrl: apiConfig.baseUrls.siliconflow
            };
        case 'deepseek':
            return {
                apiKey: apiConfig.apiKeys.deepseek,
                baseUrl: apiConfig.baseUrls.deepseek
            };
        default:
            throw new Error(`不支持的平台: ${platform}`);
    }
}

// 构建请求头
function buildHeaders(client) {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${client.apiKey}`
    };
}

// 获取实际模型ID
export function getActualModelId(model) {
    return modelIdMap[model] || model;
}

// 构建请求体
function buildRequestBody(prompt, model, maxTokens = 8000, conversationHistory = null) {
    let messages = [];
    
    // 如果有会话历史，使用会话历史
    if (conversationHistory && Array.isArray(conversationHistory) && conversationHistory.length > 0) {
        messages = conversationHistory.slice(); // 复制会话历史
        // 追加当前提示词
        messages.push({
            role: 'user',
            content: prompt
        });
    } else {
        // 否则使用默认的系统消息和用户提示词
        messages = [
            {
                role: 'system',
                content: '你是一名网络文学创作者助手，擅长创作各种类型的网络小说。'
            },
            {
                role: 'user',
                content: prompt
            }
        ];
    }
    
    return {
        model: getActualModelId(model),
        messages: messages,
        max_tokens: maxTokens,
        temperature: 0.8,
        top_p: 0.9,
        stream: true // 使用流式响应
    };
}

// 处理流式响应
function handleStreamResponse(response, onChunk, onComplete, onError) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    function readChunk() {
        reader.read().then(({ done, value }) => {
            if (done) {
                onComplete(buffer);
                return;
            }
            
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            
            // 处理SSE格式的响应
            const lines = chunk.split('\n');
            for (const line of lines) {
                if (line.trim() === '') continue;
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') {
                        onComplete(buffer);
                        return;
                    }
                    try {
                        const parsedData = JSON.parse(data);
                        if (parsedData.choices && parsedData.choices[0] && parsedData.choices[0].delta && parsedData.choices[0].delta.content) {
                            const content = parsedData.choices[0].delta.content;
                            onChunk(content);
                        }
                    } catch (error) {
                        // 忽略解析错误
                    }
                }
            }
            
            readChunk();
        }).catch(error => {
            onError(error);
        });
    }
    
    readChunk();
}

// 重试机制
async function withRetry(func, maxRetries = 3, retryDelay = 3000) {
    let lastError;
    
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await func();
        } catch (error) {
            console.warn(`尝试 ${i + 1} 失败:`, error);
            lastError = error;
            
            // 如果是429错误，标记为中断
            if (error.response && error.response.status === 429) {
                throw new Error('API调用达到限流，请稍后再试');
            }
            
            // 等待一段时间后重试
            if (i < maxRetries - 1) {
                await new Promise(resolve => setTimeout(resolve, retryDelay));
            }
        }
    }
    
    throw lastError || new Error(`达到最大重试次数(${maxRetries})`);
}

// 调用OpenAI兼容的API
export async function callOpenaiApi(prompt, step = 'step1', onChunk = null, onComplete = null, onError = null, conversationHistory = null, maxTokens = 8000) {
    // 获取当前步骤的平台和模型配置
    const config = getConfigForStep(step);
    const { platform, model } = config;
    
    // 初始化客户端
    const client = initClient(platform);
    
    // 检查API密钥
    if (!client.apiKey) {
        const error = new Error(`请设置${platform}的API密钥`);
        if (onError) onError(error);
        throw error;
    }
    
    // 构建请求参数
    const requestBody = buildRequestBody(prompt, model, maxTokens, conversationHistory);
    const headers = buildHeaders(client);
    
    console.log(`调用API，平台: ${platform}, 模型: ${model}, 提示词长度: ${prompt.length}, max_tokens: ${maxTokens}`);
    
    // 定义API调用函数
    const apiCall = async () => {
        const response = await fetch(`${client.baseUrl}/chat/completions`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            let errorMessage = `API调用失败: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage += ` - ${errorData.error?.message || JSON.stringify(errorData)}`;
            } catch {
                // 忽略JSON解析错误
            }
            
            const error = new Error(errorMessage);
            // 标记限流错误
            if (response.status === 429) {
                error.isRateLimitError = true;
            }
            throw error;
        }
        
        // 处理流式响应
        if (onChunk && onComplete && onError) {
            return new Promise((resolve, reject) => {
                handleStreamResponse(response, onChunk, (fullContent) => {
                    // 检查内容是否可能被截断
                    if (fullContent.length >= maxTokens * 3) {  // 粗略估计，每个token约3个字符
                        const warningMsg = `生成的内容可能已达到长度限制，max_tokens: ${maxTokens}。请考虑增加max_tokens参数以获取完整内容。`;
                        console.warn(warningMsg);
                        // 可以在这里添加一个UI警告提示
                    }
                    
                    if (!fullContent) {
                        const error = new Error('API请求失败: 未获取到内容');
                        onError(error);
                        reject(error);
                        return;
                    }
                    
                    onComplete(fullContent);
                    resolve(fullContent);
                }, (error) => {
                    onError(error);
                    reject(error);
                });
            });
        } else {
            // 非流式处理
            const data = await response.json();
            const content = data.choices[0].message.content;
            
            // 检查内容是否可能被截断
            if (content.length >= maxTokens * 3) {
                console.warn(`生成的内容可能已达到长度限制，max_tokens: ${maxTokens}`);
            }
            
            return content;
        }
    };
    
    // 执行带重试的API调用
    try {
        return await withRetry(apiCall, platform === 'deepseek' ? 2 : 3, platform === 'deepseek' ? 2000 : 3000);
    } catch (error) {
        // 记录错误
        console.error('API调用错误:', error);
        
        // 处理限流错误
        if (error.isRateLimitError || error.message.includes('429') || 
            error.message.toLowerCase().includes('rate limit') || 
            error.message.toLowerCase().includes('tpm limit')) {
            const rateLimitError = new Error('API限流错误: TPM限制已达到，请等待一段时间后再试');
            rateLimitError.isRateLimitError = true;
            if (onError) onError(rateLimitError);
            return '<GENERATION_INTERRUPTED>'; // 返回中断标记
        }
        
        // 处理网络错误
        if (error.message.toLowerCase().includes('timeout') || 
            error.message.toLowerCase().includes('network') || 
            error.message.toLowerCase().includes('connection')) {
            const networkError = new Error('网络错误，请检查网络连接后重试');
            if (onError) onError(networkError);
            return '<GENERATION_INTERRUPTED>'; // 返回中断标记
        }
        
        // 其他类型的错误
        if (onError) onError(error);
        
        // 返回默认值
        return 'API调用失败，使用默认格式';
    }
}

// 生成选题
export async function generateTopic(params, onChunk, onComplete, onError) {
    const { storyType, dilemmaType, publishPlatform, emotions, inspiration } = params;
    
    try {
        // 检查是否有prompts模块可用
        if (typeof window !== 'undefined' && window.prompts && window.formatPrompt) {
            const prompt = window.formatPrompt('topic', {
                storyType,
                dilemmaType,
                publishPlatform,
                emotions,
                inspiration
            });
            
            // 模拟模式
            if (window.mockMode) {
                return simulateGeneration(`生成选题: ${storyType} + ${dilemmaType}`, onChunk, onComplete);
            }
            
            // 实际API调用
            return await callOpenaiApi(prompt, 'step1', onChunk, onComplete, onError);
        } else {
            // 如果没有prompts模块，使用模拟数据
            return new Promise(resolve => {
                setTimeout(() => {
                    const mockTopic = `你们知道，在这个金钱至上的社会，没钱的人连呼吸都有罪吗？\n我妈躺在医院重症监护室，每天的费用就像流水一样。\n我跪在医院走廊里，给所有认识的人打电话借钱。\n可他们不是说最近手头紧，就是直接挂断电话。\n直到我收到一条陌生短信：「想救你妈？来XX大厦23楼。」`;
                    if (onComplete) onComplete(mockTopic);
                    resolve(mockTopic);
                }, 1500);
            });
        }
    } catch (error) {
        console.error('生成选题时出错:', error);
        if (onError) onError(error);
        throw error;
    }
}

// 生成人物设定
export async function generateCharacters(params, onChunk, onComplete, onError) {
    const { topic, storyType } = params;
    
    try {
        // 检查是否有prompts模块可用
        if (typeof window !== 'undefined' && window.prompts && window.formatPrompt) {
            const prompt = window.formatPrompt('protagonist', {
                topic,
                storyType
            });
            
            // 模拟模式
            if (window.mockMode) {
                return simulateGeneration('生成人物设定', onChunk, onComplete);
            }
            
            // 实际API调用
            return await callOpenaiApi(prompt, 'step2', onChunk, onComplete, onError);
        } else {
            // 如果没有prompts模块，使用模拟数据
            return new Promise(resolve => {
                setTimeout(() => {
                    const mockCharacters = `主角：
姓名：林风
年龄：28岁
外貌特征：身材消瘦，眼神中透着股狠劲，左眼角有一道细长的疤痕
职业/身份：外卖员
性格特点：坚韧不拔，重情义
核心动机：救母亲
深层创伤：父亲早逝，从小被人看不起
标志性动作：紧张时会摸左眼角的疤痕
价值观：亲情大于一切

反派：
姓名：张老板
年龄：45岁
外貌特征：肥胖，戴着金丝眼镜，总是挂着假笑
职业/身份：高利贷公司老板
性格特点：心狠手辣，唯利是图
行为动机：利用林风的困境获取利益
背景故事：出身贫寒，通过不正当手段发家
与主角的关系：债主与债务人`;
                    if (onComplete) onComplete(mockCharacters);
                    resolve(mockCharacters);
                }, 1500);
            });
        }
    } catch (error) {
        console.error('生成人物设定时出错:', error);
        if (onError) onError(error);
        throw error;
    }
}

// 生成大纲
export async function generateOutline(params, onChunk, onComplete, onError) {
    const { topic, characters, storyType } = params;
    
    try {
        // 检查是否有prompts模块可用
        if (typeof window !== 'undefined' && window.prompts && window.formatPrompt) {
            const prompt = window.formatPrompt('outline', {
                topic,
                characters,
                storyType
            });
            
            // 模拟模式
            if (window.mockMode) {
                return simulateGeneration('生成大纲', onChunk, onComplete);
            }
            
            // 实际API调用
            return await callOpenaiApi(prompt, 'step3', onChunk, onComplete, onError);
        } else {
            // 如果没有prompts模块，使用模拟数据
            return new Promise(resolve => {
                setTimeout(() => {
                    const mockOutline = `1. 林风接到医院电话，母亲病情恶化，需要巨额手术费\n2. 林风四处借钱无果，陷入绝望\n3. 收到神秘短信，前往XX大厦23楼\n4. 遇到张老板，被迫签下高利贷合同\n5. 为了还钱，林风开始拼命工作\n6. 发现张老板的阴谋，决定反击\n7. 经过一系列斗争，最终救回母亲并揭露张老板的罪行`;
                    if (onComplete) onComplete(mockOutline);
                    resolve(mockOutline);
                }, 1500);
            });
        }
    } catch (error) {
        console.error('生成大纲时出错:', error);
        if (onError) onError(error);
        throw error;
    }
}

// 生成细纲
export async function generateDetailedOutline(params, onChunk, onComplete, onError) {
    const { topic, characters, outline, outlineTemp, previousDetailedOutline } = params;
    
    try {
        // 检查是否有prompts模块可用
        if (typeof window !== 'undefined' && window.prompts && window.formatPrompt) {
            const prompt = window.formatPrompt('detail_outline', {
                topic,
                characters,
                outline,
                outlineTemp,
                previousDetailedOutline
            });
            
            // 模拟模式
            if (window.mockMode) {
                return simulateGeneration('生成细纲', onChunk, onComplete);
            }
            
            // 实际API调用
            return await callOpenaiApi(prompt, 'step4', onChunk, onComplete, onError);
        } else {
            // 如果没有prompts模块，使用模拟数据
            return new Promise(resolve => {
                setTimeout(() => {
                    const mockDetailedOutline = `## 冲突一\n- **目标**：林风需要在24小时内凑齐10万元手术费\n- **阻碍**：所有亲戚朋友都拒绝借钱，医院不断催款\n- **行动**：林风跪在医院走廊给所有联系人打电话，甚至向陌生人求助\n\n## 冲突二\n- **目标**：找到神秘短信的发件人，寻求帮助\n- **阻碍**：XX大厦23楼是一家高利贷公司，充满危险\n- **行动**：林风硬着头皮前往XX大厦，内心充满恐惧但为了母亲不得不冒险\n\n## 冲突三\n- **目标**：说服张老板宽限还款时间\n- **阻碍**：张老板提出苛刻条件，要求林风签署高额利息的合同\n- **行动**：林风在绝望中签署合同，发誓一定会尽快还钱`;
                    if (onComplete) onComplete(mockDetailedOutline);
                    resolve(mockDetailedOutline);
                }, 1500);
            });
        }
    } catch (error) {
        console.error('生成细纲时出错:', error);
        if (onError) onError(error);
        throw error;
    }
}

// 生成正文
export async function generateContent(params, onChunk, onComplete, onError) {
    const { topic, characters, selectedDetailedOutline, min_size } = params;
    
    try {
        // 检查是否有prompts模块可用
        if (typeof window !== 'undefined' && window.prompts && window.formatPrompt) {
            const prompt = window.formatPrompt('content', {
                topic,
                characters,
                selectedDetailedOutline,
                min_size
            });
            
            // 模拟模式
            if (window.mockMode) {
                return simulateGeneration('生成正文', onChunk, onComplete);
            }
            
            // 实际API调用
            return await callOpenaiApi(prompt, 'step5', onChunk, onComplete, onError);
        } else {
            // 如果没有prompts模块，使用模拟数据
            return new Promise(resolve => {
                setTimeout(() => {
                    const mockContent = `医院的消毒水味冲进鼻腔的时候。\n我正在送今天的第三十单外卖。\n手机在裤兜里疯狂震动。\n我手忙脚乱地停车，接起电话。\n「林风先生，您母亲的病情突然恶化，需要立即进行手术。」\n护士的声音像一把锤子。\n重重砸在我心上。\n「手术费需要10万，您能在24小时内凑齐吗？」\n我握着手机的手开始发抖。\n10万。\n对我来说，简直是天文数字。\n我是个外卖员，一个月拼死拼活也就赚八千块。\n除去房租和母亲的医药费，根本存不下钱。\n我蹲在马路边，给所有认识的人打电话。\n「喂，王哥，能借我点钱吗？我妈住院了。」\n「林风啊，不是哥不帮你，最近生意不好做...」\n电话那头传来忙音。\n我又拨通下一个号码。\n「李姐，我是小风，您能...」\n「小风啊，我女儿马上要交学费了，实在没钱...」\n夕阳西下的时候。\n我已经打了二十多个电话。\n没有一个人愿意借钱给我。\n手机突然收到一条短信。\n「想救你妈？来XX大厦23楼。」\n发件人是未知号码。\n我盯着手机屏幕。\nXX大厦我知道。\n那是市中心最豪华的写字楼。\n但23楼...\n我好像听说过。\n那里是一家高利贷公司。\n我咬了咬牙。\n不管怎样。\n只要能救我妈。\n让我做什么都愿意。`;
                    if (onComplete) onComplete(mockContent);
                    resolve(mockContent);
                }, 1500);
            });
        }
    } catch (error) {
        console.error('生成正文时出错:', error);
        if (onError) onError(error);
        throw error;
    }
}

// 生成标题
export async function generateTitle(params, onChunk, onComplete, onError) {
    const { content } = params;
    
    try {
        // 检查是否有prompts模块可用
        if (typeof window !== 'undefined' && window.prompts && window.formatPrompt) {
            const prompt = window.formatPrompt('title', {
                content
            });
            
            // 模拟模式
            if (window.mockMode) {
                return simulateGeneration('生成标题', onChunk, onComplete);
            }
            
            // 实际API调用
            return await callOpenaiApi(prompt, 'step6', onChunk, onComplete, onError);
        } else {
            // 如果没有prompts模块，使用模拟数据
            return new Promise(resolve => {
                setTimeout(() => {
                    const mockTitle = `A类：救母记\nB类：24小时的救赎\nC类：外卖员的绝境求生`;
                    if (onComplete) onComplete(mockTitle);
                    resolve(mockTitle);
                }, 1500);
            });
        }
    } catch (error) {
        console.error('生成标题时出错:', error);
        if (onError) onError(error);
        throw error;
    }
}

// 生成导语
export async function generateIntro(params, onChunk, onComplete, onError) {
    const { topic, characters, content } = params;
    
    try {
        // 检查是否有prompts模块可用
        if (typeof window !== 'undefined' && window.prompts && window.formatPrompt) {
            const prompt = window.formatPrompt('intro', {
                topic,
                characters,
                content
            });
            
            // 模拟模式
            if (window.mockMode) {
                return simulateGeneration('生成导语', onChunk, onComplete);
            }
            
            // 实际API调用
            return await callOpenaiApi(prompt, 'step7', onChunk, onComplete, onError);
        } else {
            // 如果没有prompts模块，使用模拟数据
            return new Promise(resolve => {
                setTimeout(() => {
                    const mockIntro = `你们知道，在这个金钱至上的社会，没钱的人连呼吸都有罪吗？\n我妈躺在医院重症监护室，每天的费用就像流水一样。\n我跪在医院走廊里，给所有认识的人打电话借钱。\n可他们不是说最近手头紧，就是直接挂断电话。\n直到我收到一条陌生短信：「想救你妈？来XX大厦23楼。」`;
                    if (onComplete) onComplete(mockIntro);
                    resolve(mockIntro);
                }, 1500);
            });
        }
    } catch (error) {
        console.error('生成导语时出错:', error);
        if (onError) onError(error);
        throw error;
    }
}

// 模拟生成过程（用于开发测试）
function simulateGeneration(type, onChunk, onComplete) {
    return new Promise((resolve) => {
        let content = '';
        const chunks = [`${type}开始生成...\n`, `正在努力创作中...\n`, `内容即将完成...\n`, `生成完毕！`];
        let index = 0;
        
        const interval = setInterval(() => {
            if (index < chunks.length) {
                content += chunks[index];
                if (onChunk) onChunk(chunks[index]);
                index++;
            } else {
                clearInterval(interval);
                if (onComplete) onComplete(content);
                resolve(content);
            }
        }, 800);
    });
}

// 导出所有API函数
export default {
    callOpenaiApi,
    generateTopic,
    generateCharacters,
    generateOutline,
    generateDetailedOutline,
    generateContent,
    generateTitle,
    generateIntro,
    setApiConfig,
    getApiConfig,
    getConfigForStep
};