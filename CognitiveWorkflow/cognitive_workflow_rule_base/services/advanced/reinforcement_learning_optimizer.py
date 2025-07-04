# -*- coding: utf-8 -*-
"""
强化学习策略优化器

实现基于强化学习的策略优化系统，使用Q-learning、Policy Gradient、
Actor-Critic等算法来学习最优策略选择和参数调整策略。

Phase 3: Self-Learning Optimization 核心组件
"""

from typing import Dict, List, Any, Optional, Tuple, Callable
import logging
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import math
from dataclasses import dataclass, asdict
from enum import Enum
import random

from ...domain.value_objects import (
    ReplacementStrategyType, StrategyEffectiveness, SituationScore,
    ExecutionMetrics, AdaptiveReplacementConstants
)

logger = logging.getLogger(__name__)


class RLAlgorithmType(Enum):
    """强化学习算法类型"""
    Q_LEARNING = "q_learning"
    DEEP_Q_NETWORK = "deep_q_network"
    POLICY_GRADIENT = "policy_gradient"
    ACTOR_CRITIC = "actor_critic"
    PROXIMAL_POLICY_OPTIMIZATION = "ppo"
    MULTI_ARMED_BANDIT = "multi_armed_bandit"


class ActionType(Enum):
    """行动类型"""
    STRATEGY_SELECTION = "strategy_selection"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    COMBINED_ACTION = "combined_action"


@dataclass
class RLState:
    """强化学习状态"""
    context_signature: str
    situation_health: float
    rule_density: float
    execution_efficiency: float
    goal_progress: float
    failure_frequency: float
    agent_utilization: float
    last_strategy: ReplacementStrategyType
    last_performance: float
    time_since_last_action: int
    
    def to_vector(self) -> np.ndarray:
        """转换为状态向量"""
        return np.array([
            self.situation_health,
            self.rule_density,
            self.execution_efficiency,
            self.goal_progress,
            self.failure_frequency,
            self.agent_utilization,
            self.last_performance,
            self.time_since_last_action / 60.0  # 标准化到小时
        ])
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class RLAction:
    """强化学习行动"""
    action_id: str
    action_type: ActionType
    strategy_choice: Optional[ReplacementStrategyType]
    parameter_adjustments: Dict[str, float]
    expected_reward: float
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'action_id': self.action_id,
            'action_type': self.action_type.value,
            'strategy_choice': self.strategy_choice.value if self.strategy_choice else None,
            'parameter_adjustments': self.parameter_adjustments,
            'expected_reward': self.expected_reward,
            'confidence': self.confidence
        }


@dataclass
class RLExperience:
    """强化学习经验"""
    state: RLState
    action: RLAction
    reward: float
    next_state: RLState
    done: bool
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'state': self.state.to_dict(),
            'action': self.action.to_dict(),
            'reward': self.reward,
            'next_state': self.next_state.to_dict(),
            'done': self.done,
            'timestamp': self.timestamp.isoformat()
        }


class QLearningAgent:
    """Q-Learning智能体"""
    
    def __init__(self, 
                 state_size: int = 8,
                 action_size: int = 20,
                 learning_rate: float = 0.01,
                 discount_factor: float = 0.95,
                 epsilon: float = 0.1,
                 epsilon_decay: float = 0.995,
                 epsilon_min: float = 0.01):
        """
        初始化Q-Learning智能体
        
        Args:
            state_size: 状态空间维度
            action_size: 行动空间大小
            learning_rate: 学习率
            discount_factor: 折扣因子
            epsilon: 探索率
            epsilon_decay: 探索率衰减
            epsilon_min: 最小探索率
        """
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Q表（使用离散化状态）
        self.q_table: Dict[str, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        
        # 统计信息
        self.total_episodes = 0
        self.total_steps = 0
        self.rewards_history = []
        
        logger.info(f"Q-Learning智能体初始化: 状态维度={state_size}, 行动空间={action_size}")
    
    def discretize_state(self, state_vector: np.ndarray) -> str:
        """离散化状态向量"""
        # 将连续状态离散化为字符串键
        discretized = []
        for value in state_vector:
            # 分为10个区间
            discrete_value = int(np.clip(value * 10, 0, 9))
            discretized.append(str(discrete_value))
        return "_".join(discretized)
    
    def choose_action(self, state: RLState) -> int:
        """选择行动（epsilon-greedy策略）"""
        state_key = self.discretize_state(state.to_vector())
        
        # Epsilon-greedy选择
        if random.random() < self.epsilon:
            # 探索：随机选择
            action = random.randint(0, self.action_size - 1)
        else:
            # 利用：选择Q值最高的行动
            q_values = self.q_table[state_key]
            if q_values:
                action = max(q_values.items(), key=lambda x: x[1])[0]
            else:
                action = random.randint(0, self.action_size - 1)
        
        return action
    
    def learn(self, state: RLState, action: int, reward: float, next_state: RLState, done: bool):
        """Q-Learning更新"""
        state_key = self.discretize_state(state.to_vector())
        next_state_key = self.discretize_state(next_state.to_vector())
        
        # 获取当前Q值
        current_q = self.q_table[state_key][action]
        
        # 计算目标Q值
        if done:
            target_q = reward
        else:
            next_q_values = self.q_table[next_state_key]
            max_next_q = max(next_q_values.values()) if next_q_values else 0.0
            target_q = reward + self.discount_factor * max_next_q
        
        # Q值更新
        self.q_table[state_key][action] = current_q + self.learning_rate * (target_q - current_q)
        
        # 更新探索率
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        self.total_steps += 1
    
    def get_q_value(self, state: RLState, action: int) -> float:
        """获取Q值"""
        state_key = self.discretize_state(state.to_vector())
        return self.q_table[state_key][action]
    
    def get_policy(self, state: RLState) -> Dict[int, float]:
        """获取策略（行动概率分布）"""
        state_key = self.discretize_state(state.to_vector())
        q_values = self.q_table[state_key]
        
        if not q_values:
            # 均匀分布
            return {i: 1.0 / self.action_size for i in range(self.action_size)}
        
        # Softmax转换
        max_q = max(q_values.values())
        exp_q = {action: math.exp(q_val - max_q) for action, q_val in q_values.items()}
        sum_exp = sum(exp_q.values())
        
        policy = {}
        for i in range(self.action_size):
            if i in exp_q:
                policy[i] = exp_q[i] / sum_exp
            else:
                policy[i] = 0.01  # 小概率
        
        return policy


class MultiArmedBanditAgent:
    """多臂老虎机智能体"""
    
    def __init__(self, 
                 num_arms: int = 10,
                 epsilon: float = 0.1,
                 initial_value: float = 0.0):
        """
        初始化多臂老虎机智能体
        
        Args:
            num_arms: 臂数量（策略数量）
            epsilon: 探索率
            initial_value: 初始价值估计
        """
        self.num_arms = num_arms
        self.epsilon = epsilon
        self.initial_value = initial_value
        
        # 价值估计和选择次数
        self.values = [initial_value] * num_arms
        self.counts = [0] * num_arms
        self.total_reward = 0.0
        self.total_steps = 0
        
        logger.info(f"多臂老虎机智能体初始化: {num_arms}个臂")
    
    def choose_action(self) -> int:
        """选择行动（epsilon-greedy或UCB）"""
        if random.random() < self.epsilon:
            # 探索
            return random.randint(0, self.num_arms - 1)
        else:
            # 利用：选择价值最高的臂
            return np.argmax(self.values)
    
    def choose_action_ucb(self, c: float = 2.0) -> int:
        """使用Upper Confidence Bound选择行动"""
        if self.total_steps == 0:
            return random.randint(0, self.num_arms - 1)
        
        ucb_values = []
        for i in range(self.num_arms):
            if self.counts[i] == 0:
                ucb_values.append(float('inf'))
            else:
                confidence = c * math.sqrt(math.log(self.total_steps) / self.counts[i])
                ucb_values.append(self.values[i] + confidence)
        
        return np.argmax(ucb_values)
    
    def update(self, action: int, reward: float):
        """更新价值估计"""
        self.counts[action] += 1
        self.total_steps += 1
        self.total_reward += reward
        
        # 增量更新平均值
        self.values[action] += (reward - self.values[action]) / self.counts[action]
    
    def get_arm_statistics(self) -> Dict[str, Any]:
        """获取臂统计信息"""
        return {
            'values': self.values.copy(),
            'counts': self.counts.copy(),
            'total_steps': self.total_steps,
            'total_reward': self.total_reward,
            'average_reward': self.total_reward / max(1, self.total_steps)
        }


class PolicyGradientAgent:
    """策略梯度智能体（简化实现）"""
    
    def __init__(self, 
                 state_size: int = 8,
                 action_size: int = 20,
                 learning_rate: float = 0.01):
        """
        初始化策略梯度智能体
        
        Args:
            state_size: 状态空间维度
            action_size: 行动空间大小
            learning_rate: 学习率
        """
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        
        # 简化的线性策略网络权重
        self.weights = np.random.normal(0, 0.1, (state_size, action_size))
        self.bias = np.zeros(action_size)
        
        # 经验缓冲
        self.episode_states = []
        self.episode_actions = []
        self.episode_rewards = []
        
        logger.info(f"策略梯度智能体初始化: 状态维度={state_size}, 行动空间={action_size}")
    
    def get_action_probabilities(self, state: RLState) -> np.ndarray:
        """获取行动概率"""
        state_vector = state.to_vector()
        logits = np.dot(state_vector, self.weights) + self.bias
        
        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probabilities = exp_logits / np.sum(exp_logits)
        
        return probabilities
    
    def choose_action(self, state: RLState) -> int:
        """根据策略选择行动"""
        probabilities = self.get_action_probabilities(state)
        action = np.random.choice(self.action_size, p=probabilities)
        return action
    
    def store_transition(self, state: RLState, action: int, reward: float):
        """存储转换"""
        self.episode_states.append(state.to_vector())
        self.episode_actions.append(action)
        self.episode_rewards.append(reward)
    
    def learn_episode(self):
        """从一个回合学习"""
        if not self.episode_states:
            return
        
        # 计算折扣奖励
        discounted_rewards = self._compute_discounted_rewards()
        
        # 标准化奖励
        if len(discounted_rewards) > 1:
            discounted_rewards = (discounted_rewards - np.mean(discounted_rewards)) / (np.std(discounted_rewards) + 1e-8)
        
        # 策略梯度更新
        for i, (state, action, reward) in enumerate(zip(self.episode_states, self.episode_actions, discounted_rewards)):
            # 计算梯度
            probabilities = self.get_action_probabilities(RLState(
                context_signature="", situation_health=0, rule_density=0,
                execution_efficiency=0, goal_progress=0, failure_frequency=0,
                agent_utilization=0, last_strategy=ReplacementStrategyType.CONSERVATIVE,
                last_performance=0, time_since_last_action=0
            ))
            
            # 简化的梯度计算
            gradient_weights = np.outer(state, reward * (np.eye(self.action_size)[action] - probabilities))
            gradient_bias = reward * (np.eye(self.action_size)[action] - probabilities)
            
            # 更新参数
            self.weights += self.learning_rate * gradient_weights
            self.bias += self.learning_rate * gradient_bias
        
        # 清空回合数据
        self.episode_states.clear()
        self.episode_actions.clear()
        self.episode_rewards.clear()
    
    def _compute_discounted_rewards(self, gamma: float = 0.99) -> np.ndarray:
        """计算折扣奖励"""
        discounted = np.zeros_like(self.episode_rewards, dtype=float)
        running_sum = 0
        
        for i in reversed(range(len(self.episode_rewards))):
            running_sum = self.episode_rewards[i] + gamma * running_sum
            discounted[i] = running_sum
        
        return discounted


class ReinforcementLearningOptimizer:
    """强化学习优化器 - Phase 3核心组件"""
    
    def __init__(self, 
                 algorithm_type: RLAlgorithmType = RLAlgorithmType.Q_LEARNING,
                 state_size: int = 8,
                 action_size: int = 20):
        """
        初始化强化学习优化器
        
        Args:
            algorithm_type: 使用的强化学习算法
            state_size: 状态空间维度
            action_size: 行动空间大小
        """
        self.algorithm_type = algorithm_type
        self.state_size = state_size
        self.action_size = action_size
        
        # 初始化智能体
        self.agent = self._create_agent(algorithm_type)
        
        # 状态和行动映射
        self.strategy_mapping = list(ReplacementStrategyType)
        self.action_space = self._define_action_space()
        
        # 经验回放
        self.experience_buffer: deque = deque(maxlen=1000)
        self.current_episode_experiences: List[RLExperience] = []
        
        # 性能追踪
        self.episode_rewards: List[float] = []
        self.episode_lengths: List[int] = []
        self.current_episode = 0
        
        # 学习统计
        self.learning_stats = {
            'total_experiences': 0,
            'total_rewards': 0.0,
            'average_reward': 0.0,
            'exploration_rate': getattr(self.agent, 'epsilon', 0.0),
            'learning_progress': []
        }
        
        logger.info(f"强化学习优化器初始化: {algorithm_type.value}")
    
    def _create_agent(self, algorithm_type: RLAlgorithmType):
        """创建指定类型的智能体"""
        if algorithm_type == RLAlgorithmType.Q_LEARNING:
            return QLearningAgent(
                state_size=self.state_size,
                action_size=self.action_size
            )
        elif algorithm_type == RLAlgorithmType.MULTI_ARMED_BANDIT:
            return MultiArmedBanditAgent(
                num_arms=len(self.strategy_mapping)
            )
        elif algorithm_type == RLAlgorithmType.POLICY_GRADIENT:
            return PolicyGradientAgent(
                state_size=self.state_size,
                action_size=self.action_size
            )
        else:
            # 默认使用Q-Learning
            logger.warning(f"不支持的算法类型 {algorithm_type.value}，使用Q-Learning")
            return QLearningAgent(
                state_size=self.state_size,
                action_size=self.action_size
            )
    
    def _define_action_space(self) -> List[RLAction]:
        """定义行动空间"""
        actions = []
        action_id = 0
        
        # 策略选择行动
        for strategy in self.strategy_mapping:
            action = RLAction(
                action_id=f"strategy_{action_id}",
                action_type=ActionType.STRATEGY_SELECTION,
                strategy_choice=strategy,
                parameter_adjustments={},
                expected_reward=0.0,
                confidence=0.5
            )
            actions.append(action)
            action_id += 1
        
        # 参数调整行动
        parameter_adjustments = [
            {'replacement_ratio': 0.1},
            {'replacement_ratio': -0.1},
            {'similarity_threshold': 0.05},
            {'similarity_threshold': -0.05},
            {'performance_threshold': 0.05},
            {'performance_threshold': -0.05}
        ]
        
        for adjustment in parameter_adjustments:
            action = RLAction(
                action_id=f"param_{action_id}",
                action_type=ActionType.PARAMETER_ADJUSTMENT,
                strategy_choice=None,
                parameter_adjustments=adjustment,
                expected_reward=0.0,
                confidence=0.5
            )
            actions.append(action)
            action_id += 1
        
        # 限制行动空间大小
        return actions[:self.action_size]
    
    def encode_state(self, 
                    situation: SituationScore,
                    last_strategy: ReplacementStrategyType,
                    last_performance: float,
                    time_since_last: int = 0) -> RLState:
        """编码当前状态"""
        context_signature = self._generate_context_signature(situation)
        
        return RLState(
            context_signature=context_signature,
            situation_health=situation.get_overall_health(),
            rule_density=situation.rule_density,
            execution_efficiency=situation.execution_efficiency,
            goal_progress=situation.goal_progress,
            failure_frequency=situation.failure_frequency,
            agent_utilization=situation.agent_utilization,
            last_strategy=last_strategy,
            last_performance=last_performance,
            time_since_last_action=time_since_last
        )
    
    def choose_action(self, state: RLState) -> RLAction:
        """选择行动"""
        try:
            if self.algorithm_type == RLAlgorithmType.MULTI_ARMED_BANDIT:
                # 多臂老虎机只选择策略
                arm_index = self.agent.choose_action()
                if arm_index < len(self.strategy_mapping):
                    return RLAction(
                        action_id=f"bandit_{arm_index}",
                        action_type=ActionType.STRATEGY_SELECTION,
                        strategy_choice=self.strategy_mapping[arm_index],
                        parameter_adjustments={},
                        expected_reward=0.0,
                        confidence=0.8
                    )
            
            # 其他算法
            action_index = self.agent.choose_action(state)
            
            if action_index < len(self.action_space):
                selected_action = self.action_space[action_index]
                
                # 更新期望奖励
                if hasattr(self.agent, 'get_q_value'):
                    selected_action.expected_reward = self.agent.get_q_value(state, action_index)
                
                return selected_action
            
            # 后备行动
            return self.action_space[0]
            
        except Exception as e:
            logger.error(f"选择行动失败: {e}")
            return self.action_space[0]  # 返回默认行动
    
    def learn_from_experience(self, 
                            state: RLState,
                            action: RLAction,
                            reward: float,
                            next_state: RLState,
                            done: bool = False):
        """从经验学习"""
        try:
            # 创建经验
            experience = RLExperience(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=done,
                timestamp=datetime.now()
            )
            
            # 添加到经验缓冲
            self.experience_buffer.append(experience)
            self.current_episode_experiences.append(experience)
            
            # 智能体学习
            if self.algorithm_type == RLAlgorithmType.Q_LEARNING:
                action_index = self._get_action_index(action)
                if action_index is not None:
                    self.agent.learn(state, action_index, reward, next_state, done)
            
            elif self.algorithm_type == RLAlgorithmType.MULTI_ARMED_BANDIT:
                arm_index = self._get_strategy_index(action.strategy_choice)
                if arm_index is not None:
                    self.agent.update(arm_index, reward)
            
            elif self.algorithm_type == RLAlgorithmType.POLICY_GRADIENT:
                action_index = self._get_action_index(action)
                if action_index is not None:
                    self.agent.store_transition(state, action_index, reward)
            
            # 更新统计
            self.learning_stats['total_experiences'] += 1
            self.learning_stats['total_rewards'] += reward
            self.learning_stats['average_reward'] = (
                self.learning_stats['total_rewards'] / self.learning_stats['total_experiences']
            )
            
            # 如果回合结束，进行回合级学习
            if done:
                self._end_episode()
            
            logger.debug(f"学习经验: 奖励={reward:.3f}, 总经验={self.learning_stats['total_experiences']}")
            
        except Exception as e:
            logger.error(f"从经验学习失败: {e}")
    
    def calculate_reward(self, 
                        effectiveness: StrategyEffectiveness,
                        previous_health: float) -> float:
        """计算奖励"""
        try:
            # 基础奖励：改进分数
            base_reward = effectiveness.improvement_score
            
            # 成功应用奖励
            if effectiveness.is_successful_application():
                base_reward += 0.2
            
            # 性能提升奖励
            performance_gain = effectiveness.get_performance_gain()
            if performance_gain > 0:
                base_reward += performance_gain * 0.3
            
            # 效率提升奖励
            efficiency_gain = effectiveness.get_efficiency_gain()
            if efficiency_gain > 0:
                base_reward += efficiency_gain * 0.2
            
            # 健康度改善奖励
            current_health = effectiveness.applied_context.get_overall_health()
            health_improvement = current_health - previous_health
            base_reward += health_improvement * 0.5
            
            # 风险惩罚
            if effectiveness.applied_context.failure_frequency > 0.3:
                base_reward -= 0.1
            
            # 时间效率奖励
            if effectiveness.execution_duration.total_seconds() < 30:  # 快速执行
                base_reward += 0.05
            
            # 将奖励限制在合理范围内
            final_reward = np.clip(base_reward, -1.0, 1.0)
            
            return final_reward
            
        except Exception as e:
            logger.error(f"计算奖励失败: {e}")
            return 0.0
    
    def _get_action_index(self, action: RLAction) -> Optional[int]:
        """获取行动索引"""
        for i, space_action in enumerate(self.action_space):
            if (space_action.action_type == action.action_type and
                space_action.strategy_choice == action.strategy_choice and
                space_action.parameter_adjustments == action.parameter_adjustments):
                return i
        return None
    
    def _get_strategy_index(self, strategy: Optional[ReplacementStrategyType]) -> Optional[int]:
        """获取策略索引"""
        if strategy is None:
            return None
        try:
            return self.strategy_mapping.index(strategy)
        except ValueError:
            return None
    
    def _generate_context_signature(self, situation: SituationScore) -> str:
        """生成上下文签名"""
        health = situation.get_overall_health()
        health_level = "high" if health > 0.7 else "medium" if health > 0.4 else "low"
        
        density_level = "high" if situation.rule_density > 0.7 else "medium" if situation.rule_density > 0.4 else "low"
        efficiency_level = "high" if situation.execution_efficiency > 0.7 else "medium" if situation.execution_efficiency > 0.4 else "low"
        
        return f"{health_level}_{density_level}_{efficiency_level}"
    
    def _end_episode(self):
        """结束当前回合"""
        try:
            # 计算回合奖励和长度
            episode_reward = sum(exp.reward for exp in self.current_episode_experiences)
            episode_length = len(self.current_episode_experiences)
            
            self.episode_rewards.append(episode_reward)
            self.episode_lengths.append(episode_length)
            
            # 策略梯度回合级学习
            if self.algorithm_type == RLAlgorithmType.POLICY_GRADIENT:
                self.agent.learn_episode()
            
            # 更新学习进度
            self.learning_stats['learning_progress'].append({
                'episode': self.current_episode,
                'reward': episode_reward,
                'length': episode_length,
                'average_reward': np.mean(self.episode_rewards[-10:])  # 最近10个回合的平均奖励
            })
            
            # 更新探索率
            if hasattr(self.agent, 'epsilon'):
                self.learning_stats['exploration_rate'] = self.agent.epsilon
            
            # 清空当前回合经验
            self.current_episode_experiences.clear()
            self.current_episode += 1
            
            logger.info(f"回合 {self.current_episode} 结束: 奖励={episode_reward:.3f}, 长度={episode_length}")
            
        except Exception as e:
            logger.error(f"结束回合失败: {e}")
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        try:
            stats = self.learning_stats.copy()
            
            # 添加智能体特定统计
            if hasattr(self.agent, 'get_arm_statistics'):
                stats['bandit_stats'] = self.agent.get_arm_statistics()
            
            if hasattr(self.agent, 'q_table'):
                stats['q_table_size'] = len(self.agent.q_table)
                stats['total_q_entries'] = sum(len(actions) for actions in self.agent.q_table.values())
            
            # 性能指标
            if self.episode_rewards:
                stats['performance_metrics'] = {
                    'total_episodes': len(self.episode_rewards),
                    'best_episode_reward': max(self.episode_rewards),
                    'worst_episode_reward': min(self.episode_rewards),
                    'recent_average_reward': np.mean(self.episode_rewards[-10:]) if len(self.episode_rewards) >= 10 else np.mean(self.episode_rewards),
                    'reward_trend': self._calculate_reward_trend()
                }
            
            stats['experience_buffer_size'] = len(self.experience_buffer)
            stats['current_episode'] = self.current_episode
            
            return stats
            
        except Exception as e:
            logger.error(f"获取学习统计失败: {e}")
            return {'error': str(e)}
    
    def _calculate_reward_trend(self) -> str:
        """计算奖励趋势"""
        if len(self.episode_rewards) < 5:
            return "insufficient_data"
        
        recent_rewards = self.episode_rewards[-5:]
        early_avg = np.mean(recent_rewards[:2])
        late_avg = np.mean(recent_rewards[-2:])
        
        if late_avg > early_avg + 0.05:
            return "improving"
        elif late_avg < early_avg - 0.05:
            return "declining"
        else:
            return "stable"
    
    def get_policy_recommendations(self, state: RLState) -> List[Dict[str, Any]]:
        """获取策略建议"""
        recommendations = []
        
        try:
            if self.algorithm_type == RLAlgorithmType.Q_LEARNING and hasattr(self.agent, 'get_policy'):
                # 获取策略分布
                policy = self.agent.get_policy(state)
                
                # 生成前3个推荐行动
                sorted_actions = sorted(policy.items(), key=lambda x: x[1], reverse=True)
                
                for i, (action_index, probability) in enumerate(sorted_actions[:3]):
                    if action_index < len(self.action_space):
                        action = self.action_space[action_index]
                        recommendations.append({
                            'rank': i + 1,
                            'action': action.to_dict(),
                            'probability': probability,
                            'expected_reward': getattr(action, 'expected_reward', 0.0),
                            'confidence': probability
                        })
            
            elif self.algorithm_type == RLAlgorithmType.MULTI_ARMED_BANDIT:
                # 获取臂统计信息
                if hasattr(self.agent, 'get_arm_statistics'):
                    stats = self.agent.get_arm_statistics()
                    values = stats['values']
                    counts = stats['counts']
                    
                    # 按价值排序推荐
                    arm_scores = [(i, values[i], counts[i]) for i in range(len(values))]
                    arm_scores.sort(key=lambda x: x[1], reverse=True)
                    
                    for i, (arm_index, value, count) in enumerate(arm_scores[:3]):
                        if arm_index < len(self.strategy_mapping):
                            strategy = self.strategy_mapping[arm_index]
                            recommendations.append({
                                'rank': i + 1,
                                'strategy': strategy.value,
                                'estimated_value': value,
                                'selection_count': count,
                                'confidence': min(1.0, count / 10.0)  # 基于选择次数的置信度
                            })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"生成策略建议失败: {e}")
            return []
    
    def export_learning_data(self, format_type: str = 'summary') -> Dict[str, Any]:
        """导出学习数据"""
        try:
            if format_type == 'detailed':
                return {
                    'algorithm_type': self.algorithm_type.value,
                    'learning_statistics': self.get_learning_statistics(),
                    'experience_buffer': [exp.to_dict() for exp in list(self.experience_buffer)[-50:]],  # 最近50个经验
                    'action_space': [action.to_dict() for action in self.action_space],
                    'strategy_mapping': [strategy.value for strategy in self.strategy_mapping],
                    'episode_history': {
                        'rewards': self.episode_rewards[-20:],  # 最近20个回合
                        'lengths': self.episode_lengths[-20:]
                    }
                }
            else:
                return self.get_learning_statistics()
                
        except Exception as e:
            logger.error(f"导出学习数据失败: {e}")
            return {'error': str(e)}
    
    def save_model(self, filepath: str):
        """保存模型"""
        try:
            model_data = {
                'algorithm_type': self.algorithm_type.value,
                'state_size': self.state_size,
                'action_size': self.action_size,
                'learning_stats': self.learning_stats,
                'episode_rewards': self.episode_rewards,
                'episode_lengths': self.episode_lengths,
                'current_episode': self.current_episode
            }
            
            # 保存智能体特定数据
            if hasattr(self.agent, 'q_table'):
                model_data['q_table'] = dict(self.agent.q_table)
                model_data['epsilon'] = self.agent.epsilon
            
            if hasattr(self.agent, 'values'):
                model_data['bandit_values'] = self.agent.values
                model_data['bandit_counts'] = self.agent.counts
            
            if hasattr(self.agent, 'weights'):
                model_data['policy_weights'] = self.agent.weights.tolist()
                model_data['policy_bias'] = self.agent.bias.tolist()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"模型已保存到: {filepath}")
            
        except Exception as e:
            logger.error(f"保存模型失败: {e}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            
            # 恢复基本属性
            self.learning_stats = model_data.get('learning_stats', {})
            self.episode_rewards = model_data.get('episode_rewards', [])
            self.episode_lengths = model_data.get('episode_lengths', [])
            self.current_episode = model_data.get('current_episode', 0)
            
            # 恢复智能体状态
            if hasattr(self.agent, 'q_table') and 'q_table' in model_data:
                self.agent.q_table = defaultdict(lambda: defaultdict(float))
                for state_key, actions in model_data['q_table'].items():
                    for action, q_value in actions.items():
                        self.agent.q_table[state_key][int(action)] = q_value
                
                if 'epsilon' in model_data:
                    self.agent.epsilon = model_data['epsilon']
            
            if hasattr(self.agent, 'values') and 'bandit_values' in model_data:
                self.agent.values = model_data['bandit_values']
                self.agent.counts = model_data['bandit_counts']
            
            if hasattr(self.agent, 'weights') and 'policy_weights' in model_data:
                self.agent.weights = np.array(model_data['policy_weights'])
                self.agent.bias = np.array(model_data['policy_bias'])
            
            logger.info(f"模型已从 {filepath} 加载")
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
    
    def reset_learning(self):
        """重置学习状态"""
        try:
            # 重新创建智能体
            self.agent = self._create_agent(self.algorithm_type)
            
            # 清空经验和统计
            self.experience_buffer.clear()
            self.current_episode_experiences.clear()
            self.episode_rewards.clear()
            self.episode_lengths.clear()
            self.current_episode = 0
            
            # 重置统计
            self.learning_stats = {
                'total_experiences': 0,
                'total_rewards': 0.0,
                'average_reward': 0.0,
                'exploration_rate': getattr(self.agent, 'epsilon', 0.0),
                'learning_progress': []
            }
            
            logger.info("强化学习状态已重置")
            
        except Exception as e:
            logger.error(f"重置学习状态失败: {e}")