#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Chat Bridge OCR 安装脚本
"""

import sys
import subprocess
import os
import platform
from pathlib import Path

def print_header():
    """打印标题"""
    print("=" * 60)
    print("🤖 AI Chat Bridge OCR - 安装脚本")
    print("=" * 60)
    print()

def check_python_version():
    """检查Python版本"""
    print("📋 检查Python版本...")
    version = sys.version_info
    print(f"   当前版本: Python {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print("   请升级Python后重新运行此脚本")
        return False
    else:
        print("✅ Python版本检查通过")
        return True

def install_python_packages():
    """安装Python包"""
    print("\n📦 安装Python依赖包...")
    
    packages = [
        "pillow>=9.0.0",
        "pytesseract>=0.3.10", 
        "pyautogui>=0.9.54",
        "opencv-python>=4.5.0",
        "easyocr>=1.6.0",
        "numpy>=1.21.0",
        "pyperclip>=1.8.0"
    ]
    
    failed_packages = []
    
    for package in packages:
        try:
            print(f"   安装 {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"   ✅ {package} 安装成功")
        except subprocess.CalledProcessError:
            print(f"   ❌ {package} 安装失败")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n❌ 以下包安装失败: {', '.join(failed_packages)}")
        print("   请手动安装: pip install " + " ".join(failed_packages))
        return False
    else:
        print("\n✅ 所有Python包安装成功")
        return True

def install_tesseract():
    """安装Tesseract OCR"""
    print("\n🔍 检查Tesseract OCR...")
    
    # 检查是否已安装
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✅ Tesseract OCR 已安装并可用")
        return True
    except:
        pass
    
    system = platform.system().lower()
    
    print("❌ Tesseract OCR 未安装或不可用")
    print("\n📥 Tesseract OCR 安装指南:")
    
    if system == "windows":
        print("   Windows用户:")
        print("   1. 访问: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   2. 下载并安装 tesseract-ocr-w64-setup-v5.x.x.exe")
        print("   3. 安装时选择中文语言包")
        print("   4. 将安装目录添加到系统PATH环境变量")
        
    elif system == "darwin":  # macOS
        print("   macOS用户:")
        print("   1. 安装Homebrew (如果未安装): /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("   2. 运行: brew install tesseract")
        print("   3. 安装中文语言包: brew install tesseract-lang")
        
    elif system == "linux":
        print("   Linux用户:")
        print("   Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim")
        print("   CentOS/RHEL: sudo yum install tesseract tesseract-langpack-chi_sim")
        print("   Arch Linux: sudo pacman -S tesseract tesseract-data-chi_sim")
        
    print("\n💡 提示: 如果不想安装Tesseract，程序会自动使用EasyOCR引擎")
    return False

def create_directories():
    """创建必要的目录"""
    print("\n📁 创建项目目录...")
    
    directories = [
        "data",
        "logs", 
        "screenshots",
        "exports"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            print(f"   ✅ 创建目录: {directory}")
        except Exception as e:
            print(f"   ❌ 创建目录失败 {directory}: {e}")
            return False
            
    return True

def test_installation():
    """测试安装"""
    print("\n🧪 测试安装...")
    
    # 测试导入
    test_packages = [
        ("PIL", "Pillow"),
        ("pytesseract", "pytesseract"),
        ("pyautogui", "pyautogui"),
        ("cv2", "opencv-python"),
        ("numpy", "numpy"),
        ("pyperclip", "pyperclip")
    ]
    
    failed_imports = []
    
    for module, package in test_packages:
        try:
            __import__(module)
            print(f"   ✅ {package} 导入成功")
        except ImportError:
            print(f"   ❌ {package} 导入失败")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\n❌ 以下包导入失败: {', '.join(failed_imports)}")
        return False
    
    # 测试OCR引擎
    ocr_available = False
    
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("   ✅ Tesseract OCR 可用")
        ocr_available = True
    except:
        print("   ⚠️ Tesseract OCR 不可用")
    
    try:
        import easyocr
        print("   ✅ EasyOCR 可用")
        ocr_available = True
    except:
        print("   ⚠️ EasyOCR 不可用")
    
    if not ocr_available:
        print("   ❌ 没有可用的OCR引擎")
        return False
    
    print("\n✅ 安装测试通过")
    return True

def show_next_steps():
    """显示后续步骤"""
    print("\n🎉 安装完成!")
    print("\n📋 后续步骤:")
    print("   1. 运行测试: python test_run.py")
    print("   2. 启动程序: python main.py")
    print("   3. 或使用启动器: python run.py")
    print("\n📖 使用指南:")
    print("   - 查看快速开始: QUICKSTART_CN.md")
    print("   - 查看完整文档: README.md")
    print("\n⚠️ 重要提示:")
    print("   - 首次使用前请阅读使用指南")
    print("   - 确保已登录要使用的AI聊天平台")
    print("   - 选择区域时要包含聊天内容和输入框")

def main():
    """主函数"""
    print_header()
    
    # 检查Python版本
    if not check_python_version():
        input("\n按回车键退出...")
        return
    
    # 安装Python包
    if not install_python_packages():
        print("\n❌ Python包安装失败，请检查网络连接或手动安装")
        input("按回车键退出...")
        return
    
    # 检查Tesseract
    install_tesseract()
    
    # 创建目录
    if not create_directories():
        print("\n❌ 目录创建失败")
        input("按回车键退出...")
        return
    
    # 测试安装
    if not test_installation():
        print("\n❌ 安装测试失败，请检查错误信息")
        input("按回车键退出...")
        return
    
    # 显示后续步骤
    show_next_steps()
    
    print("\n" + "=" * 60)
    input("按回车键退出...")

if __name__ == "__main__":
    main()
