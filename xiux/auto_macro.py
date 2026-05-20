import keyboard
import pydirectinput
import time
import threading
import datetime
import ctypes
import sys

# 全局变量，用于控制脚本的运行状态
running = False

def is_admin():
    """检查管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def log_action(action_message):
    """在控制台打印记录"""
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {action_message}", flush=True)

def interruptible_sleep(seconds):
    """可中断的休眠函数"""
    end_time = time.time() + seconds
    while time.time() < end_time:
        if not running:
            return False 
        time.sleep(0.1)
    return True

def press_game_key(key_name, duration=0.1):
    """
    为 3D 全屏环境专门设计的按键函数。
    模拟真实的按下、保持、抬起过程。
    """
    pydirectinput.keyDown(key_name)
    time.sleep(duration)
    pydirectinput.keyUp(key_name)

def macro_sequence():
    """自动化的核心循环逻辑"""
    global running
    while running:
        # 1. 按左键一次
        pydirectinput.click(button='left')
        
        # 2. 等待 1分40秒 (100秒) - [已修改]
        if not interruptible_sleep(100): break
        
        # 3. 按空格一次
        press_game_key('space')
        
        # 4. 等待 5 秒钟 - [已修改]
        if not interruptible_sleep(5): break
        
        # 5. 按 F 一次
        press_game_key('f')
        
        # 6. 等待 5 秒钟 - [已修改]
        if not interruptible_sleep(5): break

def start_macro():
    """按下 F10 时触发：启动自动化"""
    global running
    if not running:
        running = True
        log_action("▶ [F10] 触发：已开始执行自动点击与按键操作。")
        threading.Thread(target=macro_sequence, daemon=True).start()

def stop_macro():
    """按下 F12 时触发：立刻停止当前操作"""
    global running
    if running:
        running = False
        log_action("⏹ [F12] 触发：已立刻停止当前的操作循环。等待下次启动。")

# ================= 程序的启动入口 =================
if __name__ == "__main__":
    # 检查并自动获取管理员权限
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
        
    print("=======================================")
    print(" 自动化程序已启动 (已自动获取管理员权限)！")
    print(" [F10] - 开始执行点击和按键循环")
    print(" [F12] - 停止当前的操作循环")
    print("=======================================")
    log_action("程序就绪，等待快捷键指令...")
    
    keyboard.add_hotkey('F10', start_macro)
    keyboard.add_hotkey('F12', stop_macro)
    keyboard.wait()