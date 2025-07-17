#!/usr/bin/env python3
"""
使用内观评估模式实现加减乘除计算器的演示
"""

import os
import sys
import time
from datetime import datetime

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加父目录到系统路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 导入必要的模块
try:
    from python_core import *
from llm_lazy import get_model
    from embodied_cognitive_workflow import CognitiveAgent
    
    # 使用Gemini模型
    llm_gemini = \1("gemini_2_5_flash")
    
    print("✅ 所有模块导入成功！")
    print("🧮 使用内观评估模式实现计算器")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)

def main():
    """主函数：使用内观评估模式创建计算器"""
    print("🧮 内观评估模式计算器演示")
    print("="*80)
    
    # 创建使用内观评估的认知代理
    agent = CognitiveAgent(
        llm=llm_gemini,
        max_cycles=10,
        verbose=True,
        enable_meta_cognition=True,
        evaluation_mode="internal"  # 关键：设置为内观评估模式
    )
    
    print(f"🔧 评估模式: {agent.id_agent.evaluation_mode}")
    print(f"⏱️ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 计算器开发任务
    calculator_task = """
    创建一个完整的Python计算器程序，实现以下功能：
    
    1. 基本运算功能：
       - 加法 (add)
       - 减法 (subtract)  
       - 乘法 (multiply)
       - 除法 (divide)
    
    2. 错误处理：
       - 除零错误处理
       - 无效输入处理
    
    3. 用户界面：
       - 命令行交互界面
       - 清晰的操作提示
       - 循环执行直到用户选择退出
    
    4. 代码质量：
       - 函数模块化设计
       - 适当的注释说明
       - 简单的测试用例
    
    请将完整的计算器程序保存到文件：
    /home/guci/aiProjects/AgentFrameWork/internal_evaluation_calculator.py
    
    程序应该能够直接运行，提供用户友好的交互体验。
    """
    
    start_time = time.time()
    
    try:
        print("🚀 开始使用内观评估模式创建计算器...")
        print("📋 任务描述:")
        print("   - 实现加减乘除基本运算")
        print("   - 包含错误处理和用户界面")
        print("   - 使用内观评估模式进行任务完成判断")
        print("\n" + "="*80)
        
        # 执行计算器创建任务
        result = agent.execute_sync(calculator_task)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print("="*80)
        print(f"✅ 计算器创建完成!")
        print(f"⏱️ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕒 总执行时间: {execution_time:.2f}秒")
        print(f"✅ 任务成功: {result.success if result else False}")
        
        if result and result.return_value:
            print(f"📝 执行结果摘要:")
            print(f"   {result.return_value}")
        
        # 检查生成的计算器文件
        calculator_file = "/home/guci/aiProjects/AgentFrameWork/internal_evaluation_calculator.py"
        if os.path.exists(calculator_file):
            print(f"\n📁 计算器文件已生成: {calculator_file}")
            
            # 显示文件信息
            file_size = os.path.getsize(calculator_file)
            print(f"   📊 文件大小: {file_size} 字节")
            
            # 显示文件部分内容
            with open(calculator_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"   📄 文件行数: {len(lines)}")
                print(f"   📋 文件内容预览:")
                for i, line in enumerate(lines[:15], 1):
                    print(f"      {i:2d}: {line}")
                if len(lines) > 15:
                    print(f"      ... (还有{len(lines)-15}行)")
            
            # 尝试运行计算器（非交互模式验证）
            try:
                print(f"\n🧪 验证计算器功能...")
                # 简单的语法检查
                compile(content, calculator_file, 'exec')
                print("   ✅ 语法检查通过")
                
                # 检查关键函数是否存在
                key_functions = ['add', 'subtract', 'multiply', 'divide']
                found_functions = []
                for func in key_functions:
                    if f"def {func}(" in content:
                        found_functions.append(func)
                
                print(f"   🔍 发现的函数: {found_functions}")
                
                if len(found_functions) == 4:
                    print("   ✅ 所有基本运算函数都已实现")
                else:
                    print(f"   ⚠️ 缺少函数: {set(key_functions) - set(found_functions)}")
                
                # 检查错误处理
                if "除零" in content or "zero" in content.lower():
                    print("   ✅ 包含除零错误处理")
                else:
                    print("   ⚠️ 未发现除零错误处理")
                
                # 检查用户界面
                if "input(" in content:
                    print("   ✅ 包含用户交互界面")
                else:
                    print("   ⚠️ 未发现用户交互界面")
                
            except SyntaxError as e:
                print(f"   ❌ 语法错误: {e}")
            except Exception as e:
                print(f"   ⚠️ 验证过程中出现问题: {e}")
        
        else:
            print(f"\n❌ 计算器文件未生成: {calculator_file}")
        
        # 内观评估模式的特点分析
        print(f"\n🔍 内观评估模式的特点:")
        print(f"   ✅ 基于工作流内部状态进行评估")
        print(f"   ✅ 无需外部观察和验证步骤")
        print(f"   ✅ 减少了LLM调用和执行时间")
        print(f"   ✅ 提高了评估的可靠性")
        print(f"   ✅ 与认知循环完全兼容")
        
        return {
            "success": result.success if result else False,
            "execution_time": execution_time,
            "file_created": os.path.exists(calculator_file),
            "evaluation_mode": "internal"
        }
        
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"❌ 计算器创建失败: {e}")
        print(f"🕒 执行时间: {execution_time:.2f}秒")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "execution_time": execution_time,
            "file_created": False,
            "evaluation_mode": "internal",
            "error": str(e)
        }

if __name__ == "__main__":
    print("🎯 这个演示将展示内观评估模式的实际应用")
    print("💡 内观评估直接基于工作流状态，无需外部验证")
    print("🚀 让我们看看内观评估如何高效完成计算器开发任务")
    print()
    
    result = main()
    
    print(f"\n🎊 内观评估计算器演示完成!")
    print(f"📊 结果总结:")
    print(f"   成功状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
    print(f"   执行时间: {result['execution_time']:.2f}秒")
    print(f"   文件创建: {'✅ 已创建' if result['file_created'] else '❌ 未创建'}")
    print(f"   评估模式: {result['evaluation_mode']}")
    
    if result.get('error'):
        print(f"   错误信息: {result['error']}")
    
    print(f"\n💡 内观评估的优势:")
    print(f"   - 基于工作流内部状态，更加可靠")
    print(f"   - 减少外部依赖，提高执行效率")
    print(f"   - 简化评估流程，缩短响应时间")
    print(f"   - 保持与认知循环的完全兼容性")