from interpreter import interpreter

# --- 核心配置修正区域 ---

# 1. 强制指定模型
interpreter.llm.model = "ollama/qwen2.5:32b"

# 2. 强制关闭函数调用（解决 JSON 问题）
interpreter.llm.supports_functions = False 

# 3. 强制本地离线模式
interpreter.offline = True

# 4. 【新加入】开启全自动模式（不再问 y/n）
interpreter.auto_run = True

# 5. 植入防呆系统提示词
interpreter.system_message = """
你是一个精通 Python 的全能电脑助手。
目前的配置已禁用 Function Calling。
任何操作请务必直接输出 ```python 代码块。
不要解释，不要输出 JSON，直接写代码。
"""

# --- 启动对话 ---
print(">>> 全自动模式已开启 (Auto-Run ON)...")
interpreter.chat()