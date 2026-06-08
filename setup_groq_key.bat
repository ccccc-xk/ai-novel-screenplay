@echo off
echo ==========================================
echo   Groq API Key 设置工具
echo ==========================================
echo.
echo 1. 打开 https://console.groq.com 注册免费账号
echo 2. 进入 API Keys 页面，创建一个Key
echo 3. 复制Key，粘贴到下面
echo.
set /p GROQ_KEY="请粘贴你的 Groq API Key: "

echo.
echo 正在设置环境变量...

:: 设置用户级环境变量（永久生效）
setx GROQ_API_KEY "%GROQ_KEY%"

echo.
echo ✅ 设置完成！
echo    环境变量 GROQ_API_KEY 已保存
echo    请重启应用服务器使其生效
echo.
pause
