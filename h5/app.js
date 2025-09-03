// 全局配置和状态
import api from './api.js';

const appState = {
    currentStep: 1,
    totalSteps: 7,
    generatedContent: {},
    currentGenerationState: {},
    isInterrupted: false,
    clients: {},
    platformModelConfigs: {},
    currentPlatform: "siliconflow",
    currentModel: "[16]千问",
    prompts: {},
    config: {
        api_key: "",
        base_url: "",
        siliconflow_api_key: "",
        deepseek_api_key: ""
    },
    TIME_SLEEP: 20,
    CONTENT_SIZE_MIN: 1000
};

// DOM元素
const dom = {
    stepContainer: document.getElementById('stepContainer'),
    currentStepText: document.getElementById('currentStepText'),
    prevBtn: document.getElementById('prevBtn'),
    nextBtn: document.getElementById('nextBtn'),
    configBtn: document.getElementById('configBtn'),
    configModal: document.getElementById('configModal'),
    closeConfigBtn: document.getElementById('closeConfigBtn'),
    saveConfigBtn: document.getElementById('saveConfigBtn'),
    loadingModal: document.getElementById('loadingModal'),
    loadingText: document.getElementById('loadingText'),
    deepseekApiKey: document.getElementById('deepseekApiKey'),
    siliconflowApiKey: document.getElementById('siliconflowApiKey'),
    openaiApiKey: document.getElementById('openaiApiKey')
};

// 初始化函数
async function init() {
    // 加载配置
    loadConfig();
    // 加载平台模型配置
    loadPlatformModelConfigs();
    // 加载提示词
    await loadPrompts();
    // 绑定事件
    bindEvents();
    // 显示当前步骤
    showStep(appState.currentStep);
}

// 绑定事件
function bindEvents() {
    dom.prevBtn.addEventListener('click', goToPrevStep);
    dom.nextBtn.addEventListener('click', async () => {
        await goToNextStep();
    });
    dom.configBtn.addEventListener('click', openConfigModal);
    dom.closeConfigBtn.addEventListener('click', closeConfigModal);
    dom.saveConfigBtn.addEventListener('click', saveConfig);
}

// 显示指定步骤
function showStep(step) {
    appState.currentStep = step;
    dom.currentStepText.textContent = `步骤 ${step}/${appState.totalSteps}`;
    
    // 更新步骤指示器
    for (let i = 1; i <= appState.totalSteps; i++) {
        const indicator = document.getElementById(`stepIndicator${i}`);
        if (i < step) {
            indicator.className = 'step-completed flex flex-col items-center';
        } else if (i === step) {
            indicator.className = 'step-active flex flex-col items-center';
        } else {
            indicator.className = 'step-pending flex flex-col items-center';
        }
    }
    
    // 更新按钮状态
    dom.prevBtn.disabled = step === 1;
    
    // 清空容器
    dom.stepContainer.innerHTML = '';
    
    // 根据步骤显示内容
    switch (step) {
        case 1:
            renderStep1();
            dom.nextBtn.innerHTML = '开始生成 <i class="fa fa-arrow-right ml-1"></i>';
            break;
        case 2:
            renderStep2();
            dom.nextBtn.innerHTML = '生成人物设定 <i class="fa fa-arrow-right ml-1"></i>';
            break;
        case 3:
            renderStep3();
            dom.nextBtn.innerHTML = '生成粗纲 <i class="fa fa-arrow-right ml-1"></i>';
            break;
        case 4:
            renderStep4();
            dom.nextBtn.innerHTML = '生成细纲 <i class="fa fa-arrow-right ml-1"></i>';
            break;
        case 5:
            renderStep5();
            dom.nextBtn.innerHTML = '生成正文 <i class="fa fa-arrow-right ml-1"></i>';
            break;
        case 6:
            renderStep6();
            dom.nextBtn.innerHTML = '生成标题和导语 <i class="fa fa-arrow-right ml-1"></i>';
            break;
        case 7:
            renderStep7();
            dom.nextBtn.innerHTML = '完成 <i class="fa fa-check ml-1"></i>';
            break;
    }
}

// 上一步
function goToPrevStep() {
    if (appState.currentStep > 1) {
        showStep(appState.currentStep - 1);
    }
}

// 下一步
async function goToNextStep() {
    if (appState.currentStep === appState.totalSteps) {
        // 完成创作
        completeCreation();
        return;
    }
    
    // 对于步骤1，先保存用户选择的参数
    if (appState.currentStep === 1) {
        // 保存步骤1的参数
        appState.generatedContent.step1Params = {
            platform: document.getElementById('platform').value,
            model: document.getElementById('model').value,
            storyType: document.getElementById('storyType').value,
            dilemmaType: document.getElementById('dilemmaType').value,
            publishPlatform: document.getElementById('publishPlatform').value,
            emotions: getSelectedEmotions(),
            inspiration: document.getElementById('inspiration').value
        };
        saveGeneratedContent();
    }
    
    // 根据当前步骤执行相应的生成逻辑
    switch (appState.currentStep) {
        case 1:
            await generateTopic();
            break;
        case 2:
            await generateCharacters();
            break;
        case 3:
            await generateOutline();
            break;
        case 4:
            await generateDetailedOutline();
            break;
        case 5:
            await generateContent();
            break;
        case 6:
            await generateTitleAndIntro();
            break;
    }
}

// 更新模型选择下拉框
function updateModelOptions(selectedPlatform, selectedModel) {
    const modelSelect = document.getElementById('model');
    if (!modelSelect) return;
    
    // 清空当前选项
    modelSelect.innerHTML = '';
    
    // 获取当前平台支持的模型
    const models = platformModels[selectedPlatform] || platformModels.siliconflow;
    
    // 添加新选项
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.value;
        option.textContent = model.label;
        modelSelect.appendChild(option);
    });
    
    // 如果有指定的模型值，则选中它；否则选中第一个选项
    if (selectedModel) {
        modelSelect.value = selectedModel;
    } else if (models.length > 0) {
        modelSelect.value = models[0].value;
    }
}

// 渲染步骤1：输入参数
function renderStep1() {
    // 创建步骤1的所有控件
    const container = document.createElement('div');
    container.id = 'step1';
    container.className = 'space-y-5';
    container.innerHTML = `
        <h2 class="text-xl font-bold">基本参数设置</h2>
        
        <div class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">平台选择</label>
                <select id="platform" class="w-full rounded-lg border-gray-300 shadow-sm input-focus border px-3 py-2">
                    <option value="siliconflow">硅基流动</option>
                    <option value="deepseek">Deepseek</option>
                    <option value="openai">OpenAI</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">模型选择</label>
                <select id="model" class="w-full rounded-lg border-gray-300 shadow-sm input-focus border px-3 py-2">
                    <!-- 模型选项将通过JavaScript动态添加 -->
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">故事类型</label>
                <select id="storyType" class="w-full rounded-lg border-gray-300 shadow-sm input-focus border px-3 py-2">
                    <option value="都市情感">都市情感</option>
                    <option value="悬疑推理">悬疑推理</option>
                    <option value="玄幻仙侠">玄幻仙侠</option>
                    <option value="科幻未来">科幻未来</option>
                    <option value="历史穿越">历史穿越</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">困境类型</label>
                <select id="dilemmaType" class="w-full rounded-lg border-gray-300 shadow-sm input-focus border px-3 py-2">
                    <option value="生存困境">生存困境</option>
                    <option value="情感纠葛">情感纠葛</option>
                    <option value="道德抉择">道德抉择</option>
                    <option value="理想与现实">理想与现实</option>
                    <option value="身份认同">身份认同</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">投稿平台</label>
                <select id="publishPlatform" class="w-full rounded-lg border-gray-300 shadow-sm input-focus border px-3 py-2">
                    <option value="起点中文网">起点中文网</option>
                    <option value="番茄小说">番茄小说</option>
                    <option value="知乎故事">知乎故事</option>
                    <option value="小红书">小红书</option>
                    <option value="抖音">抖音</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">情绪类型</label>
                <div class="flex flex-wrap gap-2">
                    <label class="inline-flex items-center">
                        <input type="checkbox" id="emotion1" value="爽文" checked class="rounded text-primary focus:ring-primary">
                        <span class="ml-1 text-sm">爽文</span>
                    </label>
                    <label class="inline-flex items-center">
                        <input type="checkbox" id="emotion2" value="虐心" class="rounded text-primary focus:ring-primary">
                        <span class="ml-1 text-sm">虐心</span>
                    </label>
                    <label class="inline-flex items-center">
                        <input type="checkbox" id="emotion3" value="恐怖" class="rounded text-primary focus:ring-primary">
                        <span class="ml-1 text-sm">恐怖</span>
                    </label>
                    <label class="inline-flex items-center">
                        <input type="checkbox" id="emotion4" value="治愈" class="rounded text-primary focus:ring-primary">
                        <span class="ml-1 text-sm">治愈</span>
                    </label>
                    <label class="inline-flex items-center">
                        <input type="checkbox" id="emotion5" value="感动" class="rounded text-primary focus:ring-primary">
                        <span class="ml-1 text-sm">感动</span>
                    </label>
                </div>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">灵感输入（可选）</label>
                <textarea id="inspiration" rows="3" placeholder="输入你的故事灵感或关键词..." class="w-full rounded-lg border-gray-300 shadow-sm input-focus border px-3 py-2"></textarea>
            </div>
        </div>
    `;
    
    // 将容器添加到步骤内容区
    dom.stepContainer.appendChild(container);
    
    // 如果有保存的参数，恢复它们
    let selectedPlatform = appState.currentPlatform;
    let selectedModel = appState.currentModel;
    
    if (appState.generatedContent.step1Params) {
        const params = appState.generatedContent.step1Params;
        if (params.platform) selectedPlatform = params.platform;
        if (params.model) selectedModel = params.model;
        if (params.storyType) document.getElementById('storyType').value = params.storyType;
        if (params.dilemmaType) document.getElementById('dilemmaType').value = params.dilemmaType;
        if (params.publishPlatform) document.getElementById('publishPlatform').value = params.publishPlatform;
        if (params.inspiration) document.getElementById('inspiration').value = params.inspiration;
        
        // 恢复情绪类型选择
        if (params.emotions) {
            for (let i = 1; i <= 5; i++) {
                const checkbox = document.getElementById(`emotion${i}`);
                checkbox.checked = params.emotions.includes(checkbox.value);
            }
        }
    }
    
    // 设置平台选择
    const platformSelect = document.getElementById('platform');
    if (platformSelect) {
        platformSelect.value = selectedPlatform;
        
        // 初始化模型选项
        updateModelOptions(selectedPlatform, selectedModel);
        
        // 添加平台选择变化事件监听器
        platformSelect.addEventListener('change', function() {
            // 当平台改变时，更新模型选项
            updateModelOptions(this.value);
        });
    }
}

// 获取选中的情绪类型
function getSelectedEmotions() {
    const emotions = [];
    for (let i = 1; i <= 5; i++) {
        const checkbox = document.getElementById(`emotion${i}`);
        if (checkbox.checked) {
            emotions.push(checkbox.value);
        }
    }
    return emotions;
}

// 渲染步骤2：选题
function renderStep2() {
    const container = document.createElement('div');
    container.className = 'space-y-5';
    container.innerHTML = `
        <h2 class="text-xl font-bold">故事选题</h2>
        <div>
            <textarea id="topicText" rows="6" readonly class="w-full rounded-lg border-gray-300 shadow-sm bg-gray-50 border px-3 py-2"></textarea>
        </div>
        <div class="flex gap-2">
            <button id="regenerateTopicBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-refresh mr-1"></i> 重新生成
            </button>
            <button id="editTopicBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-pencil mr-1"></i> 手动编辑
            </button>
        </div>
    `;
    
    dom.stepContainer.appendChild(container);
    
    // 显示已生成的选题
    const topicText = document.getElementById('topicText');
    if (appState.generatedContent.topic) {
        topicText.value = appState.generatedContent.topic;
    }
    
    // 绑定按钮事件
    document.getElementById('regenerateTopicBtn').addEventListener('click', generateTopic);
    document.getElementById('editTopicBtn').addEventListener('click', function() {
        topicText.readOnly = !topicText.readOnly;
        if (topicText.readOnly) {
            // 保存手动编辑的内容
            appState.generatedContent.topic = topicText.value;
            saveGeneratedContent();
            this.innerHTML = '<i class="fa fa-pencil mr-1"></i> 手动编辑';
        } else {
            this.innerHTML = '<i class="fa fa-save mr-1"></i> 保存修改';
        }
    });
}

// 渲染步骤3：人物设定
function renderStep3() {
    const container = document.createElement('div');
    container.className = 'space-y-5';
    container.innerHTML = `
        <h2 class="text-xl font-bold">人物设定</h2>
        <div>
            <textarea id="charactersText" rows="10" readonly class="w-full rounded-lg border-gray-300 shadow-sm bg-gray-50 border px-3 py-2"></textarea>
        </div>
        <div class="flex gap-2">
            <button id="regenerateCharactersBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-refresh mr-1"></i> 重新生成
            </button>
            <button id="editCharactersBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-pencil mr-1"></i> 手动编辑
            </button>
        </div>
    `;
    
    dom.stepContainer.appendChild(container);
    
    // 显示已生成的人物设定
    const charactersText = document.getElementById('charactersText');
    if (appState.generatedContent.characters) {
        charactersText.value = appState.generatedContent.characters;
    }
    
    // 绑定按钮事件
    document.getElementById('regenerateCharactersBtn').addEventListener('click', generateCharacters);
    document.getElementById('editCharactersBtn').addEventListener('click', function() {
        charactersText.readOnly = !charactersText.readOnly;
        if (charactersText.readOnly) {
            // 保存手动编辑的内容
            appState.generatedContent.characters = charactersText.value;
            saveGeneratedContent();
            this.innerHTML = '<i class="fa fa-pencil mr-1"></i> 手动编辑';
        } else {
            this.innerHTML = '<i class="fa fa-save mr-1"></i> 保存修改';
        }
    });
}

// 渲染步骤4：粗纲
function renderStep4() {
    const container = document.createElement('div');
    container.className = 'space-y-5';
    container.innerHTML = `
        <h2 class="text-xl font-bold">故事粗纲</h2>
        <div>
            <textarea id="outlineText" rows="12" readonly class="w-full rounded-lg border-gray-300 shadow-sm bg-gray-50 border px-3 py-2"></textarea>
        </div>
        <div class="flex gap-2">
            <button id="regenerateOutlineBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-refresh mr-1"></i> 重新生成
            </button>
            <button id="editOutlineBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-pencil mr-1"></i> 手动编辑
            </button>
        </div>
    `;
    
    dom.stepContainer.appendChild(container);
    
    // 显示已生成的粗纲
    const outlineText = document.getElementById('outlineText');
    if (appState.generatedContent.outline) {
        outlineText.value = appState.generatedContent.outline;
    }
    
    // 绑定按钮事件
    document.getElementById('regenerateOutlineBtn').addEventListener('click', generateOutline);
    document.getElementById('editOutlineBtn').addEventListener('click', function() {
        outlineText.readOnly = !outlineText.readOnly;
        if (outlineText.readOnly) {
            // 保存手动编辑的内容
            appState.generatedContent.outline = outlineText.value;
            saveGeneratedContent();
            this.innerHTML = '<i class="fa fa-pencil mr-1"></i> 手动编辑';
        } else {
            this.innerHTML = '<i class="fa fa-save mr-1"></i> 保存修改';
        }
    });
}

// 渲染步骤5：细纲
function renderStep5() {
    const container = document.createElement('div');
    container.className = 'space-y-5';
    container.innerHTML = `
        <h2 class="text-xl font-bold">故事细纲</h2>
        <div>
            <textarea id="detailedOutlineText" rows="15" readonly class="w-full rounded-lg border-gray-300 shadow-sm bg-gray-50 border px-3 py-2"></textarea>
        </div>
        <div class="flex gap-2">
            <button id="regenerateDetailedOutlineBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-refresh mr-1"></i> 重新生成
            </button>
            <button id="editDetailedOutlineBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-pencil mr-1"></i> 手动编辑
            </button>
        </div>
    `;
    
    dom.stepContainer.appendChild(container);
    
    // 显示已生成的细纲
    const detailedOutlineText = document.getElementById('detailedOutlineText');
    if (appState.generatedContent.detailed_outline) {
        detailedOutlineText.value = appState.generatedContent.detailed_outline;
    }
    
    // 绑定按钮事件
    document.getElementById('regenerateDetailedOutlineBtn').addEventListener('click', generateDetailedOutline);
    document.getElementById('editDetailedOutlineBtn').addEventListener('click', function() {
        detailedOutlineText.readOnly = !detailedOutlineText.readOnly;
        if (detailedOutlineText.readOnly) {
            // 保存手动编辑的内容
            appState.generatedContent.detailed_outline = detailedOutlineText.value;
            saveGeneratedContent();
            this.innerHTML = '<i class="fa fa-pencil mr-1"></i> 手动编辑';
        } else {
            this.innerHTML = '<i class="fa fa-save mr-1"></i> 保存修改';
        }
    });
}

// 渲染步骤6：正文
function renderStep6() {
    const container = document.createElement('div');
    container.className = 'space-y-5';
    container.innerHTML = `
        <h2 class="text-xl font-bold">故事正文</h2>
        <div>
            <textarea id="contentText" rows="20" readonly class="w-full rounded-lg border-gray-300 shadow-sm bg-gray-50 border px-3 py-2"></textarea>
        </div>
        <div class="flex gap-2">
            <button id="regenerateContentBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-refresh mr-1"></i> 重新生成
            </button>
            <button id="editContentBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-pencil mr-1"></i> 手动编辑
            </button>
            <button id="copyContentBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-copy mr-1"></i> 复制全文
            </button>
        </div>
    `;
    
    dom.stepContainer.appendChild(container);
    
    // 显示已生成的正文
    const contentText = document.getElementById('contentText');
    if (appState.generatedContent.content) {
        contentText.value = appState.generatedContent.content;
    }
    
    // 绑定按钮事件
    document.getElementById('regenerateContentBtn').addEventListener('click', generateContent);
    document.getElementById('editContentBtn').addEventListener('click', function() {
        contentText.readOnly = !contentText.readOnly;
        if (contentText.readOnly) {
            // 保存手动编辑的内容
            appState.generatedContent.content = contentText.value;
            saveGeneratedContent();
            this.innerHTML = '<i class="fa fa-pencil mr-1"></i> 手动编辑';
        } else {
            this.innerHTML = '<i class="fa fa-save mr-1"></i> 保存修改';
        }
    });
    document.getElementById('copyContentBtn').addEventListener('click', function() {
        if (appState.generatedContent.content) {
            navigator.clipboard.writeText(appState.generatedContent.content).then(() => {
                showToast('内容已复制到剪贴板');
            });
        }
    });
}

// 渲染步骤7：标题和导语
function renderStep7() {
    const container = document.createElement('div');
    container.className = 'space-y-5';
    container.innerHTML = `
        <h2 class="text-xl font-bold">标题和导语</h2>
        
        <div class="space-y-3">
            <label class="block text-sm font-medium text-gray-700">故事标题</label>
            <textarea id="titleText" rows="2" readonly class="w-full rounded-lg border-gray-300 shadow-sm bg-gray-50 border px-3 py-2"></textarea>
        </div>
        
        <div class="space-y-3">
            <label class="block text-sm font-medium text-gray-700">故事导语</label>
            <textarea id="introText" rows="6" readonly class="w-full rounded-lg border-gray-300 shadow-sm bg-gray-50 border px-3 py-2"></textarea>
        </div>
        
        <div class="flex gap-2">
            <button id="regenerateTitleIntroBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-refresh mr-1"></i> 重新生成
            </button>
            <button id="editTitleIntroBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-pencil mr-1"></i> 手动编辑
            </button>
            <button id="copyAllBtn" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50">
                <i class="fa fa-copy mr-1"></i> 复制全部
            </button>
        </div>
    `;
    
    dom.stepContainer.appendChild(container);
    
    // 显示已生成的标题和导语
    const titleText = document.getElementById('titleText');
    const introText = document.getElementById('introText');
    if (appState.generatedContent.title) {
        titleText.value = appState.generatedContent.title;
    }
    if (appState.generatedContent.intro) {
        introText.value = appState.generatedContent.intro;
    }
    
    // 绑定按钮事件
    document.getElementById('regenerateTitleIntroBtn').addEventListener('click', generateTitleAndIntro);
    document.getElementById('editTitleIntroBtn').addEventListener('click', function() {
        const isReadOnly = titleText.readOnly;
        titleText.readOnly = !isReadOnly;
        introText.readOnly = !isReadOnly;
        if (isReadOnly) {
            // 保存手动编辑的内容
            appState.generatedContent.title = titleText.value;
            appState.generatedContent.intro = introText.value;
            saveGeneratedContent();
            this.innerHTML = '<i class="fa fa-pencil mr-1"></i> 手动编辑';
        } else {
            this.innerHTML = '<i class="fa fa-save mr-1"></i> 保存修改';
        }
    });
    document.getElementById('copyAllBtn').addEventListener('click', function() {
        let allContent = '';
        if (appState.generatedContent.title) {
            allContent += `【标题】${appState.generatedContent.title}\n\n`;
        }
        if (appState.generatedContent.intro) {
            allContent += `【导语】${appState.generatedContent.intro}\n\n`;
        }
        if (appState.generatedContent.content) {
            allContent += `【正文】${appState.generatedContent.content}`;
        }
        if (allContent) {
            navigator.clipboard.writeText(allContent).then(() => {
                showToast('全部内容已复制到剪贴板');
            });
        }
    });
}

// 生成选题
async function generateTopic() {
    showLoading('正在生成选题...');
    
    try {
        const params = appState.generatedContent.step1Params;
        const result = await api.generateTopic(params);
        appState.generatedContent.topic = result;
        saveGeneratedContent();
        
        hideLoading();
        showStep(2);
    } catch (error) {
        console.error('生成选题失败:', error);
        hideLoading();
        showToast('生成选题失败: ' + error.message, 'error');
    }
}

// 生成人物设定
async function generateCharacters() {
    showLoading('正在生成人物设定...');
    
    try {
        const params = {
            topic: appState.generatedContent.topic,
            storyType: appState.generatedContent.step1Params.storyType
        };
        const result = await generateCharactersFromAPI(params);
        appState.generatedContent.characters = result;
        saveGeneratedContent();
        
        hideLoading();
        showStep(3);
    } catch (error) {
        console.error('生成人物设定失败:', error);
        hideLoading();
        showToast('生成人物设定失败: ' + error.message, 'error');
    }
}

// 生成粗纲
async function generateOutline() {
    showLoading('正在生成故事粗纲...');
    
    try {
        const params = {
            topic: appState.generatedContent.topic,
            characters: appState.generatedContent.characters,
            storyType: appState.generatedContent.step1Params.storyType
        };
        const result = await api.generateOutline(params);
        appState.generatedContent.outline = result;
        saveGeneratedContent();
        
        hideLoading();
        showStep(4);
    } catch (error) {
        console.error('生成故事粗纲失败:', error);
        hideLoading();
        showToast('生成故事粗纲失败: ' + error.message, 'error');
    }
}

// 生成细纲
async function generateDetailedOutline() {
    showLoading('正在生成故事细纲...');
    
    try {
        const params = {
            topic: appState.generatedContent.topic,
            outline: appState.generatedContent.outline,
            characters: appState.generatedContent.characters,
            storyType: appState.generatedContent.step1Params.storyType
        };
        const result = await generateDetailedOutlineFromAPI(params);
        appState.generatedContent.detailed_outline = result;
        saveGeneratedContent();
        
        hideLoading();
        showStep(5);
    } catch (error) {
        console.error('生成故事细纲失败:', error);
        hideLoading();
        showToast('生成故事细纲失败: ' + error.message, 'error');
    }
}

// 生成正文
async function generateContent() {
    showLoading('正在生成故事正文...');
    
    try {
        const params = {
            topic: appState.generatedContent.topic,
            characters: appState.generatedContent.characters,
            selectedDetailedOutline: appState.generatedContent.detailed_outline,
            min_size: 3000
        };
        const result = await api.generateContent(params);
        appState.generatedContent.content = result;
        saveGeneratedContent();
        
        hideLoading();
        showStep(6);
    } catch (error) {
        console.error('生成故事正文失败:', error);
        hideLoading();
        showToast('生成故事正文失败: ' + error.message, 'error');
    }
}

// 生成标题和导语
async function generateTitleAndIntro() {
    showLoading('正在生成标题和导语...');
    
    try {
        const topic = appState.generatedContent.topic;
        const content = appState.generatedContent.content;
        
        // 并行生成标题和导语
        const [titleResult, introResult] = await Promise.all([
            api.generateTitle({ content }),
            api.generateIntro({ topic, characters: appState.generatedContent.characters, content })
        ]);
        
        appState.generatedContent.title = titleResult;
        appState.generatedContent.intro = introResult;
        saveGeneratedContent();
        
        hideLoading();
        showStep(7);
    } catch (error) {
        console.error('生成标题和导语失败:', error);
        hideLoading();
        showToast('生成标题和导语失败: ' + error.message, 'error');
    }
}

// 完成创作
function completeCreation() {
    showToast('恭喜！您的故事创作已完成！');
    // 可以在这里添加分享功能或其他后续操作
}

// 加载配置
function loadConfig() {
    const savedConfig = localStorage.getItem('sscConfig');
    if (savedConfig) {
        try {
            appState.config = JSON.parse(savedConfig);
            // 更新配置模态框中的值
            dom.deepseekApiKey.value = appState.config.deepseek_api_key || '';
            dom.siliconflowApiKey.value = appState.config.siliconflow_api_key || '';
            dom.openaiApiKey.value = appState.config.api_key || '';
        } catch (e) {
            console.error('加载配置失败:', e);
        }
    }
}

// 保存配置
function saveConfig() {
    appState.config.deepseek_api_key = dom.deepseekApiKey.value;
    appState.config.siliconflow_api_key = dom.siliconflowApiKey.value;
    appState.config.api_key = dom.openaiApiKey.value;
    
    try {
        localStorage.setItem('sscConfig', JSON.stringify(appState.config));
        showToast('配置已保存');
        closeConfigModal();
    } catch (e) {
        console.error('保存配置失败:', e);
        showToast('保存配置失败，请稍后再试', 'error');
    }
}

// 平台与模型映射关系
export const platformModels = {
    siliconflow: [
        { value: '[16]千问', label: '千问' },
        { value: '[4]千问长文', label: '千问长文' },
        { value: '[4]腾讯混元', label: '腾讯混元' }
    ],
    deepseek: [
        { value: 'deepseek-chat', label: 'DeepSeek-R1' },
        { value: 'deepseek-code', label: 'DeepSeek-Coder' }
    ],
    openai: [
        { value: 'gpt-4o', label: 'GPT-4o' },
        { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
    ]
};

// 加载平台模型配置
function loadPlatformModelConfigs() {
    const savedConfigs = localStorage.getItem('sscPlatformModelConfigs');
    if (savedConfigs) {
        try {
            appState.platformModelConfigs = JSON.parse(savedConfigs);
        } catch (e) {
            console.error('加载平台模型配置失败:', e);
        }
    }
    
    // 如果没有配置，使用默认配置
    if (Object.keys(appState.platformModelConfigs).length === 0) {
        for (let step = 1; step <= 7; step++) {
            appState.platformModelConfigs[`step${step}`] = {
                platform: appState.currentPlatform,
                model: appState.currentModel
            };
        }
    }
}

// 保存平台模型配置
function savePlatformModelConfigs() {
    try {
        localStorage.setItem('sscPlatformModelConfigs', JSON.stringify(appState.platformModelConfigs));
    } catch (e) {
        console.error('保存平台模型配置失败:', e);
    }
}

// 加载提示词
async function loadPrompts() {
    try {
        // 使用全局window.loadPrompts函数加载提示词
        if (window.loadPrompts) {
            const prompts = await window.loadPrompts();
            appState.prompts = prompts;
        } else {
            // 如果window.loadPrompts不可用，使用备用的模拟数据
            throw new Error('window.loadPrompts函数不可用');
        }
    } catch (error) {
        console.error('加载提示词失败:', error);
        // 使用备用的模拟数据
        appState.prompts = {
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

// 保存生成的内容
function saveGeneratedContent() {
    try {
        localStorage.setItem('sscGeneratedContent', JSON.stringify(appState.generatedContent));
    } catch (e) {
        console.error('保存生成内容失败:', e);
    }
}

// 加载生成的内容
function loadGeneratedContent() {
    const savedContent = localStorage.getItem('sscGeneratedContent');
    if (savedContent) {
        try {
            appState.generatedContent = JSON.parse(savedContent);
        } catch (e) {
            console.error('加载生成内容失败:', e);
        }
    }
}

// 打开配置模态框
function openConfigModal() {
    dom.configModal.classList.remove('hidden');
}

// 关闭配置模态框
function closeConfigModal() {
    dom.configModal.classList.add('hidden');
}

// 显示加载动画
function showLoading(text = '正在处理，请稍候...') {
    dom.loadingText.textContent = text;
    dom.loadingModal.classList.remove('hidden');
}

// 隐藏加载动画
function hideLoading() {
    dom.loadingModal.classList.add('hidden');
}

// 显示提示消息
function showToast(message, type = 'success') {
    // 创建提示元素
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-lg text-white ${type === 'success' ? 'bg-green-500' : 'bg-red-500'} shadow-lg z-50`;
    toast.textContent = message;
    
    // 添加到页面
    document.body.appendChild(toast);
    
    // 3秒后移除
    setTimeout(() => {
        toast.classList.add('opacity-0', 'transition-opacity', 'duration-300');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// 调用API的通用方法
async function callOpenaiApi(prompt, maxTokens = 8000, updateUi = false, conversationHistory = null, step = null) {
    try {
        // 如果没有指定步骤，使用当前步骤
        if (step === null) {
            step = appState.currentStep;
        }
        
        // 获取当前步骤的平台和模型配置
        const stepConfig = appState.platformModelConfigs[`step${step}`] || {};
        const platform = stepConfig.platform || appState.currentPlatform;
        const model = stepConfig.model || appState.currentModel;
        
        console.log(`调用API，平台: ${platform}, 模型: ${model}, 提示词长度: ${prompt.length}, max_tokens: ${maxTokens}`);
        
        // 构造消息列表
        let messages;
        if (conversationHistory) {
            messages = [...conversationHistory];
            messages.push({role: 'user', content: prompt});
        } else {
            messages = [{role: 'user', content: prompt}];
        }
        
        // 这里应该根据不同的平台调用不同的API
        // 由于是前端实现，这里只是模拟API调用
        // 在实际项目中，应该通过后端API代理调用OpenAI、硅基流动、Deepseek等服务
        
        // 模拟API调用延迟
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 返回模拟数据
        return "这是模拟的API返回内容。在实际项目中，这里应该返回真实的API调用结果。";
    } catch (error) {
        console.error('API调用失败:', error);
        throw error;
    }
}

// 初始化应用
(async () => {
    await init();
})();