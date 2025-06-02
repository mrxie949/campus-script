# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import datetime
from streamlit.components.v1 import html
import json
import os
import re

# ===== 动态时钟组件 =====
def create_live_clock():
    """创建实时更新的北京时间时钟"""
    clock_js = """
    <div style="text-align:center;margin-bottom:20px;">
        <div id="clock" style="font-size:28px;font-weight:bold;color:#4e8cff;"></div>
        <div style="font-size:16px;color:#9ca3af;">北京时间</div>
    </div>
    <script>
        function updateClock() {
            const now = new Date();
            const beijingTime = new Date(now.getTime() + (now.getTimezoneOffset() * 60000) + (3600000 * 8));
            const hours = beijingTime.getHours().toString().padStart(2, '0');
            const minutes = beijingTime.getMinutes().toString().padStart(2, '0');
            const seconds = beijingTime.getSeconds().toString().padStart(2, '0');
            document.getElementById('clock').innerHTML = `${hours}:${minutes}:${seconds}`;
        }
        setInterval(updateClock, 1000);
        updateClock();
    </script>
    """
    return html(clock_js, height=70)

# ===== 配置区 =====
# 使用您提供的API密钥
MOONSHOT_API_KEY = "sk-sqrfIzSxn92laOhBxS9HSMZ6Y4itPpZ70Z49v1pWnIl7RgQb"

# API端点列表（主备）
MOONSHOT_API_URLS = [
    "https://api.moonshot.cn/v1/chat/completions",
    "https://api.moonshot.cn/v1/completions"
]

# API健康检查
def check_api_health():
    """检查Moonshot API可用性并返回可用端点"""
    for api_url in MOONSHOT_API_URLS:
        try:
            # 获取API基础状态
            base_url = api_url.rsplit('/', 2)[0]  # 移除最后两个路径部分
            response = requests.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {MOONSHOT_API_KEY}"},
                timeout=5
            )
            if response.status_code == 200:
                return True, api_url
        except Exception as e:
            print(f"API端点 {api_url} 不可用: {str(e)}")
            continue
    return False, None

# 执行API健康检查
api_healthy, active_api_url = check_api_health()
if not api_healthy:
    st.error("🚨 Moonshot API服务不可用，请检查：")
    st.write("1. API密钥是否正确")
    st.write("2. 网络连接是否正常")
    st.write("3. 服务状态: [status.moonshot.cn](https://status.moonshot.cn)")
    st.stop()

# ===== 平台规则配置 =====
PLATFORM_RULES = {
    "抖音": {
        "opening": ["冲突", "悬念", "热点"],
        "length": "15-60秒",
        "visual": "高饱和、快转场",
        "interaction": "强（点赞/购物车）",
        "话术": ["家人们谁懂啊！", "点击购物车", "库存告急", "这波操作6不6？", "答应我，一定要试试！"],
        "爆款结构": [
            "0-3秒：冲突悬念开场（疑问句+特写）",
            "3-8秒：价值展示（核心看点）",
            "8-15秒：情感共鸣（痛点/爽点）",
            "15秒后：反转/高潮（意外惊喜）",
            "结尾：行动召唤（关注+互动）"
        ]
    },
    "B站": {
        "opening": ["知识提问", "人设开场"],
        "length": "3-15分钟",
        "depth": "中高（分点解析）",
        "interaction": "弹幕梗（前方高能、要素察觉）",
        "话术": ["懂的都懂", "接下来划重点", "弹幕刷起来", "一键三连", "前方高能预警"],
        "爆款结构": [
            "0-15秒：知识钩子开场（专业问题/争议观点）",
            "15-45秒：深度解析（分点讲解）",
            "45-120秒：案例验证（实测/数据展示）",
            "结尾：系列化引导（下期预告/弹幕互动）"
        ]
    },
    "小红书": {
        "opening": ["场景代入", "颜值画面"],
        "aesthetic": "ins风、韩系滤镜",
        "scene": "生活细节（通勤、探店、居家）",
        "soft_sell": True,
        "话术": ["种草", "避雷", "XX女孩必备", "收藏备用", "早八必备"],
        "爆款结构": [
            "0-5秒：场景痛点展示",
            "5-15秒：解决方案演示（3步法）",
            "15-23秒：效果展示+美学画面",
            "结尾：行动引导（收藏/话题）"
        ]
    },
    "快手": {
        "opening": ["真实人设（工厂、农村）"],
        "length": "15-90秒",
        "price_sensitive": True,
        "dialect": "支持（老铁、恁、薅羊毛）",
        "drama": "家庭/朋友剧情",
        "visual": "真实场景、接地气",
        "interaction": "强（关注/评论）",
        "话术": ["老铁们", "没毛病", "福利上车", "砍价", "家人们，薅羊毛了"],
        "爆款结构": [
            "0-10秒：人设+福利钩子",
            "10-25秒：产品细节+价格对比",
            "25-35秒：场景化使用演示",
            "结尾：紧迫感转化（库存/倒计时）"
        ]
    },
    "视频号": {
        "opening": ["情感共鸣", "热点"],
        "length": "15-90秒",
        "interaction": "引导关注",
        "话术": ["关注我，每天分享...", "点赞收藏", "分享给朋友"],
        "爆款结构": [
            "0-3秒：情感共鸣开场",
            "3-8秒：价值展示",
            "8-15秒：情感深化",
            "15秒后：高潮/反转",
            "结尾：关注引导"
        ]
    }
}

# ===== 扩展选项库 =====
VIDEO_CATEGORIES = [
    "旅行", "vlog", "美食", "纪念日", "萌娃", "好物分享", 
    "探店", "萌宠", "家居", "汽车", "动漫", "科技", "健身",
    "美妆", "游戏", "音乐", "舞蹈", "教育", "搞笑", "剧情"
]

VIDEO_STYLES = [
    "幽默搞笑", "知识干货", "情感治愈", "热血励志", "文艺清新",
    "悬疑反转", "浪漫唯美", "怀旧复古", "潮流时尚", "极简主义",
    "暗黑系", "治愈系", "赛博朋克", "国风古韵", "日系小清新",
    "欧美大片", "韩系ins风", "港风复古", "街头文化", "实验艺术"
]

TARGET_AUDIENCES = [
    "学生党", "上班族", "宝妈宝爸", "Z世代", "银发族",
    "二次元", "电竞玩家", "美食爱好者", "旅行达人", "健身爱好者",
    "美妆达人", "科技发烧友", "汽车爱好者", "宠物主人", "家居设计师",
    "创业者", "企业高管", "教师", "医护人员", "自由职业者"
]

# ===== 抖音流行台词库 =====
TRENDY_PHRASES = [
    "这操作，6不6？", "绝了家人们！", "这也太哇塞了吧！", 
    "答应我，一定要试试！", "不会只有我才知道吧？", 
    "救命！这也太神仙了", "直接封神了好吗！", 
    "一整个爱住！", "是谁的DNA动了？", "YYDS！",
    "绝绝子！", "这也太上头了", "给我整破防了",
    "你品，你细品", "这是什么神仙操作", "这波在大气层"
]

# ===== 热榜API配置 =====
HOT_API_CONFIG = {
    "抖音": "https://www.douyin.com/aweme/v1/web/hot/search/list/",
    "B站": "https://api.bilibili.com/x/web-interface/search/square?limit=50",  # 更新为最新热搜API
    "头条": "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"  # 保持现有有效API
}
# ===== 获取实时热榜 =====
def fetch_hotlist(platform):
    """获取指定平台的热榜数据"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.bilibili.com/" if platform == "B站" else "https://www.douyin.com/",  # 动态调整Referer
        "Cookie": "buvid3=xxxxx; sid=xxxxx"  # 示例Cookie，建议替换有效值
    }
    
    try:
        if platform == "抖音":
            response = requests.get(HOT_API_CONFIG[platform], headers=headers)
            if response.status_code == 200:
                data = response.json()
                return [f"{item.get('word', '')} 🔥{item.get('hot_value',0)//10000}万" 
                        for item in data.get('data',{}).get('word_list',[])[:10]]
            return []
        
        elif platform == "B站":
            response = requests.get(HOT_API_CONFIG[platform], headers=headers)
            if response.status_code == 200:
                data = response.json()
                # 解析新版热搜结构
                return [f"{item.get('show_name', '')} 👀{index+1}位" 
                        for index, item in enumerate(data.get('data',{}).get('trending',{}).get('list',[])[:10])]
            return []
        
        elif platform == "头条":
            response = requests.get(HOT_API_CONFIG[platform], headers=headers)
            if response.status_code == 200:
                data = response.json()
                # 强化解析逻辑
                return [f"{item.get('Title', item.get('title', ''))} 🔥{item.get('HotValue',0)//10000}万" 
                        for item in data.get('data',[])[:10]]
            return []
        
    except Exception as e:
        print(f"获取{platform}热榜失败: {str(e)}")
        return []

# ===== 智能台词生成 =====
def generate_trendy_script(prompt, platform):
    """生成符合平台流行风格的台词"""
    platform_rules = PLATFORM_RULES.get(platform, {})
    trendy_phrases = platform_rules.get("话术", []) + TRENDY_PHRASES
    
    # 提取复杂表达式到变量
    sample_size = min(3, len(trendy_phrases))
    sampled_phrases = random.sample(trendy_phrases, sample_size)
    
    trendy_prompt = f"""
    你是一位{platform}爆款内容创作专家，请根据以下要求生成短视频脚本：
    {prompt}
    
    平台特色：
    {json.dumps(platform_rules, indent=2, ensure_ascii=False)}
    
    额外要求：
    1. 台词要符合2025年最新网络流行语
    2. 每句台词控制在15字以内
    3. 加入情感共鸣点
    4. 使用平台特色表达方式
    5. 包含悬念、反转、情感共鸣等爆款元素
    6. 至少包含3个热门表达：{sampled_phrases}
    """
    
    try:
        response = requests.post(
            active_api_url,
            headers={"Authorization": f"Bearer {MOONSHOT_API_KEY}"},
            json={
                "model": "moonshot-v1-8k",
                "messages": [{"role": "user", "content": trendy_prompt}],
                "temperature": 0.9,
                "max_tokens": 3000
            },
            timeout=30  # 增加超时时间
        )
        
        # 检查响应状态
        if response.status_code != 200:
            error_detail = response.json().get("error", {}).get("message", "未知错误") if response.content else "无错误详情"
            return f"⚠️ API错误({response.status_code}): {error_detail}"
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        st.error("API请求超时，正在重试...")
        time.sleep(2)
        return generate_trendy_script(prompt, platform)  # 重试一次
    except Exception as e:
        return f"⚠️ 生成失败：{str(e)}"

# ===== AI生成核心 =====
def generate_script(topic, audience, style, platform, category, scene_count, hot_keywords):
    # 根据分镜数量动态调整提示词
    scene_prompt = ""
    if scene_count <= 15:
        scene_prompt = "节奏紧凑，1-2秒一个镜头"
    elif scene_count <= 30:
        scene_prompt = "中等节奏，2-3秒一个镜头"
    else:
        scene_prompt = "节奏舒缓，3-4秒一个镜头"
    
    # 获取平台规则
    platform_rules = PLATFORM_RULES.get(platform, {})
    
    # 构建热点提示
    hot_prompt = ""
    if hot_keywords:
        keywords = [k.strip() for k in hot_keywords.split(',') if k.strip()]
        if keywords:
            hot_prompt = f"\n【热点关键词】{', '.join(keywords)}\n要求：至少包含2个热点关键词"
    
    # 使用平台特定的爆款结构
    structure = "\n".join(platform_rules.get("爆款结构", [
        "1. 0-3秒：悬念开场（疑问句+特写）",
        "2. 3-8秒：价值展示（核心看点）",
        "3. 8-15秒：情感共鸣（痛点/爽点）",
        "4. 15秒后：反转/高潮（意外惊喜）",
        "5. 结尾：行动召唤（关注+互动）"
    ]))
    
    prompt = f"""你是一位精通{platform}平台的短视频专家，请为{audience}生成{style}风格的{category}类脚本：
    
【主题】{topic}
【风格】{style}
【分类】{category}
【分镜数量】{scene_count}个 ({scene_prompt})
【平台规则】{json.dumps(platform_rules, indent=2, ensure_ascii=False)}
{hot_prompt}

【爆款结构】
{structure}

【要求】
1. 按表格输出{scene_count}个分镜 [序号|类型|画面|台词|时长|运镜|字幕|音乐]
2. 开头3秒必须使用"{platform_rules.get('opening', ['疑问句+特写镜头'])[0]}"制造悬念
3. 第8-10秒设置情感共鸣点
4. 第15秒左右安排剧情反转
5. 结尾引导关注和@好友
6. 台词使用{platform}特色话术
7. 时长列填写数字（单位：秒）
8. 运镜方式：推/拉/摇/移/跟/甩/升降
9. 字幕样式：大标题/底部字幕/动态字/无
10. 背景音乐：悬疑/欢快/抒情/热血/无

【示例格式】
| 序号 | 类型 | 画面 | 台词 | 时长 | 运镜 | 字幕 | 音乐 |
|------|------|------|------|------|------|------|------|
| 1 | 特写 | 手机显示凌晨3点 | "{random.choice(platform_rules.get('话术', ['考研人的夜有多长？']))}" | 2 | 推 | 大标题 | 悬疑 |
| 2 | 中景 | 主人公揉眼睛看手机 | "{random.choice(platform_rules.get('话术', ['但这次，我真的拼了！']))}" | 3 | 拉 | 底部字幕 | 励志 |"""
    
    try:
        start_time = time.time()
        # 获取基础脚本（增加重试机制）
        base_response = None
        for attempt in range(3):  # 最多重试3次
            try:
                base_response = requests.post(
                    active_api_url,
                    headers={"Authorization": f"Bearer {MOONSHOT_API_KEY}"},
                    json={
                        "model": "moonshot-v1-8k",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.75,
                        "max_tokens": 4000
                    },
                    timeout=45  # 增加超时时间
                )
                if base_response.status_code == 200:
                    break
                elif base_response.status_code == 429:  # 过多请求
                    wait_time = 2 * (attempt + 1)
                    st.warning(f"API请求过于频繁，等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
            except requests.exceptions.Timeout:
                wait_time = 3 * (attempt + 1)
                st.warning(f"API请求超时，{wait_time}秒后重试...")
                time.sleep(wait_time)
                continue
            except Exception as e:
                return f"⚠️ API请求失败: {str(e)}", None
        
        # 检查响应状态
        if not base_response:
            return "⚠️ API无响应：请检查网络连接或API服务状态", None
        if base_response.status_code != 200:
            error_detail = ""
            try:
                error_data = base_response.json()
                error_detail = error_data.get("error", {}).get("message", "未知错误")
            except:
                error_detail = base_response.text[:200] + "..." if base_response.text else "无错误详情"
            return f"⚠️ API错误({base_response.status_code}): {error_detail}", None
        
        base_data = base_response.json()
        base_content = base_data["choices"][0]["message"]["content"]
        
        # 改进表格解析逻辑
        table_lines = []
        if "|" in base_content:
            lines = base_content.split('\n')
            table_started = False
            
            for line in lines:
                # 找到表格开始位置
                if '|' in line and '---' in line:
                    table_started = True
                    continue
                    
                if table_started and '|' in line:
                    # 移除行首尾的管道符号
                    cleaned_line = line.strip().strip('|')
                    parts = [p.strip() for p in cleaned_line.split('|')]
                    
                    # 只处理包含7-8列的行
                    if 7 <= len(parts) <= 8:
                        # 如果第一列是数字序号，则保留
                        if len(parts) == 8 and parts[0].isdigit():
                            table_lines.append(parts)
                        elif len(parts) == 7:
                            # 添加序号
                            table_lines.append([str(len(table_lines)+1)] + parts)
        
        processing_time = time.time() - start_time
        st.toast(f"生成完成! 耗时: {processing_time:.1f}秒")
        
        if table_lines:
            # 创建DataFrame
            df = pd.DataFrame(table_lines)
            if len(df.columns) == 8:
                df.columns = ["序号", "类型", "画面", "台词", "时长", "运镜", "字幕", "音乐"]
                # 确保时长是数值类型
                try:
                    df["时长"] = pd.to_numeric(df["时长"], errors="coerce")
                    df["时长"].fillna(2.0, inplace=True)  # 默认2秒
                except:
                    df["时长"] = [2.0] * len(df)
                return base_content, df
            else:
                return base_content, None
        else:
            return base_content, None
            
    except Exception as e:
        return f"⚠️ 生成失败：{str(e)}", None

# ===== 用户界面 =====
st.set_page_config(
    page_title="高级短视频脚本生成器",
    layout="wide",
    page_icon="🎥",
    initial_sidebar_state="expanded"
)

# 注入DeepSeek风格的CSS
st.markdown("""
<style>
/* 全局样式 */
body {
    background-color: #f5f7fb;
    color: #333;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* 主标题 */
h1 {
    color: #2d3e50;
    border-bottom: 2px solid #4e8cff;
    padding-bottom: 10px;
    font-weight: 700;
}

/* 容器样式 */
.stContainer, .stApp {
    background-color: #ffffff;
}

/* 侧边栏 */
.css-1d391kg {
    background-color: #f0f4f8;
    border-right: 1px solid #e1e8f0;
}

/* 按钮样式 */
.stButton>button {
    background-color: #4e8cff;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 10px 24px;
    font-weight: 600;
    transition: all 0.3s;
}

.stButton>button:hover {
    background-color: #3a75e0;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(78, 140, 255, 0.25);
}

/* 新增输入框样式修复 */
.stTextInput>div>div>input {
    line-height: 1.8 !important;
    padding: 12px 16px !important;
    min-height: 56px !important;
    font-size: 16px;
}

.stTextInput>div>div>input:focus {
    box-shadow: 0 0 0 3px rgba(78, 140, 255, 0.25) !important;
}

/* 选择框样式 */
.stSelectbox>div>div>div>div {
    padding: 10px 14px !important;
    line-height: 1.5;
}
            
/* 滑块样式 */
.stSlider .st-ae {
    background-color: #4e8cff;
}

.stSlider .st-bd {
    background-color: #e1e8f0;
}

/* 表格样式 */
.stDataFrame {
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.stDataFrame thead th {
    background-color: #f0f4f8;
    font-weight: 600;
}

.stDataFrame tbody tr:nth-child(even) {
    background-color: #f9fbfd;
}

/* 卡片样式 */
.stAlert {
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    padding: 20px;
    background-color: #ffffff;
    border-left: 4px solid #4e8cff;
}

/* 警告信息 */
.stAlert.stWarning {
    border-left: 4px solid #f0ad4e;
}

/* 错误信息 */
.stAlert.stError {
    border-left: 4px solid #d9534f;
}

/* 成功信息 */
.stAlert.stSuccess {
    border-left: 4px solid #5cb85c;
}

/* 信息框 */
.stAlert.stInfo {
    border-left: 4px solid #5bc0de;
}

/* 分割线 */
hr {
    border: 0;
    height: 1px;
    background: linear-gradient(to right, transparent, #d1d8e0, transparent);
    margin: 24px 0;
}

/* 标签样式 */
.stMarkdown h2 {
    color: #2d3e50;
    font-weight: 600;
    margin-top: 1.5em;
}

.stMarkdown h3 {
    color: #3a506b;
    font-weight: 600;
}

/* 代码块样式 */
.stCodeBlock {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    border: 1px solid #e1e8f0;
}

/* 底部信息 */
footer {
    text-align: center;
    color: #7b8794;
    font-size: 0.85em;
    padding: 15px 0;
}

/* 表单容器 */
.stForm {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 25px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
    border: 1px solid #e1e8f0;
}

/* 扩展面板 */
.stExpander {
    border-radius: 12px;
    border: 1px solid #e1e8f0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.03);
}

.stExpander .st-emotion-cache-1c7y2kd {
    border-radius: 12px;
}

/* 热榜样式 */
.hot-item {
    line-height: 1.6;
    padding: 12px 16px;
}

.hot-item:hover {
    background-color: #e1e8f0;
    transform: translateX(3px);
}

.hot-rank {
    display: inline-block;
    width: 24px;
    height: 24px;
    line-height: 24px;
    text-align: center;
    background-color: #4e8cff;
    color: white;
    border-radius: 4px;
    margin-right: 8px;
    font-weight: bold;
}

.hot-platform {
    font-size: 12px;
    color: #7b8794;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

# 显示API状态
st.sidebar.markdown(f"### API状态")
st.sidebar.success(f"✅ Moonshot API 已连接")
st.sidebar.caption(f"使用端点: {active_api_url}")
st.sidebar.caption(f"密钥: {MOONSHOT_API_KEY[:8]}...{MOONSHOT_API_KEY[-4:]}")

# 顶部区域
with st.container():
    st.title("🎬 AI短视频脚本生成器")
    st.caption("专业脚本创作平台 | 智能分镜设计 | 流行台词生成 | 剪映创作助手")

# 动态时钟
create_live_clock()

# 实时热榜展示
st.subheader("🔥 实时热榜参考")
tab1, tab2, tab3 = st.tabs(["抖音热榜", "B站热榜", "头条热榜"])

with tab1:
    with st.spinner('获取抖音热榜中...'):
        douyin_hot = fetch_hotlist("抖音")
        if douyin_hot:
            for i, item in enumerate(douyin_hot[:10]):
                # 提取纯文本（去除热度值）
                clean_item = re.sub(r'🔥\d+万$', '', item).strip()
                st.markdown(
                    f'<div class="hot-item" onclick="document.getElementById(\'topic_input\').value = \'{clean_item}\'">'
                    f'<div class="hot-platform">抖音热榜</div>'
                    f'<span class="hot-rank">{i+1}</span> {item}'
                    '</div>',
                    unsafe_allow_html=True
                )
        else:
            st.warning("抖音热榜获取失败，请稍后重试")

with tab2:  # B站热榜Tab
    with st.spinner('获取B站热榜中...'):
        bili_hot = fetch_hotlist("B站")
        if bili_hot:
            for i, item in enumerate(bili_hot[:10]):
                # 优化内容提取逻辑
                clean_item = re.sub(r'👀\d+位$', '', item).strip()
                st.markdown(
                    f'<div class="hot-item" onclick="document.getElementById(\'topic_input\').value = \'{clean_item}\'">'
                    f'<div class="hot-platform">B站实时热搜</div>'
                    f'<span class="hot-rank">{i+1}</span> {item}'
                    '</div>', 
                    unsafe_allow_html=True
                )
        else:
            st.warning("B站热榜获取失败，请稍后重试")

with tab3:
    with st.spinner('获取头条热榜中...'):
        toutiao_hot = fetch_hotlist("头条")
        if toutiao_hot:
            for i, item in enumerate(toutiao_hot[:10]):
                # 提取纯文本（去除热度值）
                clean_item = re.sub(r'🔥\d+万$', '', item).strip()
                st.markdown(
                    f'<div class="hot-item" onclick="document.getElementById(\'topic_input\').value = \'{clean_item}\'">'
                    f'<div class="hot-platform">头条热榜</div>'
                    f'<span class="hot-rank">{i+1}</span> {item}'
                    '</div>',
                    unsafe_allow_html=True
                )
        else:
            st.warning("头条热榜获取失败，请稍后重试")

# 主表单区
with st.form("script_form", border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input("视频主题*", placeholder="例：北京胡同美食探索/迪士尼亲子游vlog", 
                             help="越具体越好，如'三里屯网红店打卡'而非'美食探店'",
                             key="topic_input")
        audience = st.selectbox("目标受众*", TARGET_AUDIENCES, index=0)
        scene_count = st.slider("分镜数量", 6, 58, 12, help="6-15:快节奏 16-30:中等节奏 31-58:慢节奏")
        
    with col2:
        style = st.selectbox("视频风格*", VIDEO_STYLES, index=0)
        platform = st.selectbox("发布平台*", ["抖音", "快手", "B站", "视频号", "小红书"])
        category = st.selectbox("视频分类*", VIDEO_CATEGORIES, index=0)
    
    hot_keywords_input = st.text_input("热点关键词（可选）", placeholder="输入热点关键词，多个用逗号分隔", 
                                     help="输入热点关键词，多个用逗号分隔")
    
    submitted = st.form_submit_button("✨ 生成专业脚本", type="primary", use_container_width=True)
    
    if submitted:
        if not topic.strip():
            st.warning("请填写视频主题")
        else:
            with st.spinner(f'AI创作中...正在生成{scene_count}个分镜脚本'):
                result, result_df = generate_script(topic, audience, style, platform, category, scene_count, hot_keywords_input)
                
                # 存储结果在 session state 中
                st.session_state['script_result'] = result
                st.session_state['script_topic'] = topic
                st.session_state['script_platform'] = platform
                st.session_state['script_df'] = result_df
                
                # 结果展示
                if result_df is not None:
                    st.success("🎉 脚本生成成功!")
                    
                    # 显示流行短语标签
                    st.subheader("🔥 使用的流行短语")
                    platform_rules = PLATFORM_RULES.get(platform, {})
                    trendy_phrases = platform_rules.get("话术", []) + TRENDY_PHRASES
                    
                    if trendy_phrases and len(trendy_phrases) >= 5:
                        selected_phrases = random.sample(trendy_phrases, min(5, len(trendy_phrases)))
                        st.write(" | ".join([f"`{phrase}`" for phrase in selected_phrases]))
                    else:
                        st.warning("无法加载流行短语库")
                    
                    # 表格处理
                    st.divider()
                    st.subheader("📽️ 分镜脚本详情 (可编辑调整)")
                    
                    # 添加时长调整滑块
                    st.caption("调整整体节奏:")
                    total_duration = st.slider("总时长调整(秒)", 15, 180, 60, 
                                              help="调整后AI会自动重新分配各分镜时长")
                    
                    # 可编辑表格
                    edited_df = st.data_editor(
                        result_df,
                        column_config={
                            "时长": st.column_config.NumberColumn(
                                "时长(秒)",
                                help="每个分镜时长(秒)",
                                min_value=0.5,
                                max_value=10,
                                step=0.5,
                                format="%.1f s"
                            ),
                            "运镜": st.column_config.SelectboxColumn(
                                "运镜方式",
                                options=["推", "拉", "摇", "移", "跟", "甩", "升降"]
                            ),
                            "字幕": st.column_config.SelectboxColumn(
                                "字幕样式",
                                options=["大标题", "底部字幕", "动态字", "无"]
                            ),
                            "音乐": st.column_config.SelectboxColumn(
                                "背景音乐",
                                options=["悬疑", "欢快", "抒情", "热血", "无"]
                            )
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=min(600, 45 * len(result_df) + 45),
                        num_rows="fixed"
                    )
                    
                    # 保存编辑后的df
                    st.session_state['edited_df'] = edited_df
                    
                    # 显示关键节点
                    st.divider()
                    st.subheader("⏱️ 关键节点分析")
                    
                    # 确保时长是数值类型
                    try:
                        edited_df["时长"] = pd.to_numeric(edited_df["时长"], errors="coerce")
                        edited_df["时长"].fillna(2.0, inplace=True)
                    except:
                        edited_df["时长"] = [2.0] * len(edited_df)
                    
                    # 计算累计时间
                    edited_df["累计时间"] = edited_df["时长"].cumsum()
                    
                    # 查找关键帧
                    key_frames = []
                    platform_rules = PLATFORM_RULES.get(platform, {})
                    
                    for _, row in edited_df.iterrows():
                        time_point = row["累计时间"]
                        if time_point <= 3:
                            key_frames.append(f"🔥 开场(0-3秒): {row['台词']} ({platform_rules.get('opening', ['悬念开场'])[0]})")
                        elif 3 < time_point <= 8:
                            key_frames.append(f"💎 价值展示(3-8秒): {row['台词']}")
                        elif 8 < time_point <= 15:
                            key_frames.append(f"❤️ 情感共鸣(8-15秒): {row['台词']}")
                        elif 15 < time_point <= 25:
                            key_frames.append(f"🎭 剧情反转(15-25秒): {row['台词']}")
                        elif time_point > edited_df["累计时间"].max() - 5:
                            key_frames.append(f"📢 结尾引导: {row['台词']} ({platform_rules.get('interaction', ['互动引导'])[0]})")
                    
                    # 显示关键帧
                    for frame in key_frames[:5]:  # 最多显示5个关键帧
                        st.info(frame)
                        
                else:
                    st.error("⚠️ 脚本解析失败，请重试或减少分镜数量")
                    st.code(result)

# 下载按钮 - 放在表单外部
if 'script_df' in st.session_state and st.session_state['script_df'] is not None:
    df = st.session_state.get('edited_df', st.session_state['script_df'])
    
    # 创建两种下载格式
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV下载
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 下载脚本(CSV)",
            data=csv,
            file_name=f"{st.session_state.get('script_topic', '脚本')}_{st.session_state.get('script_platform', '')}_脚本.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # 剪映格式下载
        # 生成剪映专用格式的文本
        jianying_content = f"""剪映脚本模板
视频主题: {st.session_state.get('script_topic', '')}
发布平台: {st.session_state.get('script_platform', '')}
分镜数量: {len(df)}
总时长: {df['时长'].sum():.1f}秒

【分镜详情】
"""
        for i, row in df.iterrows():
            jianying_content += f"""
分镜 {i+1}:
- 类型: {row['类型']}
- 画面: {row['画面']}
- 台词: {row['台词']}
- 时长: {row['时长']}秒
- 运镜: {row['运镜']}
- 字幕: {row['字幕']}
- 音乐: {row['音乐']}
"""
        st.download_button(
            label="🎞️ 剪映专用格式",
            data=jianying_content.encode('utf-8'),
            file_name=f"{st.session_state.get('script_topic', '脚本')}_剪映脚本.txt",
            mime="text/plain",
            use_container_width=True
        )

# 平台创作指南
with st.expander("📚 平台创作指南 & 剪映技巧", expanded=True):
    platform = st.session_state.get('script_platform', '抖音')
    platform_rules = PLATFORM_RULES.get(platform, {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"{platform}平台爆款公式")
        st.markdown(f"""
        **🔥 黄金结构：**
        {"  \n".join(platform_rules.get("爆款结构", [
            "1. 0-3秒：悬念开场（疑问句+特写）",
            "2. 3-8秒：价值展示（核心看点）",
            "3. 8-15秒：情感共鸣（痛点/爽点）",
            "4. 15秒后：反转/高潮（意外惊喜）",
            "5. 结尾：行动召唤（关注+互动）"
        ]))}
        
        **🎯 平台特色：**
        - 视频长度：{platform_rules.get('length', '15-60秒')}
        - 视觉风格：{platform_rules.get('visual', platform_rules.get('aesthetic', '高饱和'))}
        - 互动方式：{platform_rules.get('interaction', '点赞/评论')}
        """)
    
    with col2:
        st.subheader("✂️ 剪映专业技巧")
        st.markdown("""
        **1. 分镜衔接技巧：**
        - 动作匹配剪辑：动作接动作
        - 跳切制造节奏感
        - J-cut（先闻其声后见其人）
        
        **2. 字幕特效指南：**
        **剪映字幕参数设置：**
        ```
        字体: 思源黑体 
        字号: 主标题72 / 副标题48
        颜色: (主色) (白)
        描边: #000000 (黑色描边)
        阴影: 5
        动画: 弹入+弹出
        ```
        
        **3. 背景音乐搭配：**
        | 段落     | 音乐类型       | 音量   | 特效               |
        |----------|----------------|--------|--------------------|
        | 开场     | 悬疑音效       | 100%   | 低音增强           |
        | 高潮     | 鼓点/重音      | 80%    | 空间混响           |
        | 结尾     | 渐弱收尾       | 60%→0  | 淡出效果           |
        """)
        
# 底部信息
st.divider()
st.caption("""
© 2025 高级短视频脚本生成器 | 支持剪映专业版脚本导入 | 
技术支持: mrxie17@163.com | 
版本: 0.5 内测版
           
注:测试版本不代表最终品质
""")

# 添加JS代码使热榜点击功能生效
st.markdown("""
<script>
document.addEventListener('click', function(e) {
    if (e.target.closest('.hot-item')) {
        const item = e.target.closest('.hot-item');
        const text = item.textContent.replace(/抖音热榜|B站热榜|头条热榜|\d/g, '').trim();
        document.getElementById('topic_input').value = text;
    }
});
</script>
""", unsafe_allow_html=True)