import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import datetime
from openai import OpenAI
from http import HTTPStatus
import json
import threading

# 读取配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 初始化OpenAI客户端
client = OpenAI(
    api_key=config["api_key"],
    base_url=config["base_url"]
)

# 根据配置选择模型
def get_model():
    return config["model"]

# 读取提示词配置文件
def load_prompts():
    prompts = {}
    prompt_files = [
        "topic.prompt",
        "outline.prompt",
        "detailed_outline_first.prompt",
        "detailed_outline_subsequent.prompt",
        "content_first.prompt",
        "content_subsequent.prompt",
        "title.prompt",
        "intro.prompt",
        "protagonist.prompt",
        "antagonist.prompt",
        "supporting.prompt"
    ]
    
    for file in prompt_files:
        with open(f'prompts/{file}', 'r', encoding='utf-8') as f:
            # 使用文件名（不含扩展名）作为键
            key = file.split('.')[0]
            prompts[key] = f.read()
    
    return prompts

prompts = load_prompts()


class StoryGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文学创作辅助工具")
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
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        # 标题
        title_label = tk.Label(self.root, text="文学创作辅助工具", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 创建 Notebook 控件用于分步显示
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
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
        
    def create_step1_widgets(self):
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
                                       values=["世情", "穿越", "悬疑", "修仙","科幻", "奇幻", "都市", "历史", "军事", "游戏", "体育"])
        story_type_combo.pack(side="left", padx=(10, 0))
        story_type_combo.set("世情")
        
        # 困境类型
        dilemma_type_frame = tk.Frame(self.step1_frame)
        dilemma_type_frame.pack(pady=5, padx=20, fill="x")
        
        dilemma_type_label = tk.Label(dilemma_type_frame, text="困境类型:")
        dilemma_type_label.pack(side="left")
        
        self.dilemma_type_var = tk.StringVar()
        dilemma_type_combo = ttk.Combobox(dilemma_type_frame, textvariable=self.dilemma_type_var,
                                         values=["爱而不得", "生死危机", "恨之入骨", "一无所有 "])
        dilemma_type_combo.pack(side="left", padx=(10, 0))
        dilemma_type_combo.set("爱而不得")
        
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
        
        # 按钮框架
        button_frame = tk.Frame(self.step1_frame)
        button_frame.pack(pady=20)
        
        self.start_generate_button = tk.Button(button_frame, text="开始生成", command=self.generate_story, bg="#4CAF50", fg="white", padx=20)
        self.start_generate_button.pack(side="left", padx=10)
        
        exit_button = tk.Button(button_frame, text="退出", command=self.root.quit, bg="#f44336", fg="white", padx=20)
        exit_button.pack(side="left", padx=10)
        
    def create_step2_widgets(self):
        # 选题编辑区域
        topic_frame = tk.Frame(self.step2_frame)
        topic_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        topic_label = tk.Label(topic_frame, text="选题:")
        topic_label.pack(anchor="w")
        
        self.topic_text = scrolledtext.ScrolledText(topic_frame, height=15)
        self.topic_text.pack(fill="both", expand=True, pady=(5, 0))
        
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
        # 人设编辑区域
        characters_frame = tk.Frame(self.step3_frame)
        characters_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        characters_label = tk.Label(characters_frame, text="人设:")
        characters_label.pack(anchor="w")
        
        self.characters_text = scrolledtext.ScrolledText(characters_frame, height=15)
        self.characters_text.pack(fill="both", expand=True, pady=(5, 0))
        
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
        # 粗纲编辑区域
        outline_frame = tk.Frame(self.step4_frame)
        outline_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        outline_label = tk.Label(outline_frame, text="粗纲:")
        outline_label.pack(anchor="w")
        
        self.outline_text = scrolledtext.ScrolledText(outline_frame, height=15)
        self.outline_text.pack(fill="both", expand=True, pady=(5, 0))
        
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
        # 细纲编辑区域
        detailed_outline_frame = tk.Frame(self.step5_frame)
        detailed_outline_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        detailed_outline_label = tk.Label(detailed_outline_frame, text="细纲:")
        detailed_outline_label.pack(anchor="w")
        
        self.detailed_outline_text = scrolledtext.ScrolledText(detailed_outline_frame, height=15)
        self.detailed_outline_text.pack(fill="both", expand=True, pady=(5, 0))
        
        # 按钮框架
        button_frame = tk.Frame(self.step5_frame)
        button_frame.pack(pady=20)
        
        prev_button = tk.Button(button_frame, text="上一步", command=self.prev_step, bg="#FF9800", fg="white", padx=20)
        prev_button.pack(side="left", padx=10)
        
        self.regenerate_detailed_outline_button = tk.Button(button_frame, text="重新生成", command=self.regenerate_detailed_outline, bg="#2196F3", fg="white", padx=20)
        self.regenerate_detailed_outline_button.pack(side="left", padx=10)
        
        self.save_detailed_outline_button = tk.Button(button_frame, text="保存并继续", command=self.save_detailed_outline_and_continue, bg="#4CAF50", fg="white", padx=20)
        self.save_detailed_outline_button.pack(side="left", padx=10)
        
    def create_step6_widgets(self):
        # 正文编辑区域
        content_frame = tk.Frame(self.step6_frame)
        content_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        content_label = tk.Label(content_frame, text="正文:")
        content_label.pack(anchor="w")
        
        self.content_text = scrolledtext.ScrolledText(content_frame, height=15)
        self.content_text.pack(fill="both", expand=True, pady=(5, 0))
        
        # 按钮框架
        button_frame = tk.Frame(self.step6_frame)
        button_frame.pack(pady=20)
        
        prev_button = tk.Button(button_frame, text="上一步", command=self.prev_step, bg="#FF9800", fg="white", padx=20)
        prev_button.pack(side="left", padx=10)
        
        self.regenerate_content_button = tk.Button(button_frame, text="重新生成", command=self.regenerate_content, bg="#2196F3", fg="white", padx=20)
        self.regenerate_content_button.pack(side="left", padx=10)
        
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
        
        intro_label = tk.Label(title_intro_frame, text="导语:")
        intro_label.pack(anchor="w", pady=(10, 0))

        self.intro_text = scrolledtext.ScrolledText(title_intro_frame, height=5)
        self.intro_text.pack(fill="both", expand=True, pady=(5, 0))
        
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
        
    def generate_topic(self):
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
        
        # 构造一个连续上下文的提示词，同时生成主角、反派和配角
        characters_prompt_template = """你是短故事专家,擅长投稿到{platform},协助进行人物设定
        
**只返回 人物基本信息、背景、性格、语言特征、价值观念、行为动作、语言风格、人物弧光**

> 用户输入故事选题
```
{topic}
```
---接下来，我们正在为一个快节奏，好看的网文短故事设计人物。这个故事需要以下三个人物：

1. 主角：
   有一个身份，这个身份交代了ta的socioeconomicstatus，基本信息，以及ta过去的和现在的处境。
   有一定的性格，ta的性格是与处境相关的，但是却是异于常人，有故事性的。
   这样的性格决定了ta的思维模式，又带来了异于常人的行为模式，带来了异于常人的事件与经历。
   以上的条件也给ta带来了特征鲜明的语言特征。人物要立体，有光明的一面也有黑暗的一面。所有的一切都要出人意料，要非常极端，但是细想又能够明白其中的逻辑
   有极致价值观念、极致行为动作、极致语言风格
   **姓名三个字以上，以减少重复的可能性**

2. 反派：
   请先想想这样的人和世界会发生什么样的关系，有什么样的激烈的冲突，100字。要精彩，要有网文风格
   然后安排给主角一个在现阶段几乎无法招架，造成极大压力的强大反派，让人一看就恨得牙痒痒。写出反派人物小传
   **姓名三个字**

3. 异性配角：
   请先想想这样的人和世界会发生什么样的关系，两个人会产生什么样的化学反应，100字。要精彩，要有网文风格
   写出异性配角人物小传
   **姓名三个字**

请在一个连续的上下文中生成这三个人物设定，确保他们之间有内在的联系和化学反应。"""
        
        # 格式化提示词
        platform = self.user_inputs.get("platform", "短故事平台")
        characters_prompt = characters_prompt_template.format(topic=topic, platform=platform)
        
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
        
        # 处理粗纲数组的0,-1,-2位置（单独1组）
        if len(outline_lines) >= 3:
            # 构造提示词，包含粗纲的0,-1,-2位置
            selected_outline = [outline_lines[0], outline_lines[-2], outline_lines[-1]]
            outline_text = "\n".join(selected_outline)
            
            # 从配置文件中获取第一组提示词模板并替换变量
            prompt_template = prompts["detailed_outline_first"]
            prompt = prompt_template.format(topic=topic, characters=characters, outline=outline_text,outlineTemp=outline_lines[0])
            
            # 调用通义千问API生成细纲，传递会话历史
            detailed_outline_part = self._call_openai_api(prompt, 8192, conversation_history=conversation_history)
            detailed_outline_parts.append(detailed_outline_part)
            
            # 更新会话历史
            conversation_history.append({'role': 'user', 'content': prompt})
            conversation_history.append({'role': 'assistant', 'content': detailed_outline_part})
        
        # 处理粗纲数组的其他位置（每次步长为2，但在处理第1、倒数第一、倒数第二项时步长为1）
        i = 1
        while i < len(outline_lines):
            
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
            
            # 调用通义千问API生成细纲，传递会话历史
            detailed_outline_part = self._call_openai_api(prompt, 8192, conversation_history=conversation_history)
            detailed_outline_parts.append(detailed_outline_part)
            
            # 更新会话历史
            conversation_history.append({'role': 'user', 'content': prompt})
            conversation_history.append({'role': 'assistant', 'content': detailed_outline_part})
        
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
        
        # 处理细纲数组的第一个位置
        if len(detailed_outline_lines) > 0:
            # 构造提示词，包含细纲的第一个位置
            selected_detailed_outline = detailed_outline_lines[0]
            
            # 从配置文件中获取第一组提示词模板并替换变量
            prompt_template = prompts["content_first"]
            prompt = prompt_template.format(characters=characters, selected_detailed_outline=selected_detailed_outline,detailed_outline=detailed_outline)
            
            # 调用通义千问API生成正文
            content_part = self._call_openai_api(prompt, 8000, False, conversation_history)
            content_parts.append(content_part.strip())
            # 实时更新UI
            self.content_text.insert(tk.END, f"\n\n\n\n{1:03d}\n\n" + content_part)
            self.root.update_idletasks()
            # 更新会话历史
            conversation_history.append({'role': 'user', 'content': prompt})
            conversation_history.append({'role': 'assistant', 'content': content_part})
        
        # 处理细纲数组的其他位置（每次使用1个）
        for i in range(1, len(detailed_outline_lines)):
            # 构造提示词，包含细纲的i位置
            selected_detailed_outline = detailed_outline_lines[i]
            print(selected_detailed_outline+"\n")
            # 从配置文件中获取后续提示词模板并替换变量
            prompt_template = prompts["content_subsequent"]
            prompt = prompt_template.format(topic=topic, characters=characters, selected_detailed_outline=selected_detailed_outline)
            
            # 调用通义千问API生成正文
            content_part = self._call_openai_api(prompt, 8000, False, conversation_history)
            content_parts.append(content_part.strip())
            # 实时更新UI
            self.content_text.insert(tk.END, f"\n\n{i+1:03d}\n" + content_part)
            self.root.update_idletasks()
            # 更新会话历史
            conversation_history.append({'role': 'user', 'content': prompt})
            conversation_history.append({'role': 'assistant', 'content': content_part})
        
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
    
    def _call_openai_api(self, prompt, max_tokens, update_ui=True, conversation_history=None):
        """
        调用OpenAI API的通用方法
        
        Args:
            prompt (str): 提示词
            max_tokens (int): 最大token数
            update_ui (bool): 是否实时更新UI，默认为True
            conversation_history (list): 会话历史，默认为None
        
        Returns:
            str: API返回的内容
        """
        try:
            print(f"调用API，提示词长度: {len(prompt)}, max_tokens: {max_tokens}")
            # 构造消息列表
            if conversation_history:
                messages = conversation_history.copy()
                messages.append({'role': 'user', 'content': prompt})
            else:
                messages = [{'role': 'user', 'content': prompt}]
            
            response = client.chat.completions.create(
                model=get_model(),
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
            messagebox.showerror("API异常", error_msg)
            return f"API调用异常，使用默认格式"
        
    def regenerate_content(self, user_provided_outline=None):
        # 清空原有内容
        self.content_text.delete(1.0, tk.END)
        # 重新生成正文
        self.generate_content(user_provided_outline)
        
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
        content = self.generated_content.get("content", "未生成正文")
        
        # 生成标题
        title_prompt_template = prompts["title"]
        # 不再限制正文内容长度
        title_prompt = title_prompt_template.format(topic=topic, characters=characters, content=content)
        
        # 调用OpenAI API生成标题
        title = self._call_openai_api(title_prompt, 8192)
        title = title.strip()
        
        # 生成导语
        intro_prompt_template = prompts["intro"]
        intro_prompt = intro_prompt_template.format(topic=topic, characters=characters, content=content)
        
        # 调用OpenAI API生成导语
        intro = self._call_openai_api(intro_prompt, 8192)
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
    root = tk.Tk()
    app = StoryGeneratorApp(root)
    root.mainloop()