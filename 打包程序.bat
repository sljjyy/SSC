@echo off
chcp 65001 > nul

:: 设置颜色
color 0A

:: 显示欢迎信息
echo. 
echo =======================================================
echo         故事生成器打包工具
          Story Generator Packager
echo =======================================================
echo.

:: 检查Python是否安装
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境。请先安装Python并添加到系统环境变量。
    echo 您可以从 https://www.python.org/downloads/ 下载Python安装包
    pause
    exit /b 1
)

echo 已检测到Python环境，正在准备打包...

:: 安装必要的依赖项
echo.
echo 正在安装必要的依赖项...
pip install --upgrade pip >nul 2>nul
pip install -r requirements.txt >nul 2>nul
if %errorlevel% neq 0 (
    echo 警告: 依赖项安装可能不完整，但会继续尝试打包。
)

echo.
echo 开始打包程序为可执行文件...
echo 这可能需要几分钟时间，请耐心等待...

:: 运行打包脚本
python build_exe.py

:: 检查打包结果
if %errorlevel% neq 0 (
    echo.
echo 错误: 打包过程中发生错误。
echo 请查看上面的错误信息并尝试解决问题。
) else (
    echo.
echo =======================================================
echo 打包完成！
echo.
echo 您可以在 dist 目录中找到 StoryGenerator.exe 文件。
echo 使用前请确保在同一目录下创建 config.json 配置文件。
echo =======================================================
)

echo.
pause