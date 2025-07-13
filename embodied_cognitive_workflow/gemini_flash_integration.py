"""
Gemini Flash 2.5 集成模块

本模块已升级为使用 pythonTask 中定义的 Gemini Flash 2.5 模型。
提供智能断点条件评估和异步bug检测功能。

升级说明：
- 从 Google generativeai 库迁移到基于 ChatOpenAI 的实现
- 使用 pythonTask 中预配置的 get_model("gemini_2_5_flash") 模型
- 保持原有 API 接口不变，确保向后兼容性
- 支持中国大陆用户的网络环境配置

要求：
- 设置 GEMINI_API_KEY 环境变量
- 确保 pythonTask 模块可正常导入
- 网络能够访问 Google API（或配置代理）
"""

import os
import asyncio
import json
import logging
import sys
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

# 导入 pythonTask 中的 Gemini Flash 2.5 模型
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from llm_lazy import get_model
    llm_gemini_2_5_flash_google = get_model("gemini_2_5_flash")
except ImportError:
    # 如果导入失败，设置为 None
    llm_gemini_2_5_flash_google = None


@dataclass
class GeminiConfig:
    """Gemini Flash 2.5 配置"""
    api_key: str
    model_name: str = "models/gemini-2.5-flash"
    temperature: float = 0.1
    max_output_tokens: int = 1000
    timeout: float = 10.0


class GeminiFlashClient:
    """Gemini Flash 2.5 客户端（基于 pythonTask 模型）"""
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        """
        初始化 Gemini Flash 2.5 客户端
        
        Args:
            config: Gemini配置（可选，将使用 pythonTask 中的默认配置）
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 检查是否成功导入了 pythonTask 模型
        if get_model("gemini_2_5_flash") is None:
            raise ImportError("无法导入 pythonTask 中的 Gemini Flash 2.5 模型")
        
        # 使用 pythonTask 中预配置的模型
        self.model = get_model("gemini_2_5_flash")
        
        # 检查环境变量
        if not os.getenv('GEMINI_API_KEY'):
            self.logger.warning("未设置 GEMINI_API_KEY 环境变量，Gemini Flash 2.5 可能无法正常工作")
        
        self.logger.info(f"Gemini Flash 2.5 客户端初始化完成：基于 pythonTask 模型")
    
    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        生成内容
        
        Args:
            prompt: 输入提示
            **kwargs: 额外参数
            
        Returns:
            str: 生成的内容
        """
        try:
            # 使用 ChatOpenAI 接口
            response = self.model.invoke(prompt)
            return response.content
            
        except Exception as e:
            self.logger.error(f"Gemini Flash 2.5 内容生成失败: {e}")
            raise
    
    async def generate_content_async(self, prompt: str, **kwargs) -> str:
        """
        异步生成内容
        
        Args:
            prompt: 输入提示
            **kwargs: 额外参数
            
        Returns:
            str: 生成的内容
        """
        try:
            # 使用 ChatOpenAI 的异步接口
            response = await self.model.ainvoke(prompt)
            return response.content
            
        except Exception as e:
            self.logger.error(f"Gemini Flash 2.5 异步内容生成失败: {e}")
            raise
    
    def evaluate_breakpoint_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        评估断点条件
        
        Args:
            condition: 断点条件（自然语言）
            context: 当前上下文
            
        Returns:
            bool: 条件是否满足
        """
        try:
            prompt = f"""
            请评估以下断点条件是否在当前上下文中满足。
            
            断点条件: {condition}
            
            当前上下文:
            {json.dumps(context, ensure_ascii=False, indent=2)}
            
            评估规则:
            1. 仔细分析断点条件的语义
            2. 检查上下文中是否存在满足条件的数据
            3. 只有当条件完全匹配时才返回true
            
            请只返回 'true' 或 'false'，不要其他任何文字。
            """
            
            response = self.generate_content(prompt)
            result = response.strip().lower()
            
            # 确保返回值只是true或false
            if result in ['true', 'false']:
                return result == 'true'
            else:
                self.logger.warning(f"意外的断点评估结果: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"断点条件评估失败: {e}")
            return False
    
    def analyze_bug_potential(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析潜在的bug
        
        Args:
            step_data: 认知步骤数据
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            prompt = f"""
分析以下认知步骤是否存在软件缺陷。

步骤数据: {json.dumps(step_data, ensure_ascii=False)}

分析要点:
- 检查错误和异常
- 评估执行时间(>3秒为异常)
- 检查数据合理性

请严格按以下JSON格式回复，不要包含任何其他文字:

{{
  "has_bug": false,
  "severity": "low",
  "bug_type": "unknown", 
  "description": "正常执行",
  "evidence": "无异常",
  "fix_suggestion": "无需修复"
}}
            """
            
            response = self.generate_content(prompt)
            
            # 智能解析JSON响应
            analysis = self._parse_json_response(response)
            
            # 验证必需字段
            required_fields = ['has_bug', 'severity', 'description']
            if all(field in analysis for field in required_fields):
                return analysis
            else:
                self.logger.warning("Bug分析结果缺少必需字段")
                return self._create_default_analysis()
                
        except Exception as e:
            self.logger.error(f"Bug潜力分析失败: {e}")
            return self._create_default_analysis()
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        智能解析JSON响应，处理包含markdown代码块的情况
        
        Args:
            response: 原始响应
            
        Returns:
            Dict[str, Any]: 解析后的JSON对象，失败时返回默认分析
        """
        try:
            # 第一步：尝试直接解析
            cleaned_response = response.strip()
            return json.loads(cleaned_response)
            
        except json.JSONDecodeError:
            try:
                # 第二步：移除markdown代码块标记
                import re
                
                # 移除 ```json 和 ``` 标记
                pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                
                if match:
                    json_content = match.group(1).strip()
                    self.logger.debug(f"提取到的JSON内容: {json_content}")
                    return json.loads(json_content)
                
                # 第三步：寻找任何JSON对象
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_content = json_match.group().strip()
                    self.logger.debug(f"通过正则提取的JSON: {json_content}")
                    return json.loads(json_content)
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {e}")
                self.logger.debug(f"原始响应: {response}")
            
        except Exception as e:
            self.logger.error(f"响应解析异常: {e}")
        
        # 如果所有方法都失败，返回默认分析
        self.logger.warning("无法解析响应，返回默认分析结果")
        return self._create_default_analysis()
    
    def _create_default_analysis(self) -> Dict[str, Any]:
        """创建默认分析结果"""
        return {
            "has_bug": False,
            "severity": "low",
            "bug_type": "unknown",
            "description": "分析失败",
            "evidence": "无法完成分析",
            "fix_suggestion": "需要人工检查"
        }
    
    async def analyze_bug_potential_async(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步分析潜在的bug
        
        Args:
            step_data: 认知步骤数据
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            prompt = f"""
            请快速分析以下认知步骤是否存在缺陷:
            
            {json.dumps(step_data, ensure_ascii=False)}
            
            返回JSON格式: {{"has_bug": bool, "severity": "level", "description": "desc"}}
            """
            
            response = await self.generate_content_async(prompt)
            
            try:
                return json.loads(response.strip())
            except json.JSONDecodeError:
                return self._create_default_analysis()
                
        except Exception as e:
            self.logger.error(f"异步Bug分析失败: {e}")
            return self._create_default_analysis()
    
    def generate_cognitive_strategy(self, task_description: str, 
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成认知策略建议
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 策略建议
        """
        try:
            prompt = f"""
            请为以下任务生成最优的认知策略:
            
            任务: {task_description}
            上下文: {json.dumps(context, ensure_ascii=False, indent=2)}
            
            请分析并提供:
            1. 任务复杂度评估 (1-10)
            2. 建议的执行策略
            3. 预期的挑战和风险
            4. 成功指标
            
            以JSON格式返回:
            {{
                "complexity": number,
                "strategy": "策略描述",
                "challenges": ["挑战1", "挑战2"],
                "success_metrics": ["指标1", "指标2"],
                "estimated_time": "预估时间",
                "resource_requirements": "资源需求"
            }}
            """
            
            response = self.generate_content(prompt)
            
            try:
                return json.loads(response.strip())
            except json.JSONDecodeError:
                return {
                    "complexity": 5,
                    "strategy": "标准执行策略",
                    "challenges": ["未知挑战"],
                    "success_metrics": ["任务完成"],
                    "estimated_time": "中等",
                    "resource_requirements": "标准资源"
                }
                
        except Exception as e:
            self.logger.error(f"认知策略生成失败: {e}")
            return {"complexity": 5, "strategy": "默认策略"}
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 客户端是否正常工作
        """
        try:
            test_prompt = "请回复'OK'"
            response = self.generate_content(test_prompt)
            return "ok" in response.lower()
            
        except Exception as e:
            self.logger.error(f"Gemini Flash 2.5 健康检查失败: {e}")
            return False


def create_gemini_client(api_key: Optional[str] = None, 
                        model_name: str = "models/gemini-2.5-flash") -> Optional[GeminiFlashClient]:
    """
    创建 Gemini Flash 2.5 客户端（基于 pythonTask 模型）
    
    Args:
        api_key: API密钥，如果为None则从环境变量获取（可选，pythonTask已处理）
        model_name: 模型名称（可选，将使用pythonTask的默认配置）
        
    Returns:
        Optional[GeminiFlashClient]: 客户端实例，失败时返回None
    """
    try:
        # 检查是否有 pythonTask 模型
        if get_model("gemini_2_5_flash") is None:
            logging.error("无法导入 pythonTask 中的 Gemini Flash 2.5 模型")
            return None
        
        # 检查API密钥
        if not os.getenv('GEMINI_API_KEY'):
            logging.warning("未找到 GEMINI_API_KEY 环境变量，Gemini Flash 2.5 可能无法正常工作")
        
        # 创建配置（可选，主要用于兼容性）
        config = GeminiConfig(
            api_key=api_key or os.getenv('GEMINI_API_KEY', ''),
            model_name=model_name
        )
        
        # 创建客户端
        client = GeminiFlashClient(config)
        
        # 健康检查
        if client.health_check():
            logging.info("Gemini Flash 2.5 客户端创建成功（基于 pythonTask 模型）")
            return client
        else:
            logging.error("Gemini Flash 2.5 客户端健康检查失败")
            return None
            
    except Exception as e:
        logging.error(f"创建 Gemini Flash 2.5 客户端失败: {e}")
        return None


# 示例用法
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Gemini Flash 2.5 集成测试（基于 pythonTask 模型）")
    print("=" * 60)
    
    # 创建客户端
    print("1. 创建 Gemini Flash 2.5 客户端...")
    client = create_gemini_client()
    
    if client:
        print("✅ Gemini Flash 2.5 客户端创建成功")
        
        # 测试断点条件评估
        print("\n2. 测试断点条件评估...")
        test_context = {
            "layer": "自我",
            "action": "执行代码",
            "success": False,
            "error_message": "语法错误"
        }
        
        condition = "如果执行失败并且包含语法错误"
        result = client.evaluate_breakpoint_condition(condition, test_context)
        print(f"   断点条件: '{condition}'")
        print(f"   评估结果: {result}")
        
        # 测试bug分析
        print("\n3. 测试Bug分析...")
        step_data = {
            "step_id": "test_step",
            "layer": "自我",
            "success": False,
            "error_message": "未定义变量",
            "execution_time": 5.0
        }
        
        bug_analysis = client.analyze_bug_potential(step_data)
        print("   Bug分析结果:")
        print(json.dumps(bug_analysis, ensure_ascii=False, indent=4))
        
        print("\n✅ 所有测试完成")
        
    else:
        print("❌ Gemini Flash 2.5 客户端创建失败")
        print("   可能的原因：")
        print("   - 未设置 GEMINI_API_KEY 环境变量")
        print("   - 网络无法访问 Google API 服务")
        print("   - pythonTask 模块导入失败")