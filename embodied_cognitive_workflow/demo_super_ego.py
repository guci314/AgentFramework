#!/usr/bin/env python3
"""
超我智能体演示程序

展示超我智能体的元认知监督、认知错误检测、UltraThink能力和四层认知架构集成的完整功能。

功能演示：
1. 超我智能体基础功能
2. 认知偏差检测和逻辑验证
3. UltraThink元认知引擎
4. 四层认知架构集成
5. 实时认知监控和策略优化
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from langchain_openai import ChatOpenAI
    from embodied_cognitive_workflow import SuperEgoAgent, CognitiveAgent
    print("✅ 成功导入具身认知工作流模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保已安装所需依赖：pip install langchain-openai")
    sys.exit(1)


class SuperEgoDemo:
    """超我智能体演示类"""
    
    def __init__(self):
        """初始化演示环境"""
        print("🚀 初始化超我智能体演示环境...")
        
        # 初始化语言模型（需要有效的API密钥）
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=2000
        )
        
        # 初始化超我智能体
        self.super_ego = SuperEgoAgent(
            llm=self.llm,
            enable_bias_detection=True,
            enable_logic_validation=True,
            enable_consistency_check=True,
            enable_moral_guidance=True,
            enable_ultra_think=True
        )
        
        print("✅ 超我智能体初始化完成")
        self.super_ego.start_cognitive_monitoring()
        print("📊 认知监控已启动")
    
    def demo_basic_supervision(self):
        """演示基础认知监督功能"""
        print("\n" + "="*60)
        print("🧠 演示1: 基础认知监督功能")
        print("="*60)
        
        # 模拟一段有偏差的推理
        biased_reasoning = """
        我们公司的销售额下降了，这肯定是因为竞争对手的恶意竞争。
        上个月我看到一篇文章说竞争对手在搞价格战，这证明了我的观点。
        我们应该立即降价来对抗他们，这是唯一的解决方案。
        """
        
        context = {
            "domain": "商业决策",
            "stakeholders": ["公司", "客户", "员工"],
            "initial_info": "销售额下降"
        }
        
        goals = ["分析销售下降原因", "制定应对策略"]
        actions = ["立即降价", "对抗竞争对手"]
        
        print("📝 分析推理文本:")
        print(biased_reasoning)
        print("\n🔍 开始认知监督...")
        
        result = self.super_ego.supervise_cognitive_process(
            reasoning_text=biased_reasoning,
            context=context,
            goals=goals,
            actions=actions
        )
        
        self._print_supervision_result(result)
    
    def demo_ultra_think_engine(self):
        """演示UltraThink元认知引擎"""
        print("\n" + "="*60)
        print("🤖 演示2: UltraThink元认知引擎")
        print("="*60)
        
        if not self.super_ego.ultra_think:
            print("❌ UltraThink引擎未启用")
            return
        
        # 模拟认知过程数据
        process_data = {
            "task": "项目风险评估",
            "complexity": "高",
            "execution_time": 15.5,
            "memory_usage": 0.7,
            "cpu_usage": 0.6,
            "token_usage": 0.8,
            "strategy": "系统性分析",
            "error_rate": 0.1
        }
        
        performance_metrics = {
            "execution_time": 15.5,
            "accuracy": 0.85,
            "resource_usage": 0.7
        }
        
        context = {
            "project_type": "AI系统开发",
            "timeline": "紧急",
            "team_size": 5
        }
        
        goals = ["识别关键风险", "制定缓解策略", "优化项目流程"]
        
        print("📊 执行元认知分析...")
        
        meta_analysis = self.super_ego.meta_cognitive_analysis(
            process_data=process_data,
            performance_metrics=performance_metrics,
            context=context,
            goals=goals
        )
        
        self._print_meta_analysis_result(meta_analysis)
    
    def demo_comprehensive_supervision(self):
        """演示综合认知监督"""
        print("\n" + "="*60)
        print("🔬 演示3: 综合认知监督")
        print("="*60)
        
        # 模拟复杂的认知数据
        cognitive_data = {
            "reasoning_text": "基于市场数据分析，我们需要调整产品策略...",
            "efficiency": 0.6,
            "accuracy": 0.9,
            "error_rate": 0.2,
            "actions": ["调整定价", "优化功能", "扩大市场"]
        }
        
        context = {
            "business_context": "产品策略调整",
            "market_conditions": "竞争激烈",
            "resources": "有限"
        }
        
        goals = ["提升竞争力", "增加市场份额", "保持盈利"]
        
        print("🧪 执行综合认知监督...")
        
        supervision_result = self.super_ego.comprehensive_cognitive_supervision(
            cognitive_data=cognitive_data,
            context=context,
            goals=goals
        )
        
        self._print_comprehensive_supervision_result(supervision_result)
    
    def demo_four_layer_integration(self):
        """演示四层认知架构集成"""
        print("\n" + "="*60)
        print("🏗️ 演示4: 四层认知架构集成")
        print("="*60)
        
        print("🔧 创建具有超我监督的认知智能体...")
        
        # 创建四层认知架构的智能体
        cognitive_agent = CognitiveAgent(
            llm=self.llm,
            enable_super_ego=True,
            super_ego_config={
                "enable_bias_detection": True,
                "enable_ultra_think": True
            },
            verbose=True
        )
        
        print("✅ 四层认知架构已创建")
        
        # 执行一个测试任务
        test_task = "分析如何提高团队协作效率，并给出具体的改进建议"
        
        print(f"\n📋 执行测试任务: {test_task}")
        print("🔄 开始执行...")
        
        result = cognitive_agent.execute_sync(test_task)
        
        print(f"\n📊 执行结果:")
        print(f"成功: {result.success}")
        if result.return_value:
            print(f"结果: {result.return_value[:200]}...")
        
        # 获取超我状态
        super_ego_state = cognitive_agent.get_super_ego_state()
        if super_ego_state.get('enabled'):
            print("\n🧠 超我监督状态:")
            cognitive_health = super_ego_state.get('cognitive_health', {})
            print(f"认知健康评分: {cognitive_health.get('overall_score', 'N/A'):.2f}")
            print(f"健康状态: {cognitive_health.get('status', 'N/A')}")
            
            strengths = cognitive_health.get('strengths', [])
            if strengths:
                print(f"认知优势: {', '.join(strengths[:3])}")
        
        print("✅ 四层架构演示完成")
    
    def demo_learning_and_reflection(self):
        """演示学习和反思功能"""
        print("\n" + "="*60)
        print("🎓 演示5: 学习和反思功能")
        print("="*60)
        
        # 模拟多个经验数据
        experiences = [
            {
                "task": "客户投诉处理",
                "approach": "主动倾听",
                "success": True,
                "outcome": "客户满意"
            },
            {
                "task": "团队冲突解决", 
                "approach": "忽视问题",
                "success": False,
                "outcome": "冲突加剧"
            },
            {
                "task": "项目进度管控",
                "approach": "定期检查",
                "success": True,
                "outcome": "按时完成"
            }
        ]
        
        print("📚 处理经验数据...")
        
        for i, exp in enumerate(experiences, 1):
            print(f"\n🔍 反思经验 {i}: {exp['task']}")
            
            experience_data = {
                "task_type": exp["task"],
                "strategy": exp["approach"],
                "context": "工作场景"
            }
            
            outcome = {
                "success": exp["success"],
                "result": exp["outcome"],
                "lessons": []
            }
            
            reflection = self.super_ego.reflect_and_learn(experience_data, outcome)
            
            if not reflection.get('error'):
                lessons = reflection.get('lessons_learned', [])
                if lessons:
                    print(f"💡 学习要点: {lessons[0]}")
                
                patterns = reflection.get('reusable_patterns', [])
                if patterns:
                    print(f"🔄 可复用模式: {patterns[0]}")
        
        # 生成学习总结
        print("\n📊 生成学习总结...")
        learning_summary = self.super_ego.get_learning_summary()
        
        if not learning_summary.get('error') and learning_summary.get('learning_patterns'):
            print("🎯 主要学习模式:")
            for pattern in learning_summary['learning_patterns'][:3]:
                print(f"  • {pattern}")
        
        print("✅ 学习反思演示完成")
    
    def _print_supervision_result(self, result: Dict[str, Any]):
        """打印监督结果"""
        print(f"\n📊 监督结果:")
        print(f"整体健康分数: {result.get('overall_health_score', 0):.2f}")
        
        biases = result.get('biases_detected', [])
        if biases:
            print(f"\n⚠️ 检测到认知偏差 ({len(biases)}个):")
            for bias in biases:
                print(f"  • {bias.bias_type.value}: {bias.evidence[:100]}...")
        
        logic_errors = result.get('logic_errors', [])
        if logic_errors:
            print(f"\n❌ 检测到逻辑错误 ({len(logic_errors)}个):")
            for error in logic_errors:
                print(f"  • {error.error_type.value}: {error.explanation[:100]}...")
        
        recommendations = result.get('recommendations', [])
        if recommendations:
            print(f"\n💡 改进建议:")
            for rec in recommendations:
                print(f"  • {rec}")
    
    def _print_meta_analysis_result(self, result: Dict[str, Any]):
        """打印元认知分析结果"""
        print(f"\n🧠 元认知分析结果:")
        
        monitoring = result.get('monitoring_result')
        if monitoring:
            print(f"认知效率: {monitoring.get('cognitive_efficiency', 0):.2f}")
            print(f"资源利用率: {monitoring.get('resource_utilization', 0):.2f}")
            
            recommendations = monitoring.get('recommendations', [])
            if recommendations:
                print(f"监控建议: {', '.join(recommendations)}")
        
        strategy = result.get('strategy_regulation')
        if strategy and not strategy.get('error'):
            print(f"策略评估: {strategy.get('strategy_assessment', 'N/A')}")
            if strategy.get('adjustment_needed'):
                print(f"推荐策略: {strategy.get('recommended_strategy', 'N/A')}")
        
        learning = result.get('meta_learning')
        if learning and not learning.get('error'):
            patterns = learning.get('success_patterns', [])
            if patterns:
                print(f"成功模式: {', '.join(patterns[:2])}")
    
    def _print_comprehensive_supervision_result(self, result: Dict[str, Any]):
        """打印综合监督结果"""
        print(f"\n🔍 综合监督结果:")
        
        assessment = result.get('overall_assessment')
        if assessment:
            print(f"认知健康等级: {assessment.get('cognitive_health_level', 'unknown')}")
            
            critical_issues = assessment.get('critical_issues', [])
            if critical_issues:
                print(f"关键问题: {', '.join(critical_issues)}")
            
            priority_recs = assessment.get('priority_recommendations', [])
            if priority_recs:
                print(f"优先建议: {', '.join(priority_recs)}")
        
        monitoring = result.get('real_time_monitoring')
        if monitoring:
            status = monitoring.get('cognitive_status', 'unknown')
            print(f"实时认知状态: {status}")
            
            alerts = monitoring.get('alerts', [])
            if alerts:
                print(f"警报数量: {len(alerts)}")
    
    def run_full_demo(self):
        """运行完整演示"""
        print("🎬 开始超我智能体完整功能演示")
        print("="*80)
        
        try:
            # 运行各个演示
            self.demo_basic_supervision()
            self.demo_ultra_think_engine() 
            self.demo_comprehensive_supervision()
            self.demo_four_layer_integration()
            self.demo_learning_and_reflection()
            
            # 显示最终状态
            print("\n" + "="*60)
            print("📈 最终超我状态报告")
            print("="*60)
            
            state = self.super_ego.get_supervision_summary()
            print(f"监督次数: {state['metrics']['total_supervisions']}")
            print(f"检测偏差: {state['metrics']['biases_detected']}")
            print(f"发现逻辑错误: {state['metrics']['logic_errors_found']}")
            print(f"一致性问题: {state['metrics']['consistency_issues']}")
            
            health = state.get('cognitive_health')
            if health:
                print(f"整体认知健康: {health.status.value} (评分: {health.overall_score:.2f})")
            
            print("\n🎉 超我智能体演示完成!")
            print("✨ 四层认知架构已成功实现元认知监督能力")
            
        except Exception as e:
            print(f"\n❌ 演示过程中出现错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    print("🧠 超我智能体 (SuperEgoAgent) 演示程序")
    print("基于具身认知理论的四层架构元认知监督系统")
    print("="*80)
    
    try:
        demo = SuperEgoDemo()
        demo.run_full_demo()
    except KeyboardInterrupt:
        print("\n\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"\n\n❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()