#!/usr/bin/env python3
"""
天气数据模块
提供模拟的天气数据和查询功能
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class WeatherData:
    """天气数据类，提供模拟的天气信息"""
    
    def __init__(self):
        # 城市数据库：城市名 -> (纬度, 经度, 时区)
        self.cities = {
            # 中国主要城市
            "北京": (39.9042, 116.4074, "Asia/Shanghai"),
            "beijing": (39.9042, 116.4074, "Asia/Shanghai"),
            "上海": (31.2304, 121.4737, "Asia/Shanghai"),
            "shanghai": (31.2304, 121.4737, "Asia/Shanghai"),
            "广州": (23.1291, 113.2644, "Asia/Shanghai"),
            "guangzhou": (23.1291, 113.2644, "Asia/Shanghai"),
            "深圳": (22.3193, 114.1694, "Asia/Shanghai"),
            "shenzhen": (22.3193, 114.1694, "Asia/Shanghai"),
            "杭州": (30.2741, 120.1551, "Asia/Shanghai"),
            "hangzhou": (30.2741, 120.1551, "Asia/Shanghai"),
            "成都": (30.5728, 104.0668, "Asia/Shanghai"),
            "chengdu": (30.5728, 104.0668, "Asia/Shanghai"),
            "西安": (34.3416, 108.9398, "Asia/Shanghai"),
            "xian": (34.3416, 108.9398, "Asia/Shanghai"),
            
            # 国际城市
            "london": (51.5074, -0.1278, "Europe/London"),
            "伦敦": (51.5074, -0.1278, "Europe/London"),
            "new york": (40.7128, -74.0060, "America/New_York"),
            "纽约": (40.7128, -74.0060, "America/New_York"),
            "tokyo": (35.6762, 139.6503, "Asia/Tokyo"),
            "东京": (35.6762, 139.6503, "Asia/Tokyo"),
            "paris": (48.8566, 2.3522, "Europe/Paris"),
            "巴黎": (48.8566, 2.3522, "Europe/Paris"),
            "singapore": (1.3521, 103.8198, "Asia/Singapore"),
            "新加坡": (1.3521, 103.8198, "Asia/Singapore"),
        }
        
        # 天气状况列表
        self.weather_conditions = [
            {"condition": "晴天", "icon": "☀️", "english": "sunny"},
            {"condition": "多云", "icon": "⛅", "english": "cloudy"},
            {"condition": "阴天", "icon": "☁️", "english": "overcast"},
            {"condition": "小雨", "icon": "🌦️", "english": "light rain"},
            {"condition": "中雨", "icon": "🌧️", "english": "moderate rain"},
            {"condition": "大雨", "icon": "⛈️", "english": "heavy rain"},
            {"condition": "雪", "icon": "❄️", "english": "snow"},
            {"condition": "雾", "icon": "🌫️", "english": "fog"},
        ]
    
    def normalize_city_name(self, city: str) -> str:
        """标准化城市名称"""
        return city.lower().strip()
    
    def get_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        """获取城市坐标"""
        normalized_city = self.normalize_city_name(city)
        if normalized_city in self.cities:
            lat, lon, _ = self.cities[normalized_city]
            return (lat, lon)
        return None
    
    def find_city_by_coordinates(self, lat: float, lon: float, tolerance: float = 0.1) -> Optional[str]:
        """根据坐标查找最近的城市"""
        min_distance = float('inf')
        closest_city = None
        
        for city, (city_lat, city_lon, _) in self.cities.items():
            distance = ((lat - city_lat) ** 2 + (lon - city_lon) ** 2) ** 0.5
            if distance < min_distance and distance <= tolerance:
                min_distance = distance
                closest_city = city
        
        return closest_city
    
    def generate_weather(self, city: str = None, lat: float = None, lon: float = None) -> Dict:
        """生成模拟天气数据"""
        # 确定城市信息
        if city:
            normalized_city = self.normalize_city_name(city)
            if normalized_city not in self.cities:
                raise ValueError(f"城市 '{city}' 不在支持列表中")
            
            city_lat, city_lon, timezone = self.cities[normalized_city]
            display_city = city
        elif lat is not None and lon is not None:
            # 根据坐标查找城市
            closest_city = self.find_city_by_coordinates(lat, lon)
            if closest_city:
                city_lat, city_lon, timezone = self.cities[closest_city]
                display_city = closest_city
            else:
                city_lat, city_lon = lat, lon
                timezone = "UTC"
                display_city = f"坐标({lat:.2f}, {lon:.2f})"
        else:
            raise ValueError("必须提供城市名称或坐标")
        
        # 生成随机天气数据
        condition_data = random.choice(self.weather_conditions)
        
        # 根据纬度调整温度范围
        base_temp = 20 - abs(city_lat) * 0.6  # 纬度越高温度越低
        temp_variation = random.uniform(-10, 15)
        temperature = round(base_temp + temp_variation, 1)
        
        weather_data = {
            "city": display_city,
            "coordinates": {"latitude": city_lat, "longitude": city_lon},
            "timezone": timezone,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": temperature,
            "feels_like": round(temperature + random.uniform(-3, 3), 1),
            "humidity": random.randint(30, 90),
            "pressure": random.randint(990, 1030),
            "wind_speed": round(random.uniform(0, 20), 1),
            "wind_direction": random.choice(["北", "东北", "东", "东南", "南", "西南", "西", "西北"]),
            "visibility": round(random.uniform(5, 30), 1),
            "uv_index": random.randint(1, 10),
            "condition": condition_data["condition"],
            "condition_icon": condition_data["icon"],
            "condition_english": condition_data["english"],
            "air_quality": {
                "aqi": random.randint(20, 200),
                "level": random.choice(["优", "良", "轻度污染", "中度污染", "重度污染"]),
                "pm25": random.randint(10, 150),
                "pm10": random.randint(20, 300)
            }
        }
        
        return weather_data
    
    def generate_forecast(self, city: str = None, lat: float = None, lon: float = None, days: int = 5) -> List[Dict]:
        """生成天气预报数据"""
        forecast = []
        base_weather = self.generate_weather(city=city, lat=lat, lon=lon)
        
        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            condition_data = random.choice(self.weather_conditions)
            
            # 基于当前天气生成预报，添加一些变化
            temp_change = random.uniform(-5, 5)
            base_temp = base_weather["temperature"] + temp_change
            
            forecast_data = {
                "date": date.strftime("%Y-%m-%d"),
                "day_of_week": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()],
                "high_temperature": round(base_temp + random.uniform(2, 8), 1),
                "low_temperature": round(base_temp - random.uniform(2, 8), 1),
                "condition": condition_data["condition"],
                "condition_icon": condition_data["icon"],
                "condition_english": condition_data["english"],
                "humidity": random.randint(30, 90),
                "wind_speed": round(random.uniform(0, 15), 1),
                "precipitation": round(random.uniform(0, 10), 1) if "雨" in condition_data["condition"] else 0
            }
            forecast.append(forecast_data)
        
        return forecast
    
    def get_supported_cities(self) -> List[str]:
        """获取支持的城市列表"""
        return list(self.cities.keys())
    
    def format_weather_report(self, weather_data: Dict) -> str:
        """格式化天气报告"""
        report = f"""
🌤️ **{weather_data['city']} 天气报告**

📅 **当前时间**: {weather_data['current_time']}
🌡️ **温度**: {weather_data['temperature']}°C (体感温度: {weather_data['feels_like']}°C)
{weather_data['condition_icon']} **天气**: {weather_data['condition']}
💧 **湿度**: {weather_data['humidity']}%
🌪️ **风速**: {weather_data['wind_speed']} km/h ({weather_data['wind_direction']}风)
👁️ **能见度**: {weather_data['visibility']} km
☀️ **紫外线指数**: {weather_data['uv_index']}
🏭 **空气质量**: {weather_data['air_quality']['level']} (AQI: {weather_data['air_quality']['aqi']})

📍 **坐标**: ({weather_data['coordinates']['latitude']:.2f}, {weather_data['coordinates']['longitude']:.2f})
        """.strip()
        
        return report
    
    def format_forecast_report(self, forecast_data: List[Dict], city: str) -> str:
        """格式化天气预报报告"""
        report = f"📊 **{city} {len(forecast_data)}天天气预报**\n\n"
        
        for day in forecast_data:
            report += f"""📅 **{day['date']} ({day['day_of_week']})**
{day['condition_icon']} {day['condition']} | 🌡️ {day['low_temperature']}°C - {day['high_temperature']}°C
💧 湿度: {day['humidity']}% | 🌪️ 风速: {day['wind_speed']} km/h"""
            
            if day['precipitation'] > 0:
                report += f" | 🌧️ 降水: {day['precipitation']}mm"
            
            report += "\n\n"
        
        return report.strip()


# 全局天气数据实例
weather_db = WeatherData()