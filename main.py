import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import datetime
import time
from openai import OpenAI
from http import HTTPStatus
import json
import threading

TIME_SLEEP = 20
CONTENT_SIZE_MIN = 1000
# 读取配置文件
def load_config():
    config = {}
    config_path = 'config.json'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"已从{config_path}加载配置")
    except FileNotFoundError:
        # 如果配置文件不存在，创建默认配置
        print(f"配置文件{config_path}不存在，将使用默认配置")
        config = {
            "api_key": "",
            "base_url": "",
            "siliconflow_api_key": "",
            "deepseek_api_key": ""
        }
        # 尝试保存默认配置
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"已创建默认配置文件{config_path}")
        except PermissionError:
            print(f"无法在当前目录创建配置文件，程序将使用内存中的默认配置")
        except Exception as e:
            print(f"创建默认配置文件失败: {e}")
    except PermissionError:
        # 如果没有读取权限，尝试从用户目录读取或使用默认配置
        print(f"没有权限读取配置文件{config_path}")
        user_dir = os.path.expanduser('~')
        alt_config_path = os.path.join(user_dir, 'ssc_config.json')
        if os.path.exists(alt_config_path):
            try:
                with open(alt_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"已从用户目录配置文件{alt_config_path}加载配置")
            except Exception as e:
                print(f"从用户目录读取配置失败: {e}")
                config = {"api_key": "", "base_url": "", "siliconflow_api_key": "", "deepseek_api_key": ""}
        else:
            print("用户目录也没有配置文件，将使用默认配置")
            config = {"api_key": "", "base_url": "", "siliconflow_api_key": "", "deepseek_api_key": ""}
    except Exception as e:
        print(f"读取配置文件时发生错误: {e}")
        config = {"api_key": "", "base_url": "", "siliconflow_api_key": "", "deepseek_api_key": ""}
    
    return config

# 加载配置
config = load_config()

# 初始化OpenAI客户端
def init_openai_client(api_key, base_url):
    return OpenAI(
        api_key=api_key,
        base_url=base_url
    )

# 初始化硅基流动API客户端
def init_siliconflow_client(api_key):
    return OpenAI(
        api_key=api_key,
        base_url="https://api.siliconflow.cn/v1"
    )

# 初始化Deepseek API客户端
def init_deepseek_client(api_key):
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1"
    )

# 初始化客户端
def init_client(platform, api_key, base_url=None):
    if platform == "siliconflow":
        return init_siliconflow_client(api_key)
    elif platform == "deepseek":
        return init_deepseek_client(api_key)
    else:
        # 默认使用deepseek作为后备选项
        return init_deepseek_client(api_key)

# 模型显示名称到实际ID的映射
model_display_names = {
    "[10]千问": "Qwen/Qwen3-235B-A22B",
    "[4]千问长文": "Tongyi-Zhiwen/QwenLong-L1-32B",
    "[14]智普清言": "zai-org/GLM-4.5",
    "[12]ProDeepseekV3.1": "Pro/deepseek-ai/DeepSeek-V3.1",
    "[8]DeepseekR1": "deepseek-ai/DeepSeek-R1",
    "[免费]DSR1+Qwen3": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
    "[8]百度": "baidu/ERNIE-4.5-300B-A47B",
    "[4]腾讯混元": "tencent/Hunyuan-A13B-Instruct"
}

# 获取平台支持的模型（返回显示名称）
def get_platform_models(platform):
    if platform == "siliconflow":
        return ["[10]千问", "[4]千问长文", "[14]智普清言", "[12]ProDeepseekV3.1", "[8]DeepseekR1", "[8]百度","[4]腾讯混元","[免费]DSR1+Qwen3"]
    elif platform == "deepseek":
        return ["deepseek-chat", "deepseek-llm-7b-chat", "deepseek-coder"]
    else:
        return ["deepseek-chat"]

# 获取实际的模型ID
def get_actual_model_id(display_name):
    return model_display_names.get(display_name, display_name)

# 全局客户端和模型配置
clients = {}
platform_model_configs = {}
current_platform = "deepseek"
current_model = "deepseek-chat"

# 保存平台模型配置到文件
def save_platform_model_configs():
    try:
        # 首先尝试在当前目录保存
        config_path = 'config.json'
        config_data = {}
        
        # 如果文件存在且可读取，则读取现有配置
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception as read_error:
                print(f"读取现有配置失败: {read_error}，将创建新配置")
                config_data = {}
        
        # 添加或更新平台模型配置
        config_data['platform_model_configs'] = platform_model_configs
        
        # 尝试保存配置到文件
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            print(f"平台模型配置已保存到{config_path}")
        except PermissionError:
            # 如果当前目录没有写入权限，尝试保存到用户目录
            import getpass
            import tempfile
            user_dir = os.path.expanduser('~')
            alt_config_path = os.path.join(user_dir, 'ssc_config.json')
            try:
                with open(alt_config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                print(f"当前目录没有写入权限，配置已保存到用户目录: {alt_config_path}")
            except Exception as alt_error:
                print(f"在用户目录保存配置也失败: {alt_error}")
        except Exception as e:
            print(f"保存平台模型配置失败: {e}")
    except Exception as e:
        print(f"保存平台模型配置过程中发生错误: {e}")

# 从文件加载平台模型配置
def load_platform_model_configs():
    global platform_model_configs
    try:
        import os
        # 首先尝试从当前目录加载配置
        config_path = 'config.json'
        config_loaded = False
        
        # 如果当前目录有配置文件，尝试加载
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    if 'platform_model_configs' in config_data:
                        platform_model_configs = config_data['platform_model_configs']
                        print(f"已从{config_path}加载平台模型配置")
                        config_loaded = True
            except Exception as e:
                print(f"从当前目录加载配置失败: {e}")
        
        # 如果当前目录没有配置文件或加载失败，尝试从用户目录加载
        if not config_loaded:
            user_dir = os.path.expanduser('~')
            alt_config_path = os.path.join(user_dir, 'ssc_config.json')
            if os.path.exists(alt_config_path):
                try:
                    with open(alt_config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        if 'platform_model_configs' in config_data:
                            platform_model_configs = config_data['platform_model_configs']
                            print(f"已从用户目录配置文件{alt_config_path}加载平台模型配置")
                            config_loaded = True
                except Exception as e:
                    print(f"从用户目录加载配置失败: {e}")
        
        # 如果两个位置都没有配置文件，使用默认配置
        if not config_loaded:
            print("未找到配置文件，将使用默认配置")
            # 设置默认配置
            for step in range(1, 8):
                platform_model_configs[f"step{step}"] = {
                    "platform": current_platform,
                    "model": current_model
                }
    except Exception as e:
        print(f"加载平台模型配置过程中发生错误: {e}")

# 加载保存的平台模型配置
load_platform_model_configs()

# 初始化默认客户端
# 根据当前平台类型选择正确的API密钥
if current_platform == "siliconflow":
    api_key = config.get("siliconflow_api_key", config["api_key"])
elif current_platform == "deepseek":
    api_key = config.get("deepseek_api_key", config["api_key"])
else:
    api_key = config["api_key"]
clients[current_platform] = init_client(current_platform, api_key)

# 只在配置为空时初始化默认值（确保已经加载的配置不会被覆盖）
if not platform_model_configs:
    for step in range(1, 8):
        platform_model_configs[f"step{step}"] = {
            "platform": current_platform,
            "model": current_model
        }

# 读取提示词配置文件
def load_prompts(story_type=None):
    prompts = {}
    prompt_files = [
        "topic.prompt",
        "outline.prompt",
        "detailed_outline_first.prompt",
        "detailed_outline_subsequent.prompt",
        "content_first.prompt",
        "content_subsequent.prompt",
        "content_last.prompt",  # 添加最后的提示词文件
        "title.prompt",
        "intro.prompt",
        "protagonist.prompt",
        "antagonist.prompt",
        "supporting.prompt"
    ]
    
    # 确定提示词目录
    prompt_dir = "prompts"
    if story_type and os.path.exists(f"prompts/{story_type}"):
        prompt_dir = f"prompts/{story_type}"
        print(f"使用{story_type}类型的提示词，目录: {prompt_dir}")
    else:
        print(f"使用默认提示词，目录: {prompt_dir}")
    
    for file in prompt_files:
        file_path = os.path.join(prompt_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 使用文件名（不含扩展名）作为键
                key = file.split('.')[0]
                prompts[key] = f.read()
        except FileNotFoundError:
            # 如果特定类型的提示词文件不存在，尝试使用默认目录下的文件
            default_file_path = os.path.join("prompts", file)
            if os.path.exists(default_file_path):
                with open(default_file_path, 'r', encoding='utf-8') as f:
                    key = file.split('.')[0]
                    prompts[key] = f.read()
                print(f"{story_type}类型缺少{file}，使用默认提示词")
            else:
                # 如果默认文件也不存在，设置空字符串
                prompts[key] = ""
                print(f"警告：无法找到提示词文件 {file}")
    
    return prompts

# 初始加载默认提示词
prompts = load_prompts()


class StoryGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文学创作辅助V3.0")
        self.root.geometry("1000x700")
        
        # 创建存储目录
        self.story_dir = ""
        # 确保存储统一目录存在
        self.stories_base_dir = "stories"
        os.makedirs(self.stories_base_dir, exist_ok=True)
        
        # 当前创作步骤
        self.current_step = 0
        
        # 存储用户输入和生成内容
        self.user_inputs = {}
        self.generated_content = {}
        
        # 平台和模型选择相关变量
        self.platform_vars = {}
        self.model_vars = {}
        
        # 中断和恢复相关状态
        self.is_interrupted = False
        self.current_generation_state = {}
        
        # 创建界面
        self.create_widgets()
        
    def add_context_menu(self, text_widget):
        """为文本输入框添加右键菜单（复制、粘贴）和确保撤销功能正常"""
        # 创建右键菜单
        context_menu = tk.Menu(text_widget, tearoff=0)
        context_menu.add_command(label="复制", command=lambda: text_widget.event_generate('<<Copy>>'))
        context_menu.add_command(label="粘贴", command=lambda: text_widget.event_generate('<<Paste>>'))
        context_menu.add_command(label="剪切", command=lambda: text_widget.event_generate('<<Cut>>'))
        context_menu.add_separator()
        context_menu.add_command(label="全选", command=lambda: text_widget.tag_add('sel', '1.0', 'end'))
        
        # 绑定右键菜单到文本框
        def show_menu(event):
            context_menu.post(event.x_root, event.y_root)
        
        text_widget.bind("<Button-3>", show_menu)
        
        # 确保撤销功能正常（Tkinter默认支持Ctrl+Z）
        # 如果需要额外配置撤销堆栈大小，可以取消下面的注释
        # text_widget.config(undo=True)
        
    def create_widgets(self):
        # 标题
        title_label = tk.Label(self.root, text="文学创作辅助工具V3.0", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # 创建 Notebook 控件用于分步显示
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 平台和模型选择变量
        self.platform_vars = {}
        self.model_vars = {}
        
        # 第一步：输入参数
        self.step1_frame = tk.Frame(self.notebook)
        self.notebook.add(self.step1_frame, text="1. 输入参数")
        self.create_step1_widgets()
        
        # 第二步：选题
        self.step2_frame = tk.Frame(self.notebook)
        self.notebook.add(self.step2_frame, text="2. 选题")
        self.create_step2_widgets()
        
        # 第三步：人设
        self.step3_frame = tk.Frame(self.notebook)
        self.notebook.add(self.step3_frame, text="3. 人设")
        self.create_step3_widgets()
        
        # 第四步：粗纲
        self.step4_frame = tk.Frame(self.notebook)
        self.notebook.add(self.step4_frame, text="4. 粗纲")
        self.create_step4_widgets()
        
        # 第五步：细纲
        self.step5_frame = tk.Frame(self.notebook)
        self.notebook.add(self.step5_frame, text="5. 细纲")
        self.create_step5_widgets()
        
        # 第六步：正文
        self.step6_frame = tk.Frame(self.notebook)
        self.notebook.add(self.step6_frame, text="6. 正文")
        self.create_step6_widgets()
        
        # 第七步：标题和导语
        self.step7_frame = tk.Frame(self.notebook)
        self.notebook.add(self.step7_frame, text="7. 标题和导语")
        self.create_step7_widgets()
        
    def create_platform_model_selector(self, parent, step):
        """
        在指定的父窗口中创建平台和模型选择控件
        
        Args:
            parent: 父窗口控件
            step: 当前步骤编号
        """
        # 创建平台和模型选择框架
        api_frame = tk.Frame(parent)
        api_frame.pack(pady=5, padx=20, fill="x")
        
        # 平台选择
        platform_label = tk.Label(api_frame, text="AI平台:")
        platform_label.pack(side="left")
        
        self.platform_vars[step] = tk.StringVar()
        platforms = ["siliconflow", "deepseek"]
        platform_combo = ttk.Combobox(api_frame, textvariable=self.platform_vars[step], 
                                     values=platforms, width=10)
        platform_combo.pack(side="left", padx=(10, 0))
        
        # 设置默认平台
        default_platform = platform_model_configs.get(f"step{step}", {}).get("platform", current_platform)
        self.platform_vars[step].set(default_platform)
        
        # 模型选择
        model_label = tk.Label(api_frame, text="模型:")
        model_label.pack(side="left", padx=(10, 0))
        
        self.model_vars[step] = tk.StringVar()
        model_combo = ttk.Combobox(api_frame, textvariable=self.model_vars[step], width=20)
        model_combo.pack(side="left", padx=(10, 0))
        
        # 更新模型列表的函数
        def update_models(*args):
            selected_platform = self.platform_vars[step].get()
            models = get_platform_models(selected_platform)
            model_combo['values'] = models
            # 设置默认模型
            default_model = platform_model_configs.get(f"step{step}", {}).get("model", current_model)
            if default_model in models:
                self.model_vars[step].set(default_model)
            else:
                self.model_vars[step].set(models[0] if models else "")
            # 保存配置到内存
            platform_model_configs[f"step{step}"] = {
                "platform": selected_platform,
                "model": self.model_vars[step].get()
            }
            # 保存配置到文件
            save_platform_model_configs()
        
        # 保存模型选择的函数
        def save_model_selection(*args):
            # 保存配置到内存
            platform_model_configs[f"step{step}"] = {
                "platform": self.platform_vars[step].get(),
                "model": self.model_vars[step].get()
            }
            # 保存配置到文件
            save_platform_model_configs()
        
        # 绑定事件
        self.platform_vars[step].trace("w", update_models)
        self.model_vars[step].trace("w", save_model_selection)
        
        # 初始化模型列表
        update_models()
        
        return api_frame
        
    def create_step1_widgets(self):
        # 移除AI平台和模型选择控件
        # self.create_platform_model_selector(self.step1_frame, 1)
        
        # 获取已有的故事目录
        story_dirs = []
        if os.path.exists(self.stories_base_dir):
            story_dirs = [d for d in os.listdir(self.stories_base_dir) if os.path.isdir(os.path.join(self.stories_base_dir, d)) and d.startswith('story_')]
        
        # 选择之前记录
        previous_story_frame = tk.Frame(self.step1_frame)
        previous_story_frame.pack(pady=5, padx=20, fill="x")
        
        previous_story_label = tk.Label(previous_story_frame, text="选择之前记录:")
        previous_story_label.pack(side="left")
        
        self.previous_story_var = tk.StringVar()
        previous_story_combo = ttk.Combobox(previous_story_frame, textvariable=self.previous_story_var, 
                                           values=story_dirs)
        previous_story_combo.pack(side="left", padx=(10, 0))
        previous_story_combo.bind("<<ComboboxSelected>>", self.load_previous_story)
        
        # 故事类型
        story_type_frame = tk.Frame(self.step1_frame)
        story_type_frame.pack(pady=5, padx=20, fill="x")
        
        story_type_label = tk.Label(story_type_frame, text="故事类型:")
        story_type_label.pack(side="left")
        
        self.story_type_var = tk.StringVar()
        story_type_combo = ttk.Combobox(story_type_frame, textvariable=self.story_type_var, 
                                       values=["世情", "穿越", "言情","悬疑", "修仙","科幻", "奇幻", "都市", "历史", "军事", "游戏", "体育"])
        story_type_combo.pack(side="left", padx=(10, 0))
        story_type_combo.set("悬疑")
        
        # 困境类型
        dilemma_type_frame = tk.Frame(self.step1_frame)
        dilemma_type_frame.pack(pady=5, padx=20, fill="x")
        
        dilemma_type_label = tk.Label(dilemma_type_frame, text="困境类型:")
        dilemma_type_label.pack(side="left")
        
        self.dilemma_type_var = tk.StringVar()
        dilemma_type_combo = ttk.Combobox(dilemma_type_frame, textvariable=self.dilemma_type_var,
                                         values=["爱而不得", "生死危机", "恨之入骨", "一无所有 "])
        dilemma_type_combo.pack(side="left", padx=(10, 0))
        dilemma_type_combo.set("一无所有")
        
        # 投稿平台
        platform_frame = tk.Frame(self.step1_frame)
        platform_frame.pack(pady=5, padx=20, fill="x")
        
        platform_label = tk.Label(platform_frame, text="投稿平台:")
        platform_label.pack(side="left")
        
        self.platform_var = tk.StringVar()
        platform_combo = ttk.Combobox(platform_frame, textvariable=self.platform_var,
                                     values=["番茄小说", "百度小说", "起点中文网", "晋江文学城", "纵横中文网", "创世中文网", "云起书院", "红袖添香", "小说阅读网", "逐浪网"])
        platform_combo.pack(side="left", padx=(10, 0))
        platform_combo.set("番茄小说")
        
        # 情绪类型
        emotion_type_frame = tk.Frame(self.step1_frame)
        emotion_type_frame.pack(pady=5, padx=20, fill="x")
        
        emotion_type_label = tk.Label(emotion_type_frame, text="情绪类型:")
        emotion_type_label.pack(side="left")
        
        # 使用Checkbutton实现多项选择
        self.emotion_type_vars = []
        emotion_types = ["甜宠", "虐文", "爽文", "反转", "励志"]
        for i, emotion in enumerate(emotion_types):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(emotion_type_frame, text=emotion, variable=var)
            chk.pack(side="left", padx=(10, 0))
            self.emotion_type_vars.append((emotion, var))
            # 默认选中"爽文"
            if emotion == "爽文":
                var.set(True)
        
        # 灵感输入
        inspiration_frame = tk.Frame(self.step1_frame)
        inspiration_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        inspiration_label = tk.Label(inspiration_frame, text="灵感:")
        inspiration_label.pack(anchor="w")
        
        self.inspiration_text = scrolledtext.ScrolledText(inspiration_frame, height=10)
        self.inspiration_text.pack(fill="both", expand=True, pady=(5, 0))
        # 添加右键菜单和确保撤销功能
        self.add_context_menu(self.inspiration_text)
        
        # 按钮框架
        button_frame = tk.Frame(self.step1_frame)
        button_frame.pack(pady=20)
        
        self.start_generate_button = tk.Button(button_frame, text="开始生成", command=self.generate_story, bg="#4CAF50", fg="white", padx=20)
        self.start_generate_button.pack(side="left", padx=10)
        
        exit_button = tk.Button(button_frame, text="退出", command=self.root.quit, bg="#f44336", fg="white", padx=20)
        exit_button.pack(side="left", padx=10)
        
    def create_step2_widgets(self):
        # 添加平台和模型选择控件
        self.create_platform_model_selector(self.step2_frame, 2)
        
        # 选题编辑区域
        topic_frame = tk.Frame(self.step2_frame)
        topic_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        topic_label = tk.Label(topic_frame, text="选题:")
        topic_label.pack(anchor="w")
        
        self.topic_text = scrolledtext.ScrolledText(topic_frame, height=15)
        self.topic_text.pack(fill="both", expand=True, pady=(5, 0))
        # 添加右键菜单和确保撤销功能
        self.add_context_menu(self.topic_text)
        
        # 按钮框架
        button_frame = tk.Frame(self.step2_frame)
        button_frame.pack(pady=20)
        
        prev_button = tk.Button(button_frame, text="上一步", command=self.prev_step, bg="#FF9800", fg="white", padx=20)
        prev_button.pack(side="left", padx=10)
        
        self.regenerate_topic_button = tk.Button(button_frame, text="重新生成", command=self.regenerate_topic, bg="#2196F3", fg="white", padx=20)
        self.regenerate_topic_button.pack(side="left", padx=10)
        
        self.save_topic_button = tk.Button(button_frame, text="保存并继续", command=self.save_topic_and_continue, bg="#4CAF50", fg="white", padx=20)
        self.save_topic_button.pack(side="left", padx=10)
        
    def create_step3_widgets(self):
        # 添加平台和模型选择控件
        self.create_platform_model_selector(self.step3_frame, 3)
        
        # 人设编辑区域
        characters_frame = tk.Frame(self.step3_frame)
        characters_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        characters_label = tk.Label(characters_frame, text="人设:")
        characters_label.pack(anchor="w")
        
        self.characters_text = scrolledtext.ScrolledText(characters_frame, height=15)
        self.characters_text.pack(fill="both", expand=True, pady=(5, 0))
        # 添加右键菜单和确保撤销功能
        self.add_context_menu(self.characters_text)
        
        # 按钮框架
        button_frame = tk.Frame(self.step3_frame)
        button_frame.pack(pady=20)
        
        prev_button = tk.Button(button_frame, text="上一步", command=self.prev_step, bg="#FF9800", fg="white", padx=20)
        prev_button.pack(side="left", padx=10)
        
        self.regenerate_characters_button = tk.Button(button_frame, text="重新生成", command=self.regenerate_characters, bg="#2196F3", fg="white", padx=20)
        self.regenerate_characters_button.pack(side="left", padx=10)
        
        self.save_characters_button = tk.Button(button_frame, text="保存并继续", command=self.save_characters_and_continue, bg="#4CAF50", fg="white", padx=20)
        self.save_characters_button.pack(side="left", padx=10)
        
    def create_step4_widgets(self):
        # 添加平台和模型选择控件
        self.create_platform_model_selector(self.step4_frame, 4)
        
        # 粗纲编辑区域
        outline_frame = tk.Frame(self.step4_frame)
        outline_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        outline_label = tk.Label(outline_frame, text="粗纲:")
        outline_label.pack(anchor="w")
        
        self.outline_text = scrolledtext.ScrolledText(outline_frame, height=15)
        self.outline_text.pack(fill="both", expand=True, pady=(5, 0))
        # 添加右键菜单和确保撤销功能
        self.add_context_menu(self.outline_text)
        
        # 按钮框架
        button_frame = tk.Frame(self.step4_frame)
        button_frame.pack(pady=20)
        
        prev_button = tk.Button(button_frame, text="上一步", command=self.prev_step, bg="#FF9800", fg="white", padx=20)
        prev_button.pack(side="left", padx=10)
        
        self.regenerate_outline_button = tk.Button(button_frame, text="重新生成", command=self.regenerate_outline, bg="#2196F3", fg="white", padx=20)
        self.regenerate_outline_button.pack(side="left", padx=10)
        
        self.save_outline_button = tk.Button(button_frame, text="保存并继续", command=self.save_outline_and_continue, bg="#4CAF50", fg="white", padx=20)
        self.save_outline_button.pack(side="left", padx=10)
        
    def create_step5_widgets(self):
        # 添加平台和模型选择控件
        self.create_platform_model_selector(self.step5_frame, 5)
        
        # 细纲编辑区域
        detailed_outline_frame = tk.Frame(self.step5_frame)
        detailed_outline_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        detailed_outline_label = tk.Label(detailed_outline_frame, text="细纲:")
        detailed_outline_label.pack(anchor="w")
        
        self.detailed_outline_text = scrolledtext.ScrolledText(detailed_outline_frame, height=15)
        self.detailed_outline_text.pack(fill="both", expand=True, pady=(5, 0))
        # 添加右键菜单和确保撤销功能
        self.add_context_menu(self.detailed_outline_text)
        
        # 按钮框架
        button_frame = tk.Frame(self.step5_frame)
        button_frame.pack(pady=20)
        
        prev_button = tk.Button(button_frame, text="上一步", command=self.prev_step, bg="#FF9800", fg="white", padx=20)
        prev_button.pack(side="left", padx=10)
        
        self.regenerate_detailed_outline_button = tk.Button(button_frame, text="重新生成", command=self.regenerate_detailed_outline, bg="#2196F3", fg="white", padx=20)
        self.regenerate_detailed_outline_button.pack(side="left", padx=10)
        
        self.continue_detailed_outline_button = tk.Button(button_frame, text="中断后继续", command=self.continue_detailed_outline, bg="#9C27B0", fg="white", padx=20)
        self.continue_detailed_outline_button.pack(side="left", padx=10)
        # 默认禁用继续按钮，只有在中断时才启用
        self.continue_detailed_outline_button.config(state=tk.DISABLED)
        
        self.save_detailed_outline_button = tk.Button(button_frame, text="保存并继续", command=self.save_detailed_outline_and_continue, bg="#4CAF50", fg="white", padx=20)
        self.save_detailed_outline_button.pack(side="left", padx=10)
        
    def create_step6_widgets(self):
        # 添加平台和模型选择控件
        self.create_platform_model_selector(self.step6_frame, 6)
        
        # 正文编辑区域
        content_frame = tk.Frame(self.step6_frame)
        content_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        content_label = tk.Label(content_frame, text="正文:")
        content_label.pack(anchor="w")
        
        self.content_text = scrolledtext.ScrolledText(content_frame, height=15)
        self.content_text.pack(fill="both", expand=True, pady=(5, 0))
        # 添加右键菜单和确保撤销功能
        self.add_context_menu(self.content_text)
        
        # 按钮框架
        button_frame = tk.Frame(self.step6_frame)
        button_frame.pack(pady=20)
        
        prev_button = tk.Button(button_frame, text="上一步", command=self.prev_step, bg="#FF9800", fg="white", padx=20)
        prev_button.pack(side="left", padx=10)
        
        self.regenerate_content_button = tk.Button(button_frame, text="重新生成", command=self.regenerate_content, bg="#2196F3", fg="white", padx=20)
        self.regenerate_content_button.pack(side="left", padx=10)
        
        self.continue_content_button = tk.Button(button_frame, text="中断后继续", command=self.continue_content, bg="#9C27B0", fg="white", padx=20)
        self.continue_content_button.pack(side="left", padx=10)
        # 默认禁用继续按钮，只有在中断时才启用
        self.continue_content_button.config(state=tk.DISABLED)
        
        self.save_content_button = tk.Button(button_frame, text="保存并继续", command=self.save_content_and_continue, bg="#4CAF50", fg="white", padx=20)
        self.save_content_button.pack(side="left", padx=10)
        
    def create_step7_widgets(self):
        # 标题和导语编辑区域
        title_intro_frame = tk.Frame(self.step7_frame)
        title_intro_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        title_label = tk.Label(title_intro_frame, text="标题:")
        title_label.pack(anchor="w")
        
        self.title_text = scrolledtext.ScrolledText(title_intro_frame, height=3)
        self.title_text.pack(fill="both", expand=True, pady=(5, 0))
        # 添加右键菜单和确保撤销功能
        self.add_context_menu(self.title_text)
        
        intro_label = tk.Label(title_intro_frame, text="导语:")
        intro_label.pack(anchor="w", pady=(10, 0))

        self.intro_text = scrolledtext.ScrolledText(title_intro_frame, height=5)
        self.intro_text.pack(fill="both", expand=True, pady=(5, 0))
        # 添加右键菜单和确保撤销功能
        self.add_context_menu(self.intro_text)
        
        # 按钮框架
        button_frame = tk.Frame(self.step7_frame)
        button_frame.pack(pady=20)
        
        prev_button = tk.Button(button_frame, text="上一步", command=self.prev_step, bg="#FF9800", fg="white", padx=20)
        prev_button.pack(side="left", padx=10)
        
        self.regenerate_title_and_intro_button = tk.Button(button_frame, text="重新生成", command=self.regenerate_title_and_intro, bg="#2196F3", fg="white", padx=20)
        self.regenerate_title_and_intro_button.pack(side="left", padx=10)
        
        self.save_title_and_intro_and_finish_button = tk.Button(button_frame, text="保存并完成", command=self.save_title_and_intro_and_finish, bg="#4CAF50", fg="white", padx=20)
        self.save_title_and_intro_and_finish_button.pack(side="left", padx=10)
        
    def generate_story(self):
        # 在新线程中执行生成任务
        threading.Thread(target=self._async_generate_story, daemon=True).start()
        
    def _async_generate_story(self):
        # 禁用开始生成按钮
        self.start_generate_button.config(state=tk.DISABLED)
        
        # 获取用户输入
        story_type = self.story_type_var.get()
        dilemma_type = self.dilemma_type_var.get()
        platform = self.platform_var.get()
        
        # 获取多项选择的情绪类型
        selected_emotions = [emotion for emotion, var in self.emotion_type_vars if var.get()]
        emotion_type = ",".join(selected_emotions)  # 将选中的情绪类型用逗号连接
        
        inspiration = self.inspiration_text.get("1.0", tk.END).strip()
        
        # 检查输入
        if not inspiration:
            messagebox.showwarning("警告", "请输入灵感内容！")
            # 重新启用开始生成按钮
            self.start_generate_button.config(state=tk.NORMAL)
            return
        
        # 保存用户输入
        self.user_inputs = {
            "story_type": story_type,
            "dilemma_type": dilemma_type,
            "platform": platform,
            "emotion_type": emotion_type,
            "inspiration": inspiration
        }
        
        # 如果没有选择之前的故事记录，则创建新的存储目录
        if not self.story_dir or not self.story_dir.startswith("story_"):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            story_dir_name = f"story_{timestamp}"
            self.story_dir = os.path.join(self.stories_base_dir, story_dir_name)
            os.makedirs(self.story_dir, exist_ok=True)
        
        # 开始创作流程
        self.current_step = 2
        self.generate_topic()
        
        # 重新启用开始生成按钮
        self.start_generate_button.config(state=tk.NORMAL)
        
    def reload_prompts_by_story_type(self, story_type):
        """
        根据故事类型重新加载提示词
        
        Args:
            story_type: 故事类型
        """
        global prompts
        # 重新加载提示词
        prompts = load_prompts(story_type)
        print(f"已根据故事类型 '{story_type}' 重新加载提示词")
        
    def generate_topic(self):
        # 获取用户选择的故事类型
        story_type = self.story_type_var.get()
        # 根据故事类型重新加载提示词
        self.reload_prompts_by_story_type(story_type)
        # 在新线程中执行生成任务
        threading.Thread(target=self._async_generate_topic, daemon=True).start()
        
    def _async_generate_topic(self):
        # 禁用保存并继续按钮
        self.save_topic_button.config(state=tk.DISABLED)
        # 禁用重新生成按钮
        self.regenerate_topic_button.config(state=tk.DISABLED)
        
        # 获取用户输入
        story_type = self.user_inputs["story_type"]
        dilemma_type = self.user_inputs["dilemma_type"]
        platform = self.user_inputs["platform"]
        emotion_type = self.user_inputs["emotion_type"]
        inspiration = self.user_inputs["inspiration"]
        
        # 从配置文件中获取提示词模板并替换变量
        prompt_template = prompts["topic"]
        prompt = prompt_template.format(story_type=story_type, inspiration=inspiration, dilemma_type=dilemma_type, emotion_type=emotion_type)
        
        # 调用OpenAI API生成选题，增加max_tokens以确保完整输出
        topic = self._call_openai_api(prompt, 8192)
        
        # 保存生成的内容
        self.generated_content["topic"] = topic
        
        # 切换到选题页面
        self.notebook.select(self.step2_frame)
        
        # 重新启用按钮
        self.save_topic_button.config(state=tk.NORMAL)
        self.regenerate_topic_button.config(state=tk.NORMAL)
        
    def regenerate_topic(self):
        # 清空原有内容
        self.topic_text.delete(1.0, tk.END)
        # 重新生成选题
        self.generate_topic()
        
    def save_topic_and_continue(self):
        # 保存选题
        topic = self.topic_text.get("1.0", tk.END).strip()
        self.generated_content["topic"] = topic
        
        # 保存选题到文件
        story_type = self.user_inputs["story_type"]
        dilemma_type = self.user_inputs["dilemma_type"]
        platform = self.user_inputs["platform"]
        emotion_type = self.user_inputs["emotion_type"]
        inspiration = self.user_inputs["inspiration"]
        
        with open(os.path.join(self.story_dir, "topic.txt"), "w", encoding="utf-8") as f:
            f.write(f"故事类型：{story_type}\n")
            f.write(f"困境类型：{dilemma_type}\n")
            f.write(f"情绪类型：{emotion_type}\n")
            f.write(f"投稿平台：{platform}\n")
            f.write(f"灵感：{inspiration}\n")
            f.write(f"选题：{topic}\n")
        
        # 继续生成人物设定
        self.current_step = 3
        self.generate_characters()
        
    def generate_characters(self):
        # 在新线程中执行生成任务
        threading.Thread(target=self._async_generate_characters, daemon=True).start()
        
    def _async_generate_characters(self):
        # 禁用保存并继续按钮
        self.save_characters_button.config(state=tk.DISABLED)
        # 禁用重新生成按钮
        self.regenerate_characters_button.config(state=tk.DISABLED)
        
        # 获取之前步骤的内容
        topic = self.generated_content.get("topic", "未生成选题")
        
        # 动态拼接人物设定提示词，不硬编码
        platform = self.user_inputs.get("platform", "短故事平台")
        
        # 先构建基础提示词
        base_prompt = f"你是短故事专家,擅长投稿到{platform},协助进行人物设定\n\n"
        
        # 从prompts字典获取各个角色的提示词
        protagonist_prompt = prompts.get("protagonist", "").format(topic=topic)
        antagonist_prompt = prompts.get("antagonist", "")
        supporting_prompt = prompts.get("supporting", "")
        
        # 构建连续上下文的提示词
        characters_prompt = base_prompt + protagonist_prompt + "\n\n" + antagonist_prompt + "\n\n" + supporting_prompt
        
        # 确保生成的人物设定有内在联系
        characters_prompt += "\n\n请在一个连续的上下文中生成这三个人物设定，确保他们之间有内在的联系和化学反应。"
        
        # 调用OpenAI API生成人物设定
        characters_content = self._call_openai_api(characters_prompt, 8192)
        
        # 保存生成的内容
        self.generated_content["characters"] = characters_content
        
        # 切换到人物设定页面
        self.notebook.select(self.step3_frame)
        
        # 重新启用按钮
        self.save_characters_button.config(state=tk.NORMAL)
        self.regenerate_characters_button.config(state=tk.NORMAL)
        
    def regenerate_characters(self):
        # 清空原有内容
        self.characters_text.delete(1.0, tk.END)
        # 重新生成人物设定
        self.generate_characters()
        
    def save_characters_and_continue(self):
        # 保存人物设定
        characters = self.characters_text.get("1.0", tk.END).strip()
        self.generated_content["characters"] = characters
        
        # 保存人物设定到文件
        with open(os.path.join(self.story_dir, "characters.txt"), "w", encoding="utf-8") as f:
            f.write(characters)
        
        # 继续生成粗纲
        self.current_step = 4
        self.generate_outline()
        
    def generate_outline(self):
        # 在新线程中执行生成任务
        threading.Thread(target=self._async_generate_outline, daemon=True).start()
        
    def _async_generate_outline(self):
        # 禁用保存并继续按钮
        self.save_outline_button.config(state=tk.DISABLED)
        # 禁用重新生成按钮
        self.regenerate_outline_button.config(state=tk.DISABLED)
        
        # 获取之前步骤的内容
        topic = self.generated_content.get("topic", "未生成选题")
        characters = self.generated_content.get("characters", "未生成人物设定")
        
        # 从配置文件中获取提示词模板并替换变量
        prompt_template = prompts["outline"]
        prompt = prompt_template.format(topic=topic, characters=characters)
        
        # 调用OpenAI API生成粗纲
        outline = self._call_openai_api(prompt, 8192)
        
        # 保存生成的内容
        self.generated_content["outline"] = outline
        
        # 在UI中显示粗纲
        self.outline_text.delete("1.0", tk.END)
        self.outline_text.insert("1.0", outline)
        
        # 切换到粗纲页面
        self.notebook.select(self.step4_frame)
        
        # 重新启用按钮
        self.save_outline_button.config(state=tk.NORMAL)
        self.regenerate_outline_button.config(state=tk.NORMAL)
        
    def regenerate_outline(self):
        # 清空原有内容
        self.outline_text.delete(1.0, tk.END)
        # 重新生成粗纲
        self.generate_outline()
        
    def save_outline_and_continue(self):
        # 保存粗纲
        outline = self.outline_text.get("1.0", tk.END).strip()
        self.generated_content["outline"] = outline
        
        # 保存粗纲到文件
        with open(os.path.join(self.story_dir, "outline.txt"), "w", encoding="utf-8") as f:
            f.write(outline)
        
        # 继续生成细纲
        self.current_step = 5
        self.generate_detailed_outline()
        
    def generate_detailed_outline(self):
        # 在新线程中执行生成任务
        threading.Thread(target=self._async_generate_detailed_outline, daemon=True).start()
        
    def _async_generate_detailed_outline(self):
        # 禁用保存并继续按钮
        self.save_detailed_outline_button.config(state=tk.DISABLED)
        # 禁用重新生成按钮
        self.regenerate_detailed_outline_button.config(state=tk.DISABLED)
        
        # 获取之前步骤的内容
        topic = self.generated_content.get("topic", "未生成选题")
        characters = self.generated_content.get("characters", "未生成人物设定")
        outline = self.generated_content.get("outline", "未生成粗纲")
        
        # 解析粗纲为数组（支持JSON数组格式和指定格式）
        try:
            outline_lines = json.loads(outline)
            if not isinstance(outline_lines, list):
                # 如果不是数组，按行分割
                outline_lines = [line.strip() for line in outline.split('\n') if line.strip()]
        except (json.JSONDecodeError, ValueError):
            # 尝试按指定格式解析
            if outline.strip().startswith('[') and outline.strip().endswith(']'):
                # 尝试解析为JSON数组
                try:
                    # 移除首尾的方括号
                    content = outline.strip()[1:-1]
                    # 分割数组元素
                    parts = []
                    current_part = ""
                    in_string = False
                    bracket_count = 0
                    
                    for char in content:
                        if char == '"' and (not current_part or current_part[-1] != '\\'):
                            in_string = not in_string
                            current_part += char
                        elif char == '[' and not in_string:
                            bracket_count += 1
                            current_part += char
                        elif char == ']' and not in_string:
                            bracket_count -= 1
                            current_part += char
                        elif char == ',' and not in_string and bracket_count == 0:
                            parts.append(current_part.strip())
                            current_part = ""
                        else:
                            current_part += char
                    
                    if current_part.strip():
                        parts.append(current_part.strip())
                    
                    # 处理每个部分，移除引号
                    outline_lines = []
                    for part in parts:
                        if part.startswith('"') and part.endswith('"'):
                            outline_lines.append(part[1:-1])
                        else:
                            outline_lines.append(part)
                except:
                    # 如果解析失败，按行分割
                    outline_lines = [line.strip() for line in outline.split('\n') if line.strip()]
            else:
                # 按行分割
                outline_lines = [line.strip() for line in outline.split('\n') if line.strip()]
        
        # 生成细纲
        detailed_outline_parts = []
        
        # 预处理outline_lines，移除不包含#的元素
        outline_lines = [line for line in outline_lines if '#' in line]
        
        # 初始化会话历史
        conversation_history = []
        
        # 检查是否有中断状态需要恢复
        resume_state = self.current_generation_state.get('detailed_outline', {})
        start_index = resume_state.get('current_index', 0)
        if resume_state.get('detailed_outline_parts'):
            detailed_outline_parts = resume_state['detailed_outline_parts']
        if resume_state.get('conversation_history'):
            conversation_history = resume_state['conversation_history']
        
        # 重置中断标记
        self.is_interrupted = False
        
        try:
            # 处理粗纲数组的0,-1,-2位置（单独1组） - 如果是第一次执行
            if len(outline_lines) >= 3 and start_index == 0:
                # 构造提示词，包含粗纲的0,-1,-2位置
                selected_outline = [outline_lines[0], outline_lines[-2], outline_lines[-1]]
                outline_text = "\n".join(selected_outline)
                
                # 从配置文件中获取第一组提示词模板并替换变量
                prompt_template = prompts["detailed_outline_first"]
                prompt = prompt_template.format(topic=topic, characters=characters, outline=outline_text,outlineTemp=outline_lines[0])
                
                # 调用API生成细纲，传递会话历史和当前步骤
                detailed_outline_part = self._call_openai_api(prompt, 8192, conversation_history=conversation_history, step=5)
                
                # 检查是否中断
                if detailed_outline_part == "<GENERATION_INTERRUPTED>":
                    self.current_generation_state['detailed_outline'] = {
                        'current_index': 0,
                        'detailed_outline_parts': detailed_outline_parts,
                        'conversation_history': conversation_history,
                        'outline_lines': outline_lines,
                        'topic': topic,
                        'characters': characters
                    }
                    # 启用继续按钮
                    self.root.after(0, lambda: self.continue_detailed_outline_button.config(state=tk.NORMAL))
                    return
                
                detailed_outline_parts.append(detailed_outline_part)
                
                # 更新会话历史
                conversation_history.append({'role': 'user', 'content': prompt})
                conversation_history.append({'role': 'assistant', 'content': detailed_outline_part})
                
                # 更新当前进度
                start_index = 1
            
            # 处理粗纲数组的其他位置（每次步长为2，但在处理第1、倒数第一、倒数第二项时步长为1）
            i = start_index
            while i < len(outline_lines) and not self.is_interrupted:
                
                # 检查是否是第1、倒数第一、倒数第二项
                if i == 1 or i == len(outline_lines) - 1 or i == len(outline_lines) - 2:
                    # 步长为1
                    selected_outline = [outline_lines[i]]
                    outlineTemp = outline_lines[i]
                    i += 1
                else:
                    # 步长为2
                    selected_outline = outline_lines[i:i+2]
                    outlineTemp = "\n".join(selected_outline)
                    i += 2
                
                print(outlineTemp+"\n")
                # 从配置文件中获取后续提示词模板并替换变量
                prompt_template = prompts["detailed_outline_subsequent"]
                prompt = prompt_template.format(topic=topic, characters=characters, outline_text=outlineTemp,outlineTime=outlineTemp)
                
                # 调用API生成细纲，传递会话历史和当前步骤
                detailed_outline_part = self._call_openai_api(prompt, 8192, conversation_history=conversation_history, step=5)
                
                # 检查是否中断
                if detailed_outline_part == "<GENERATION_INTERRUPTED>":
                    self.current_generation_state['detailed_outline'] = {
                        'current_index': i,
                        'detailed_outline_parts': detailed_outline_parts,
                        'conversation_history': conversation_history,
                        'outline_lines': outline_lines,
                        'topic': topic,
                        'characters': characters
                    }
                    # 启用继续按钮
                    self.root.after(0, lambda: self.continue_detailed_outline_button.config(state=tk.NORMAL))
                    return
                
                detailed_outline_parts.append(detailed_outline_part)
                
                # 更新会话历史
                conversation_history.append({'role': 'user', 'content': prompt})
                conversation_history.append({'role': 'assistant', 'content': detailed_outline_part})
        except Exception as e:
            print(f"细纲生成异常: {e}")
            # 如果是中断异常，记录当前状态
            if self.is_interrupted:
                self.current_generation_state['detailed_outline'] = {
                    'current_index': i if 'i' in locals() else 0,
                    'detailed_outline_parts': detailed_outline_parts,
                    'conversation_history': conversation_history,
                    'outline_lines': outline_lines,
                    'topic': topic,
                    'characters': characters
                }
                # 启用继续按钮
                self.root.after(0, lambda: self.continue_detailed_outline_button.config(state=tk.NORMAL))
            return
        
        # 合并所有细纲部分
        detailed_outline = "\n\n".join(detailed_outline_parts)
        
        # 保存生成的内容
        self.generated_content["detailed_outline"] = detailed_outline
        
        # 在UI中显示细纲
        self.detailed_outline_text.delete("1.0", tk.END)
        self.detailed_outline_text.insert("1.0", detailed_outline)
        
        # 切换到细纲页面
        self.notebook.select(self.step5_frame)
        
        # 重新启用按钮
        self.save_detailed_outline_button.config(state=tk.NORMAL)
        self.regenerate_detailed_outline_button.config(state=tk.NORMAL)
        
    def regenerate_detailed_outline(self):
        # 清空原有内容
        self.detailed_outline_text.delete(1.0, tk.END)
        # 重新生成细纲
        self.generate_detailed_outline()
        
    def continue_detailed_outline(self):
        """
        从中断处继续生成细纲
        """
        # 检查是否有中断状态
        if 'detailed_outline' not in self.current_generation_state:
            messagebox.showinfo("提示", "没有检测到中断的细纲生成任务。")
            return
        
        # 获取中断状态
        resume_state = self.current_generation_state['detailed_outline']
        
        # 禁用按钮
        self.save_detailed_outline_button.config(state=tk.DISABLED)
        self.regenerate_detailed_outline_button.config(state=tk.DISABLED)
        self.continue_detailed_outline_button.config(state=tk.DISABLED)
        
        # 在新线程中继续生成
        threading.Thread(target=lambda: self._async_continue_detailed_outline(resume_state), daemon=True).start()
        
    def _async_continue_detailed_outline(self, resume_state):
        """
        异步从中断处继续生成细纲
        """
        try:
            # 从中断状态中恢复参数
            current_index = resume_state.get('current_index', 0)
            detailed_outline_parts = resume_state.get('detailed_outline_parts', [])
            conversation_history = resume_state.get('conversation_history', [])
            outline_lines = resume_state.get('outline_lines', [])
            topic = resume_state.get('topic', "")
            characters = resume_state.get('characters', "")
            
            # 重置中断标记
            self.is_interrupted = False
            
            # 继续处理未完成的部分
            i = current_index
            while i < len(outline_lines) and not self.is_interrupted:
                
                # 检查是否是第1、倒数第一、倒数第二项
                if i == 1 or i == len(outline_lines) - 1 or i == len(outline_lines) - 2:
                    # 步长为1
                    selected_outline = [outline_lines[i]]
                    outlineTemp = outline_lines[i]
                    i += 1
                else:
                    # 步长为2
                    selected_outline = outline_lines[i:i+2]
                    outlineTemp = "\n".join(selected_outline)
                    i += 2
                
                print(outlineTemp+"\n")
                # 从配置文件中获取后续提示词模板并替换变量
                prompt_template = prompts["detailed_outline_subsequent"]
                prompt = prompt_template.format(topic=topic, characters=characters, outline_text=outlineTemp,outlineTime=outlineTemp)
                
                # 调用API生成细纲，传递会话历史和当前步骤
                detailed_outline_part = self._call_openai_api(prompt, 8192, conversation_history=conversation_history, step=5)
                
                # 检查是否中断
                if detailed_outline_part == "<GENERATION_INTERRUPTED>":
                    self.current_generation_state['detailed_outline'] = {
                        'current_index': i,
                        'detailed_outline_parts': detailed_outline_parts,
                        'conversation_history': conversation_history,
                        'outline_lines': outline_lines,
                        'topic': topic,
                        'characters': characters
                    }
                    # 重新启用继续按钮
                    self.root.after(0, lambda: self.continue_detailed_outline_button.config(state=tk.NORMAL))
                    return
                
                detailed_outline_parts.append(detailed_outline_part)
                
                # 更新会话历史
                conversation_history.append({'role': 'user', 'content': prompt})
                conversation_history.append({'role': 'assistant', 'content': detailed_outline_part})
                
            # 如果完成了所有部分，清理中断状态
            if i >= len(outline_lines) and not self.is_interrupted:
                # 合并所有细纲部分
                detailed_outline = "\n\n".join(detailed_outline_parts)
                
                # 保存生成的内容
                self.generated_content["detailed_outline"] = detailed_outline
                
                # 在UI中显示细纲
                self.root.after(0, lambda: self.detailed_outline_text.delete("1.0", tk.END))
                self.root.after(0, lambda: self.detailed_outline_text.insert("1.0", detailed_outline))
                
                # 切换到细纲页面
                self.root.after(0, lambda: self.notebook.select(self.step5_frame))
                
                # 清理中断状态
                if 'detailed_outline' in self.current_generation_state:
                    del self.current_generation_state['detailed_outline']
                    # 禁用继续按钮
                    self.root.after(0, lambda: self.continue_detailed_outline_button.config(state=tk.DISABLED))
            
        except Exception as e:
            print(f"继续生成细纲异常: {e}")
            # 如果是中断异常，记录当前状态
            if self.is_interrupted:
                self.current_generation_state['detailed_outline'] = {
                    'current_index': i,
                    'detailed_outline_parts': detailed_outline_parts,
                    'conversation_history': conversation_history,
                    'outline_lines': outline_lines,
                    'topic': topic,
                    'characters': characters
                }
            # 重新启用继续按钮
            self.root.after(0, lambda: self.continue_detailed_outline_button.config(state=tk.NORMAL))
        finally:
            # 重新启用按钮
            self.root.after(0, lambda: self.save_detailed_outline_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.regenerate_detailed_outline_button.config(state=tk.NORMAL))
        
    def save_detailed_outline_and_continue(self):
        # 保存细纲
        detailed_outline = self.detailed_outline_text.get("1.0", tk.END).strip()
        self.generated_content["detailed_outline"] = detailed_outline
        
        # 保存细纲到文件
        with open(os.path.join(self.story_dir, "detailed_outline.txt"), "w", encoding="utf-8") as f:
            f.write(detailed_outline)
        
        # 继续生成正文
        self.current_step = 6
        self.generate_content()
        
    def generate_content(self, user_provided_outline=None):
        # 在新线程中执行生成任务
        threading.Thread(target=lambda: self._async_generate_content(user_provided_outline), daemon=True).start()
        
    def _async_generate_content(self, user_provided_outline=None):
        # 禁用保存并继续按钮
        self.save_content_button.config(state=tk.DISABLED)
        # 禁用重新生成按钮
        self.regenerate_content_button.config(state=tk.DISABLED)
        
        # 获取之前步骤的内容
        topic = self.generated_content.get("topic", "未生成选题")
        characters = self.generated_content.get("characters", "未生成人物设定")
        detailed_outline=""
        # 使用用户提供的细纲测试用例，如果没有则使用原来的细纲
        if user_provided_outline:
            detailed_outline_lines = user_provided_outline
        else:
            detailed_outline = self.generated_content.get("detailed_outline", "未生成细纲")
            
            # 解析细纲为数组（支持JSON数组格式和指定格式）
            try:
                detailed_outline_lines = json.loads(detailed_outline)
                if not isinstance(detailed_outline_lines, list):
                    # 如果不是数组，按行分割
                    detailed_outline_lines = [line.strip() for line in detailed_outline.split('\n') if line.strip()]
            except (json.JSONDecodeError, ValueError):
                # 尝试按指定格式解析
                if detailed_outline.strip().startswith('[') and detailed_outline.strip().endswith(']'):
                    # 尝试解析为JSON数组
                    try:
                        # 移除首尾的方括号
                        content = detailed_outline.strip()[1:-1]
                        # 分割数组元素
                        parts = []
                        current_part = ""
                        in_string = False
                        bracket_count = 0
                        
                        for char in content:
                            if char == '"' and (not current_part or current_part[-1] != '\\'):
                                in_string = not in_string
                                current_part += char
                            elif char == '[' and not in_string:
                                bracket_count += 1
                                current_part += char
                            elif char == ']' and not in_string:
                                bracket_count -= 1
                                current_part += char
                            elif char == ',' and not in_string and bracket_count == 0:
                                parts.append(current_part.strip())
                                current_part = ""
                            else:
                                current_part += char
                        
                        if current_part.strip():
                            parts.append(current_part.strip())
                        
                        # 处理每个部分，移除引号
                        detailed_outline_lines = []
                        for part in parts:
                            if part.startswith('"') and part.endswith('"'):
                                detailed_outline_lines.append(part[1:-1])
                            else:
                                detailed_outline_lines.append(part)
                    except:
                        # 如果解析失败，按"## 冲突"格式分割
                        detailed_outline_lines = self._parse_detailed_outline_by_conflict(detailed_outline)
                else:
                    # 按"## 冲突"格式分割
                    detailed_outline_lines = self._parse_detailed_outline_by_conflict(detailed_outline)
        
        # 生成正文
        content_parts = []
        conversation_history = []
        
        # 检查是否有中断状态需要恢复
        resume_state = self.current_generation_state.get('content', {})
        start_index = resume_state.get('current_index', 0)
        if resume_state.get('content_parts'):
            content_parts = resume_state['content_parts']
        if resume_state.get('conversation_history'):
            conversation_history = resume_state['conversation_history']
        
        # 重置中断标记
        self.is_interrupted = False
        
        try:
            # 处理细纲数组的第一个位置 - 如果是第一次执行
            if len(detailed_outline_lines) > 0 and start_index == 0:
                # 构造提示词，包含细纲的第一个位置
                selected_detailed_outline = detailed_outline_lines[0]
                
                # 从配置文件中获取第一组提示词模板并替换变量
                prompt_template = prompts["content_first"]
                prompt = prompt_template.format(characters=characters, selected_detailed_outline=selected_detailed_outline,detailed_outline=detailed_outline)
                
                # 调用API生成正文，传递当前步骤
                content_part = self._call_openai_api(prompt, 8000, False, conversation_history, step=6)
                
                # 检查是否中断
                if content_part == "<GENERATION_INTERRUPTED>":
                    self.current_generation_state['content'] = {
                        'current_index': 0,
                        'content_parts': content_parts,
                        'conversation_history': conversation_history,
                        'detailed_outline_lines': detailed_outline_lines,
                        'topic': topic,
                        'characters': characters,
                        'detailed_outline': detailed_outline
                    }
                    # 启用继续按钮
                    self.root.after(0, lambda: self.continue_content_button.config(state=tk.NORMAL))
                    return
                
                # 检查内容字数是否达标（首次生成要求1000字）
                if len(content_part.strip()) < CONTENT_SIZE_MIN and "API调用" not in content_part:
                    print(f"首次生成内容字数不足({len(content_part.strip())}字)，尝试补充...")
                    # 生成补充内容的提示词
                    supplement_prompt = f"""以下是你刚生成的内容，但字数不足{CONTENT_SIZE_MIN}字，请在保持原有风格和情节的基础上，补充更多细节和描写，使总字数达到要求。\n\n{content_part}"""
                    # 调用API补充内容
                    supplement_content = self._call_openai_api(supplement_prompt, 4000, False, conversation_history, step=6)
                    if "API调用" not in supplement_content:
                        content_part += supplement_content
                
                # 检查是否是API调用失败的特殊标记
                display_content = content_part  # 默认显示API返回的内容
                if "API调用失败" in content_part or "API调用异常" in content_part:
                    # 创建一个默认内容，确保章节不会缺失
                    default_content = f"（注：当前章节内容生成失败，请检查API配置后重试。细纲内容：{selected_detailed_outline[:50]}...）"
                    content_parts.append(default_content)
                    display_content = default_content  # 显示默认内容
                    print(f"API调用失败，使用默认内容替代: {default_content}")
                else:
                    content_parts.append(content_part.strip())
                
                # 实时更新UI
                self.content_text.insert(tk.END, f"\n\n{1:03d}\n" + display_content)
                self.root.update_idletasks()
                # 更新会话历史
                conversation_history.append({'role': 'user', 'content': prompt})
                conversation_history.append({'role': 'assistant', 'content': content_part})
                               
                # 获取当前步骤的平台配置
                step = 6  # 正文生成是第6步
                step_config = platform_model_configs.get(f"step{step}", {})
                platform = step_config.get("platform", current_platform)
                
                # 根据平台决定是否添加延迟，Deepseek平台API间隔限制较小，可以不停顿
                if platform != "deepseek":
                    print(f"等待{TIME_SLEEP}秒以避免请求限制...")
                    time.sleep(TIME_SLEEP)
                else:
                    print("使用Deepseek平台，无需额外延迟")
                
                # 更新当前进度
                start_index = 1
            
            # 处理细纲数组的其他位置（每次使用1个）
            for i in range(start_index, len(detailed_outline_lines)):
                if self.is_interrupted:
                    break
                    
                # 构造提示词，包含细纲的i位置
                selected_detailed_outline = detailed_outline_lines[i]
                print(selected_detailed_outline+"\n")
                # 判断是否为最后一次循环，决定使用哪个提示词模板
                if i == len(detailed_outline_lines) - 1 and prompts.get("content_last"):
                    # 最后一次循环，使用content_last.prompt
                    prompt_template = prompts["content_last"]
                    print("使用content_last.prompt生成最后一部分内容")
                else:
                    # 不是最后一次循环，使用content_subsequent.prompt
                    prompt_template = prompts["content_subsequent"]
                prompt = prompt_template.format(topic=topic, characters=characters, min_size=CONTENT_SIZE_MIN,selected_detailed_outline=selected_detailed_outline)
                
                # 调用API生成正文，传递当前步骤
                content_part = self._call_openai_api(prompt, 8000, False, conversation_history, step=6)
                
                # 检查是否中断
                if content_part == "<GENERATION_INTERRUPTED>":
                    self.current_generation_state['content'] = {
                        'current_index': i,
                        'content_parts': content_parts,
                        'conversation_history': conversation_history,
                        'detailed_outline_lines': detailed_outline_lines,
                        'topic': topic,
                        'characters': characters,
                        'detailed_outline': detailed_outline
                    }
                    # 启用继续按钮
                    self.root.after(0, lambda: self.continue_content_button.config(state=tk.NORMAL))
                    return
                
                # 检查内容字数是否达标（后续生成要求800字）
                if len(content_part.strip()) < CONTENT_SIZE_MIN and "API调用" not in content_part:
                    print(f"后续生成内容字数不足({len(content_part.strip())}字)，尝试补充...")
                    # 生成补充内容的提示词
                    supplement_prompt = f"""以下是你刚生成的内容，但字数不足{CONTENT_SIZE_MIN}字，请在保持原有风格和情节的基础上，补充更多细节和描写，使总字数达到要求。\n\n{content_part}"""
                    # 调用API补充内容
                    supplement_content = self._call_openai_api(supplement_prompt, 4000, False, conversation_history, step=6)
                    if "API调用" not in supplement_content:
                        content_part += supplement_content
                
                # 检查是否是API调用失败的特殊标记
                display_content = content_part  # 默认显示API返回的内容
                if "API调用失败" in content_part or "API调用异常" in content_part:
                    # 创建一个默认内容，确保章节不会缺失
                    default_content = f"（注：当前章节内容生成失败，请检查API配置后重试。细纲内容：{selected_detailed_outline[:50]}...）"
                    content_parts.append(default_content)
                    display_content = default_content  # 显示默认内容
                    print(f"API调用失败，使用默认内容替代: {default_content}")
                else:
                    content_parts.append(content_part.strip())
                
                # 实时更新UI
                self.content_text.insert(tk.END, f"\n\n{i+1:03d}\n" + display_content)
                self.root.update_idletasks()
                # 更新会话历史
                conversation_history.append({'role': 'user', 'content': prompt})
                conversation_history.append({'role': 'assistant', 'content': content_part})
                
                # 根据平台决定是否添加延迟，Deepseek平台API间隔限制较小，可以不停顿
                if platform != "deepseek":
                    print(f"等待{TIME_SLEEP}秒以避免请求限制...")
                    time.sleep(TIME_SLEEP)
                else:
                    print("使用Deepseek平台，无需额外延迟")
        except Exception as e:
            print(f"正文生成异常: {e}")
            # 如果是中断异常，记录当前状态
            if self.is_interrupted:
                self.current_generation_state['content'] = {
                    'current_index': i if 'i' in locals() else start_index,
                    'content_parts': content_parts,
                    'conversation_history': conversation_history,
                    'detailed_outline_lines': detailed_outline_lines,
                    'topic': topic,
                    'characters': characters,
                    'detailed_outline': detailed_outline
                }
                # 启用继续按钮
                self.root.after(0, lambda: self.continue_content_button.config(state=tk.NORMAL))
            return
        
        # 合并所有正文部分
        # 为每个段落添加带补零的章节号
        numbered_content_parts = [f"{idx+1:03d}\n{part}" for idx, part in enumerate(content_parts)]
        content = "\n".join(numbered_content_parts)
        
        # 保存生成的内容
        self.generated_content["content"] = content
        
        # 在UI中显示正文
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", content)
        
        # 切换到正文页面
        self.notebook.select(self.step6_frame)
        
        # 重新启用按钮
        self.save_content_button.config(state=tk.NORMAL)
        self.regenerate_content_button.config(state=tk.NORMAL)
        
    def _parse_detailed_outline_by_conflict(self, detailed_outline):
        """
        按"## 冲突"格式解析细纲
        
        Args:
            detailed_outline (str): 细纲内容
        
        Returns:
            list: 解析后的细纲数组
        """
        # 按"## 冲突"分割内容
        conflicts = detailed_outline.split('## 冲突')
        # 移除第一个空元素（如果有的话）
        if conflicts and not conflicts[0].strip():
            conflicts = conflicts[1:]
        
        # 处理每个冲突部分
        detailed_outline_lines = []
        for conflict in conflicts:
            # 移除首尾空白字符
            conflict = conflict.strip()
            if conflict:
                # 重新添加"## 冲突"前缀
                detailed_outline_lines.append('## 冲突' + conflict)
        
        return detailed_outline_lines
    
    def _call_openai_api(self, prompt, max_tokens, update_ui=True, conversation_history=None, step=None):
        """
        调用AI API的通用方法，支持多平台和多模型，包含网络错误重试机制
        
        Args:
            prompt (str): 提示词
            max_tokens (int): 最大token数
            update_ui (bool): 是否实时更新UI，默认为True
            conversation_history (list): 会话历史，默认为None
            step (int): 当前步骤，用于选择对应的平台和模型
        
        Returns:
            str: API返回的内容，如果是网络错误且重试失败则返回特殊标记
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 如果没有指定步骤，使用当前步骤
                if step is None:
                    step = self.current_step
                
                # 获取当前步骤的平台和模型配置
                step_config = platform_model_configs.get(f"step{step}", {})
                platform = step_config.get("platform", current_platform)
                model = step_config.get("model", current_model)
                
                print(f"调用API，平台: {platform}, 模型: {model}, 提示词长度: {len(prompt)}, max_tokens: {max_tokens}")
                
                # 构造消息列表
                if conversation_history:
                    messages = conversation_history.copy()
                    messages.append({'role': 'user', 'content': prompt})
                else:
                    messages = [{'role': 'user', 'content': prompt}]
                
                # 确保客户端已初始化
                if platform not in clients:
                    # 尝试使用默认的API密钥初始化
                    if platform == "siliconflow":
                        # 假设config中有siliconflow_api_key
                        api_key = config.get("siliconflow_api_key", config["api_key"])
                        clients[platform] = init_client(platform, api_key)
                    elif platform == "deepseek":
                        # Deepseek平台只需要API密钥
                        api_key = config.get("deepseek_api_key", config["api_key"])
                        clients[platform] = init_client(platform, api_key)
                    else:
                        # 其他平台可能需要base_url
                        api_key = config["api_key"]
                        base_url = config.get("base_url", "")
                        clients[platform] = init_client(platform, api_key, base_url)
                
                # 获取实际的模型ID
                actual_model_id = get_actual_model_id(model)
                
                # 调用对应的API
                response = clients[platform].chat.completions.create(
                    model=actual_model_id,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.8,
                    top_p=0.9,
                    stream=True
                )
                content = ""
                chunk_count = 0
                for chunk in response:
                    chunk_count += 1
                    if chunk.choices[0].delta.content:
                        chunk_content = chunk.choices[0].delta.content
                        # 去除正文部分每行末尾的两个空格
                        if self.current_step == 6 and '\n' in chunk_content:
                            # 处理chunk中的每行，移除行尾的两个空格
                            lines = chunk_content.split('\n')
                            for i in range(len(lines)):
                                if lines[i].endswith('  ') and len(lines[i]) > 2:
                                    lines[i] = lines[i][:-2]
                            chunk_content = '\n'.join(lines)
                        
                        content += chunk_content
                        # 根据参数决定是否实时更新UI
                        if update_ui:
                            if hasattr(self, 'topic_text') and self.current_step == 2:
                                self.topic_text.insert(tk.END, chunk_content)
                                self.topic_text.see(tk.END)
                            elif hasattr(self, 'characters_text') and self.current_step == 3:
                                self.characters_text.insert(tk.END, chunk_content)
                                self.characters_text.see(tk.END)
                            elif hasattr(self, 'outline_text') and self.current_step == 4:
                                self.outline_text.insert(tk.END, chunk_content)
                                self.outline_text.see(tk.END)
                            elif hasattr(self, 'detailed_outline_text') and self.current_step == 5:
                                self.detailed_outline_text.insert(tk.END, chunk_content)
                                self.detailed_outline_text.see(tk.END)
                            elif hasattr(self, 'content_text') and self.current_step == 6:
                                self.content_text.insert(tk.END, chunk_content)
                                self.content_text.see(tk.END)
                            elif hasattr(self, 'title_text') and hasattr(self, 'intro_text') and self.current_step == 7:
                                # 标题和导语的处理
                                pass  # 在具体方法中处理
                            self.root.update_idletasks()
                print(f"API调用完成，接收chunk数: {chunk_count}, 内容长度: {len(content)}")
                
                # 检查内容是否可能被截断
                if chunk_count > 0 and len(content) >= max_tokens * 3:  # 粗略估计，每个token约3个字符
                    warning_msg = f"生成的内容可能已达到长度限制，max_tokens: {max_tokens}。请考虑增加max_tokens参数以获取完整内容。"
                    print(warning_msg)
                    messagebox.showwarning("内容长度警告", warning_msg)
                
                if not content:
                    error_msg = f"API请求失败: 未获取到内容"
                    print(error_msg)
                    messagebox.showwarning("API错误", error_msg)
                    return "API调用失败，使用默认格式"
                return content
            except Exception as e:
                error_msg = f"API调用异常: {e}"
                print(error_msg)
                
                # 判断错误类型并设置不同的处理方式
                error_str = str(e).lower()
                # 限流错误 (429) - 直接标记为中断，让用户手动控制继续
                if "429" in error_str or "rate limit" in error_str or "tpm limit" in error_str:
                    # 标记为中断
                    self.is_interrupted = True
                    # 在主线程中显示对话框
                    self.root.after(0, lambda: messagebox.showerror("API限流", "API限流错误(429)：TPM限制已达到。\n请等待一段时间后点击'中断后继续'按钮。"))
                    return "<GENERATION_INTERRUPTED>"
                # 网络错误
                elif "timeout" in error_str or "network" in error_str or "connection" in error_str:
                    retry_count += 1
                    if retry_count < max_retries:
                        retry_msg = f"网络错误，正在进行第{retry_count}次重试..."
                        print(retry_msg)
                        # 在主线程中显示对话框
                        self.root.after(0, lambda msg=retry_msg: messagebox.showinfo("网络错误重试", msg))
                        # 确保platform变量已定义
                        if 'platform' not in locals():
                            step_config = platform_model_configs.get(f"step{step}", {})
                            platform = step_config.get("platform", current_platform)
                        
                        # 等待3秒后重试
                        if platform != "deepseek":
                            time.sleep(TIME_SLEEP)
                        else:
                            # Deepseek平台重试间隔可以更小
                            time.sleep(2)
                        continue
                    else:
                        # 重试次数用完，标记为中断
                        self.is_interrupted = True
                        # 在主线程中显示对话框
                        self.root.after(0, lambda: messagebox.showerror("网络错误", "网络错误，已尝试3次重试，生成中断。请检查网络连接后点击'中断后继续'按钮。"))
                        return "<GENERATION_INTERRUPTED>"
                # 硅基流动特定错误处理
                elif platform == "siliconflow":
                    # 检查是否是硅基流动平台的特定错误码
                    if "50508" in error_str or "system is too busy" in error_str:
                        # 标记为中断
                        self.is_interrupted = True
                        # 在主线程中显示对话框，提供更友好的错误提示和建议
                        self.root.after(0, lambda: messagebox.showerror(
                            "硅基流动服务繁忙", 
                            "硅基流动服务当前过于繁忙（错误码：50508）\n\n建议：\n1. 等待几分钟后点击'中断后继续'按钮重试\n2. 切换到其他平台（如DeepSeek或OpenAI）\n3. 尝试使用其他模型（如[16]千问替代[10]千问）"
                        ))
                        return "<GENERATION_INTERRUPTED>"
                    elif "50500" in error_str or "unknown error" in error_str:
                        # 标记为中断
                        self.is_interrupted = True
                        # 在主线程中显示对话框，提供更友好的错误提示和建议
                        self.root.after(0, lambda: messagebox.showerror(
                            "硅基流动未知错误", 
                            "硅基流动服务处理请求时出现未知错误（错误码：50500）\n\n建议：\n1. 等待几分钟后点击'中断后继续'按钮重试\n2. 切换到其他平台（如DeepSeek或OpenAI）\n3. 检查API密钥是否正确配置"
                        ))
                        return "<GENERATION_INTERRUPTED>"
                    elif "401" in error_str or "unauthorized" in error_str:
                        # 标记为中断
                        self.is_interrupted = True
                        # 在主线程中显示对话框
                        self.root.after(0, lambda: messagebox.showerror(
                            "API密钥错误", 
                            "硅基流动API密钥无效或已过期（错误码：401）\n\n建议：\n1. 检查并重新配置硅基流动API密钥\n2. 切换到其他平台（如DeepSeek或OpenAI）"
                        ))
                        return "<GENERATION_INTERRUPTED>"
                
                # 其他类型的错误不重试
                # 在主线程中显示对话框
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("API异常", msg))
                return f"API调用异常，使用默认格式"
        
    def regenerate_content(self, user_provided_outline=None):
        # 清空原有内容
        self.content_text.delete(1.0, tk.END)
        # 重新生成正文
        self.generate_content(user_provided_outline)
        
    def continue_content(self):
        """
        从中断处继续生成正文
        """
        # 检查是否有中断状态
        if 'content' not in self.current_generation_state:
            messagebox.showinfo("提示", "没有检测到中断的正文生成任务。")
            return
        
        # 获取中断状态
        resume_state = self.current_generation_state['content']
        
        # 禁用按钮
        self.save_content_button.config(state=tk.DISABLED)
        self.regenerate_content_button.config(state=tk.DISABLED)
        self.continue_content_button.config(state=tk.DISABLED)
        
        # 在新线程中继续生成
        threading.Thread(target=lambda: self._async_continue_content(resume_state), daemon=True).start()
        
    def _async_continue_content(self, resume_state):
        """
        异步从中断处继续生成正文
        """
        try:
            # 从中断状态中恢复参数
            current_index = resume_state.get('current_index', 0)
            content_parts = resume_state.get('content_parts', [])
            conversation_history = resume_state.get('conversation_history', [])
            detailed_outline_lines = resume_state.get('detailed_outline_lines', [])
            topic = resume_state.get('topic', "")
            characters = resume_state.get('characters', "")
            detailed_outline = resume_state.get('detailed_outline', "")
            
            # 重置中断标记
            self.is_interrupted = False
            
            # 继续处理未完成的部分
            for i in range(current_index, len(detailed_outline_lines)):
                if self.is_interrupted:
                    break
                    
                # 构造提示词，包含细纲的i位置
                selected_detailed_outline = detailed_outline_lines[i]
                print(selected_detailed_outline+"\n")
                # 判断是否为最后一次循环，决定使用哪个提示词模板
                if i == len(detailed_outline_lines) - 1 and prompts.get("content_last"):
                    # 最后一次循环，使用content_last.prompt
                    prompt_template = prompts["content_last"]
                    print("使用content_last.prompt生成最后一部分内容")
                else:
                    # 不是最后一次循环，使用content_subsequent.prompt
                    prompt_template = prompts["content_subsequent"]
                prompt = prompt_template.format(topic=topic, characters=characters, selected_detailed_outline=selected_detailed_outline)
                
                # 调用API生成正文，传递当前步骤
                content_part = self._call_openai_api(prompt, 8000, False, conversation_history, step=6)
                
                # 检查是否中断
                if content_part == "<GENERATION_INTERRUPTED>":
                    self.current_generation_state['content'] = {
                        'current_index': i,
                        'content_parts': content_parts,
                        'conversation_history': conversation_history,
                        'detailed_outline_lines': detailed_outline_lines,
                        'topic': topic,
                        'characters': characters,
                        'detailed_outline': detailed_outline
                    }
                    # 重新启用继续按钮
                    self.root.after(0, lambda: self.continue_content_button.config(state=tk.NORMAL))
                    return
                
                content_parts.append(content_part.strip())
                # 实时更新UI
                self.root.after(0, lambda i=i, content_part=content_part: self.content_text.insert(tk.END, f"\n\n{i+1:03d}\n" + content_part))
                self.root.after(0, lambda: self.root.update_idletasks())
                # 更新会话历史
                conversation_history.append({'role': 'user', 'content': prompt})
                conversation_history.append({'role': 'assistant', 'content': content_part})
                
            # 如果完成了所有部分，清理中断状态
            if i >= len(detailed_outline_lines) - 1 and not self.is_interrupted:
                # 合并所有正文部分
                # 为每个段落添加带补零的章节号
                numbered_content_parts = [f"{idx+1:03d}\n{part}" for idx, part in enumerate(content_parts)]
                content = "\n".join(numbered_content_parts)
                
                # 保存生成的内容
                self.generated_content["content"] = content
                
                # 在UI中显示正文
                self.root.after(0, lambda: self.content_text.delete("1.0", tk.END))
                self.root.after(0, lambda: self.content_text.insert("1.0", content))
                
                # 切换到正文页面
                self.root.after(0, lambda: self.notebook.select(self.step6_frame))
                
                # 清理中断状态
                if 'content' in self.current_generation_state:
                    del self.current_generation_state['content']
                    # 禁用继续按钮
                    self.root.after(0, lambda: self.continue_content_button.config(state=tk.DISABLED))
            
        except Exception as e:
            print(f"继续生成正文异常: {e}")
            # 如果是中断异常，记录当前状态
            if self.is_interrupted:
                self.current_generation_state['content'] = {
                    'current_index': i if 'i' in locals() else current_index,
                    'content_parts': content_parts,
                    'conversation_history': conversation_history,
                    'detailed_outline_lines': detailed_outline_lines,
                    'topic': topic,
                    'characters': characters,
                    'detailed_outline': detailed_outline
                }
            # 重新启用继续按钮
            self.root.after(0, lambda: self.continue_content_button.config(state=tk.NORMAL))
        finally:
            # 重新启用按钮
            self.root.after(0, lambda: self.save_content_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.regenerate_content_button.config(state=tk.NORMAL))
        
    def save_content_and_continue(self):
        # 保存正文
        content = self.content_text.get("1.0", tk.END).strip()
        self.generated_content["content"] = content
        
        # 保存正文到文件
        with open(os.path.join(self.story_dir, "content.txt"), "w", encoding="utf-8") as f:
            f.write(content)
        
        # 继续生成标题和导语
        self.current_step = 7
        self.generate_title_and_intro()
        
    def generate_title_and_intro(self):
        # 在新线程中执行生成任务
        threading.Thread(target=self._async_generate_title_and_intro, daemon=True).start()
        
    def _async_generate_title_and_intro(self):
        # 禁用保存按钮
        self.save_title_and_intro_and_finish_button.config(state=tk.DISABLED)
        # 禁用重新生成按钮
        self.regenerate_title_and_intro_button.config(state=tk.DISABLED)
        
        # 获取之前步骤的内容
        topic = self.generated_content.get("topic", "未生成选题")
        characters = self.generated_content.get("characters", "未生成人物设定")
        detailed_outline = self.generated_content.get("detailed_outline", "未生成细纲")
        
        # 生成标题
        title_prompt_template = prompts["title"]
        # 使用细纲代替正文生成标题
        title_prompt = title_prompt_template.format(topic=topic, characters=characters, content=detailed_outline)
        
        # 调用API生成标题，传递当前步骤
        title = self._call_openai_api(title_prompt, 8192, step=7)
        title = title.strip()
        
        # 生成导语
        intro_prompt_template = prompts["intro"]
        # 使用细纲代替正文生成导语
        intro_prompt = intro_prompt_template.format(topic=topic, characters=characters, content=detailed_outline)
        
        # 调用API生成导语，传递当前步骤
        intro = self._call_openai_api(intro_prompt, 8192, step=7)
        intro = intro.strip()
        
        # 保存生成的内容
        self.generated_content["title"] = title
        self.generated_content["intro"] = intro
        
        # 在UI中显示标题和导语
        self.title_text.delete("1.0", tk.END)
        self.title_text.insert("1.0", title)
        self.intro_text.delete("1.0", tk.END)
        self.intro_text.insert("1.0", intro)
        
        # 切换到标题和导语页面
        self.notebook.select(self.step7_frame)
        
        # 重新启用按钮
        self.save_title_and_intro_and_finish_button.config(state=tk.NORMAL)
        self.regenerate_title_and_intro_button.config(state=tk.NORMAL)
        
    def regenerate_title_and_intro(self):
        # 清空原有内容
        self.title_text.delete(1.0, tk.END)
        self.intro_text.delete(1.0, tk.END)
        # 重新生成标题和导语
        self.generate_title_and_intro()
        
    def save_title_and_intro_and_finish(self):
        # 保存标题和导语
        title = self.title_text.get("1.0", tk.END).strip()
        intro = self.intro_text.get("1.0", tk.END).strip()
        self.generated_content["title"] = title
        self.generated_content["intro"] = intro
        
        # 保存标题和导语到文件
        with open(os.path.join(self.story_dir, "title_intro.txt"), "w", encoding="utf-8") as f:
            f.write(f"标题：{title}\n")
            f.write(f"导语：{intro}\n")
        
        # 完成
        messagebox.showinfo("完成", f"故事生成完成！\n文件已保存到：{self.story_dir}")
        
    def load_previous_story(self, event=None):
        """加载之前的故事记录"""
        selected_story = self.previous_story_var.get()
        if not selected_story:
            return

        # 设置当前故事目录
        self.story_dir = os.path.join(self.stories_base_dir, selected_story)
        
        # 加载topic.txt
        topic_file = os.path.join(self.story_dir, "topic.txt")
        if os.path.exists(topic_file):
            with open(topic_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 解析内容
                lines = content.split("\n")
                story_type = ""
                dilemma_type = ""
                platform = ""
                inspiration = ""
                
                for line in lines:
                    if line.startswith("故事类型："):
                        story_type = line.split("：", 1)[1]
                        self.story_type_var.set(story_type)
                    elif line.startswith("困境类型："):
                        dilemma_type = line.split("：", 1)[1]
                        self.dilemma_type_var.set(dilemma_type)
                    elif line.startswith("投稿平台："):
                        platform = line.split("：", 1)[1]
                        self.platform_var.set(platform)
                    elif line.startswith("灵感："):
                        inspiration = line.split("：", 1)[1]
                        self.inspiration_text.delete("1.0", tk.END)
                        self.inspiration_text.insert("1.0", inspiration)
                    elif line.startswith("选题："):
                        # 保存选题内容
                        topic_content = "\n".join(lines[lines.index(line):])
                        self.generated_content["topic"] = topic_content
                
                # 更新user_inputs字典
                self.user_inputs = {
                    "story_type": story_type,
                    "dilemma_type": dilemma_type,
                    "platform": platform,
                    "emotion_type": self.user_inputs.get("emotion_type", "默认情绪类型"),
                    "inspiration": inspiration
                }
        
        # 加载characters.txt
        characters_file = os.path.join(self.story_dir, "characters.txt")
        if os.path.exists(characters_file):
            with open(characters_file, "r", encoding="utf-8") as f:
                self.generated_content["characters"] = f.read()
        
        # 加载outline.txt
        outline_file = os.path.join(self.story_dir, "outline.txt")
        if os.path.exists(outline_file):
            with open(outline_file, "r", encoding="utf-8") as f:
                self.generated_content["outline"] = f.read()
        
        # 加载detailed_outline.txt
        detailed_outline_file = os.path.join(self.story_dir, "detailed_outline.txt")
        if os.path.exists(detailed_outline_file):
            with open(detailed_outline_file, "r", encoding="utf-8") as f:
                self.generated_content["detailed_outline"] = f.read()
        
        # 加载content.txt
        content_file = os.path.join(self.story_dir, "content.txt")
        if os.path.exists(content_file):
            with open(content_file, "r", encoding="utf-8") as f:
                self.generated_content["content"] = f.read()
        
        # 加载title_intro.txt
        title_intro_file = os.path.join(self.story_dir, "title_intro.txt")
        if os.path.exists(title_intro_file):
            with open(title_intro_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 解析标题和导语
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("标题："):
                        if "title" not in self.generated_content:
                            self.generated_content["title"] = line.split("：", 1)[1]
                    elif line.startswith("导语："):
                        if "intro" not in self.generated_content:
                            self.generated_content["intro"] = line.split("：", 1)[1]
        
        # 更新UI
        self.update_ui_with_loaded_content()
        
    def update_ui_with_loaded_content(self):
        """使用加载的内容更新UI"""
        # 更新选题页面
        if "topic" in self.generated_content:
            self.topic_text.delete("1.0", tk.END)
            self.topic_text.insert("1.0", self.generated_content["topic"])
        
        # 更新人物设定页面
        if "characters" in self.generated_content:
            self.characters_text.delete("1.0", tk.END)
            self.characters_text.insert("1.0", self.generated_content["characters"])
        
        # 更新粗纲页面
        if "outline" in self.generated_content:
            self.outline_text.delete("1.0", tk.END)
            self.outline_text.insert("1.0", self.generated_content["outline"])
        
        # 更新细纲页面
        if "detailed_outline" in self.generated_content:
            self.detailed_outline_text.delete("1.0", tk.END)
            self.detailed_outline_text.insert("1.0", self.generated_content["detailed_outline"])
        
        # 更新正文页面
        if "content" in self.generated_content:
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert("1.0", self.generated_content["content"])
        
        # 更新标题和导语页面
        if "title" in self.generated_content:
            self.title_text.delete("1.0", tk.END)
            self.title_text.insert("1.0", self.generated_content["title"])
        if "intro" in self.generated_content:
            self.intro_text.delete("1.0", tk.END)
            self.intro_text.insert("1.0", self.generated_content["intro"])
        
        messagebox.showinfo("加载完成", f"已加载故事记录：{self.story_dir}")
        
    def prev_step(self):
        # 回到上一步
        if self.current_step > 2:
            self.current_step -= 1
            # 切换到对应的页面
            if self.current_step == 2:
                self.notebook.select(self.step2_frame)
            elif self.current_step == 3:
                self.notebook.select(self.step3_frame)
            elif self.current_step == 4:
                self.notebook.select(self.step4_frame)
            elif self.current_step == 5:
                self.notebook.select(self.step5_frame)
            elif self.current_step == 6:
                self.notebook.select(self.step6_frame)
            elif self.current_step == 7:
                self.notebook.select(self.step7_frame)


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = StoryGeneratorApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("程序已被用户中断")
        # 可以添加更多清理代码如果需要
    except Exception as e:
        print(f"程序异常: {e}")
        input("按回车键退出...")