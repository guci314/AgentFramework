#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成示例：在enhancedAgent_v2.py中使用新的多方案ResponseParser

这个示例展示如何将新的response_parser_v2.py集成到现有的框架中
"""

import logging
from typing import Dict, Any, Optional
from response_parser_v2 import (
    ParserFactory, ParserMethod, ParserConfig,
    MultiMethodResponseParser, ParsedStateInfo
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedAgentWithNewParser:
    """集成新解析器的增强智能体示例"""
    
    def __init__(self, parser_method: str = "rule", **parser_kwargs):
        """
        初始化智能体
        
        Args:
            parser_method: 解析方法 ("rule", "transformer", "deepseek", "embedding")
            **parser_kwargs: 解析器的其他参数
        """
        self.logger = logging.getLogger(f"{__name__}.EnhancedAgentWithNewParser")
        
        # 创建解析器
        self.response_parser = self._create_parser(parser_method, **parser_kwargs)
        
        # 模拟工作流状态
        self.workflow_state = {
            "current_step": "初始化",
            "execution_history": [],
            "global_variables": {}
        }
        
        self.logger.info(f"智能体初始化完成，使用 {parser_method} 解析器")
    
    def _create_parser(self, method: str, **kwargs) -> MultiMethodResponseParser:
        """创建解析器实例"""
        if method == "rule":
            return ParserFactory.create_rule_parser(**kwargs)
        elif method == "transformer":
            return ParserFactory.create_transformer_parser(**kwargs)
        elif method == "deepseek":
            api_key = kwargs.get('api_key') or "your_deepseek_api_key"
            return ParserFactory.create_deepseek_parser(api_key=api_key, **kwargs)
        elif method == "embedding":
            return ParserFactory.create_embedding_parser(**kwargs)
        elif method == "hybrid":
            primary_method = kwargs.pop('primary_method', ParserMethod.RULE)
            fallback_chain = kwargs.pop('fallback_chain', [ParserMethod.RULE])
            return ParserFactory.create_hybrid_parser(
                primary_method=primary_method,
                fallback_chain=fallback_chain,
                **kwargs
            )
        else:
            self.logger.warning(f"未知解析方法 {method}，使用默认规则解析器")
            return ParserFactory.create_rule_parser()
    
    def execute_step(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行步骤并解析响应
        
        Args:
            instruction: 执行指令
            context: 执行上下文
            
        Returns:
            执行结果字典
        """
        self.logger.info(f"执行步骤: {instruction}")
        
        # 模拟执行过程
        if "错误" in instruction or "失败" in instruction:
            response = f"执行指令时发生错误: {instruction}"
            execution_success = False
        elif "创建" in instruction or "生成" in instruction:
            response = f"成功创建了相关资源，指令: {instruction}"
            execution_success = True
        elif "查询" in instruction or "检查" in instruction:
            response = f"查询完成，状态正常，指令: {instruction}"
            execution_success = True
        else:
            response = f"正在处理指令: {instruction}，请稍候..."
            execution_success = None  # 进行中
        
        # 使用新解析器分析响应
        parsed_result = self.response_parser.parse_response(response, context)
        
        # 构建执行结果
        result = {
            "instruction": instruction,
            "raw_response": response,
            "execution_success": execution_success,
            "parsed_info": {
                "main_content": parsed_result.main_content,
                "status_type": parsed_result.extracted_entities.get('status_type'),
                "sentiment": parsed_result.sentiment,
                "intent": parsed_result.intent,
                "confidence_score": parsed_result.confidence_score,
                "quality": parsed_result.quality_metrics.get('overall_quality')
            },
            "entities": parsed_result.extracted_entities,
            "timestamp": "2024-06-21T10:00:00Z"
        }
        
        # 更新工作流状态
        self._update_workflow_state(result)
        
        self.logger.info(f"步骤执行完成，置信度: {parsed_result.confidence_score:.2f}")
        
        return result
    
    def _update_workflow_state(self, execution_result: Dict[str, Any]):
        """更新工作流状态"""
        status_type = execution_result["parsed_info"]["status_type"]
        
        if status_type == "success":
            self.workflow_state["current_step"] = "成功完成"
        elif status_type == "error":
            self.workflow_state["current_step"] = "错误处理"
        elif status_type == "progress":
            self.workflow_state["current_step"] = "执行中"
        else:
            self.workflow_state["current_step"] = "待定"
        
        # 添加到执行历史
        self.workflow_state["execution_history"].append({
            "step": execution_result["instruction"],
            "status": status_type,
            "confidence": execution_result["parsed_info"]["confidence_score"],
            "timestamp": execution_result["timestamp"]
        })
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        parser_stats = self.response_parser.get_stats()
        
        return {
            "current_step": self.workflow_state["current_step"],
            "total_steps": len(self.workflow_state["execution_history"]),
            "parser_stats": parser_stats,
            "recent_steps": self.workflow_state["execution_history"][-3:]  # 最近3步
        }
    
    def demonstrate_natural_language_state(self) -> str:
        """演示自然语言状态描述"""
        status = self.get_workflow_status()
        
        if not status["recent_steps"]:
            return "工作流尚未开始执行任何步骤。"
        
        recent_step = status["recent_steps"][-1]
        step_status = recent_step["status"]
        confidence = recent_step["confidence"]
        
        if step_status == "success":
            state_desc = f"最近成功完成了'{recent_step['step']}'步骤，系统运行良好。"
        elif step_status == "error":
            state_desc = f"在执行'{recent_step['step']}'时遇到问题，需要进一步处理。"
        elif step_status == "progress":
            state_desc = f"正在执行'{recent_step['step']}'，进展顺利。"
        else:
            state_desc = f"'{recent_step['step']}'的执行状态待确认。"
        
        state_desc += f" (解析置信度: {confidence:.1%})"
        
        return state_desc


def demo_integration():
    """演示集成效果"""
    print("=== 新解析器集成演示 ===\n")
    
    # 测试不同解析器
    parser_configs = [
        ("规则解析器", "rule", {}),
        ("混合解析器", "hybrid", {
            "primary_method": ParserMethod.RULE,
            "fallback_chain": [ParserMethod.RULE],
            "confidence_threshold": 0.8
        })
    ]
    
    for parser_name, method, config in parser_configs:
        print(f"--- 使用 {parser_name} ---")
        
        # 创建智能体
        agent = EnhancedAgentWithNewParser(parser_method=method, **config)
        
        # 执行一系列步骤
        test_instructions = [
            "创建新的配置文件",
            "查询数据库连接状态", 
            "执行数据备份操作",
            "模拟一个错误情况",
            "检查系统整体状态"
        ]
        
        for instruction in test_instructions:
            result = agent.execute_step(instruction)
            parsed_info = result["parsed_info"]
            
            print(f"指令: {instruction}")
            print(f"  状态: {parsed_info['status_type']} | 情感: {parsed_info['sentiment']} | 置信度: {parsed_info['confidence_score']:.2f}")
            print(f"  解析结果: {parsed_info['main_content']}")
        
        # 显示工作流状态
        print(f"\n工作流状态:")
        status = agent.get_workflow_status()
        print(f"  当前步骤: {status['current_step']}")
        print(f"  总步骤数: {status['total_steps']}")
        print(f"  解析器统计: {status['parser_stats']}")
        
        # 自然语言状态描述
        nl_state = agent.demonstrate_natural_language_state()
        print(f"  自然语言描述: {nl_state}")
        
        print()


def demo_comparison():
    """演示不同解析器的效果对比"""
    print("=== 解析器效果对比 ===\n")
    
    test_responses = [
        "文件上传成功，共处理了1000个记录。",
        "连接超时，无法访问远程服务器。", 
        "正在分析数据，预计需要5分钟时间。",
        "请提供管理员权限以继续操作。"
    ]
    
    parser_methods = ["rule"]  # 只测试可用的方法
    
    for response in test_responses:
        print(f"测试响应: {response}")
        
        for method in parser_methods:
            agent = EnhancedAgentWithNewParser(parser_method=method)
            result = agent.response_parser.parse_response(response)
            
            print(f"  {method}解析器:")
            print(f"    状态: {result.extracted_entities.get('status_type')}")
            print(f"    情感: {result.sentiment}")
            print(f"    意图: {result.intent}")
            print(f"    置信度: {result.confidence_score:.3f}")
        
        print()


if __name__ == "__main__":
    # 运行演示
    demo_integration()
    demo_comparison()
    
    print("=== 集成演示完成 ===")
    print("✅ 新解析器已成功集成到智能体框架中")
    print("🔧 可通过配置参数选择不同的解析方法")
    print("📊 支持实时统计和性能监控")
    print("🎯 提供了完整的降级和容错机制")