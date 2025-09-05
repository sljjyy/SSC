import os
import subprocess
import sys
import shutil

# 确保中文显示正常
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

def build_exe():
    print("开始打包程序为可执行文件...")
    
    # 检查pyinstaller是否已安装
    try:
        import PyInstaller
        print(f"已安装PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller未安装，正在尝试安装...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("PyInstaller安装成功")
    
    # 定义打包命令参数
    # --onefile: 生成单个可执行文件
    # --windowed: 不显示控制台窗口
    # --icon: 可选，设置程序图标
    # --name: 设置生成的exe文件名
    # --add-data: 添加资源文件（提示词文件夹）
    # --hidden-import: 添加隐藏导入的模块
    # 使用python -m pyinstaller的方式调用，更可靠
    build_command = [
        sys.executable,
        '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name', 'StoryGenerator',
        '--add-data', f'{os.path.join(current_dir, "prompts")};prompts',
        '--hidden-import', 'tkinter',
        '--hidden-import', 'openai',
        '--hidden-import', 'win32api',
        '--hidden-import', 'win32con',
        '--hidden-import', 'win32gui',
        '--clean',
        os.path.join(current_dir, 'main.py')
    ]
    
    # 打印打包命令以便调试
    print(f"执行打包命令: {' '.join(build_command)}")
    
    # 执行打包命令
    try:
        subprocess.run(build_command, check=True)
        print("打包成功!")
        
        # 检查dist目录是否存在
        dist_dir = os.path.join(current_dir, 'dist')
        if os.path.exists(dist_dir):
            print(f"可执行文件已生成在: {dist_dir}")
            
            # 创建配置文件模板
            create_config_template()
            
            # 复制README文件
            copy_readme_files()
            
            print("\n打包完成！\n\n" \
                  "请执行以下步骤: \
" \
                  "1. 前往dist目录找到StoryGenerator.exe\n" \
                  "2. 运行程序前，请确保在同一目录下创建config.json文件\n" \
                  "3. 您可以参考config.json.exp文件作为配置模板")
        else:
            print("dist目录不存在，打包可能失败")
            
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
        
def create_config_template():
    """创建配置文件模板"""
    try:
        # 检查是否有config.json.exp文件
        config_exp_path = os.path.join(current_dir, 'config.json.exp')
        dist_config_path = os.path.join(current_dir, 'dist', 'config.json.exp')
        
        if os.path.exists(config_exp_path):
            # 复制现有模板文件
            shutil.copy2(config_exp_path, dist_config_path)
            print(f"已复制配置模板到: {dist_config_path}")
        else:
            # 创建默认模板文件
            default_config = {
                "api_key": "",
                "base_url": "",
                "siliconflow_api_key": "",
                "deepseek_api_key": ""
            }
            
            with open(dist_config_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            print(f"已创建默认配置模板到: {dist_config_path}")
    except Exception as e:
        print(f"创建配置模板失败: {e}")

def copy_readme_files():
    """复制README文件到dist目录"""
    try:
        # 复制README.md
        readme_path = os.path.join(current_dir, 'README.md')
        dist_readme_path = os.path.join(current_dir, 'dist', 'README.md')
        if os.path.exists(readme_path):
            shutil.copy2(readme_path, dist_readme_path)
            print(f"已复制README.md到: {dist_readme_path}")
        
        # 复制README_PROMPTS.md
        prompts_readme_path = os.path.join(current_dir, 'prompts', 'README_PROMPTS.md')
        dist_prompts_readme_path = os.path.join(current_dir, 'dist', 'README_PROMPTS.md')
        if os.path.exists(prompts_readme_path):
            shutil.copy2(prompts_readme_path, dist_prompts_readme_path)
            print(f"已复制README_PROMPTS.md到: {dist_prompts_readme_path}")
        
        # 复制README_LAUNCHER.md
        launcher_readme_path = os.path.join(current_dir, 'README_LAUNCHER.md')
        dist_launcher_readme_path = os.path.join(current_dir, 'dist', 'README_LAUNCHER.md')
        if os.path.exists(launcher_readme_path):
            shutil.copy2(launcher_readme_path, dist_launcher_readme_path)
            print(f"已复制README_LAUNCHER.md到: {dist_launcher_readme_path}")
            
        # 复制README_FIX.md
        fix_readme_path = os.path.join(current_dir, 'README_FIX.md')
        dist_fix_readme_path = os.path.join(current_dir, 'dist', 'README_FIX.md')
        if os.path.exists(fix_readme_path):
            shutil.copy2(fix_readme_path, dist_fix_readme_path)
            print(f"已复制README_FIX.md到: {dist_fix_readme_path}")
            
    except Exception as e:
        print(f"复制README文件失败: {e}")

if __name__ == "__main__":
    build_exe()