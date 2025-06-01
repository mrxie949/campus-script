# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import pytz
from streamlit.components.v1 import html

# ===== 动态时钟组件 =====
def create_live_clock():
    """创建实时更新的北京时间时钟"""
    clock_js = """
    <div style="text-align:center;margin-bottom:20px;">
        <div id="clock" style="font-size:28px;font-weight:bold;color:#2563EB;"></div>
        <div style="font-size:16px;color:#6B7280;">北京时间</div>
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
MOONSHOT_API_KEY = "sk-sqrfIzSxn92laOhBxS9HSMZ6Y4itPpZ70Z49v1pWnIl7RgQb"
MOONSHOT_API_URL = "https://api.moonshot.cn/v1/chat/completions"

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

# ===== 智能台词生成 =====
def generate_trendy_script(prompt, scene_count):
    """生成符合抖音流行风格的台词"""
    trendy_prompt = f"""
    你是一位抖音爆款内容创作专家，请根据以下要求生成短视频脚本：
    {prompt}
    
    额外要求：
    1. 台词要符合2025年最新网络流行语
    2. 至少包含3个热门表达（如"绝绝子"、"YYDS"等）
    3. 每句台词控制在15字以内
    4. 加入情感共鸣点
    5. 使用年轻人喜欢的表达方式
    """
    
    try:
        response = requests.post(
            MOONSHOT_API_URL,
            headers={"Authorization": f"Bearer {MOONSHOT_API_KEY}"},
            json={
                "model": "moonshot-v1-8k",
                "messages": [{"role": "user", "content": trendy_prompt}],
                "temperature": 0.85,  # 更高的创造性
                "max_tokens": 2000
            },
            timeout=15
        )
        
        # 检查响应状态
        if response.status_code != 200:
            return f"⚠️ API错误: {response.status_code}"
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ 生成失败：{str(e)}"

# ===== AI生成核心 =====
def generate_script(topic, audience, style, platform, category, scene_count):
    prompt = f"""你是一位精通{platform}平台的短视频专家，请为{audience}生成{style}风格的{category}类脚本：
    
【主题】{topic}
【风格】{style}
【分类】{category}
【要求】
1. 按表格输出{scene_count}个分镜 [镜头序号|类型|画面|台词|时长|运镜]
2. 开头3秒使用"疑问句+特写镜头"制造悬念
3. 第10秒添加互动话术
4. 结尾引导关注和@好友
5. 台词使用2025年最新网络流行语

【示例格式】
| 镜头 | 类型 | 画面 | 台词 | 时长 | 运镜 |
|------|------|------|------|------|------|
| 1 | 特写 | 手机显示凌晨3点 | "考研人的夜有多长？" | 2s | 推镜头 |"""
    
    try:
        start_time = time.time()
        # 先获取基础脚本
        base_response = requests.post(
            MOONSHOT_API_URL,
            headers={"Authorization": f"Bearer {MOONSHOT_API_KEY}"},
            json={
                "model": "moonshot-v1-8k",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000
            },
            timeout=15
        )
        
        # 检查响应状态
        if base_response.status_code != 200:
            return f"⚠️ API错误: {base_response.status_code}", []
        
        base_data = base_response.json()
        base_content = base_data["choices"][0]["message"]["content"]
        
        # 提取台词部分进行流行语优化
        if "|" in base_content:
            lines = base_content.split('\n')
            dialogue_lines = []
            for line in lines:
                if '|' in line and len(line.split('|')) > 4:
                    parts = line.split('|')
                    dialogue_lines.append(parts[4].strip())  # 台词在第四列
            
            # 生成优化后的台词
            dialogue_prompt = "生成符合抖音流行趋势的短视频台词，要求使用最新网络用语：\n"
            for i, dialogue in enumerate(dialogue_lines[:min(6, len(dialogue_lines))]):
                dialogue_prompt += f"{i+1}. {dialogue}\n"
            
            trendy_dialogues = generate_trendy_script(dialogue_prompt, scene_count)
            
            # 替换原始台词
            trendy_lines = trendy_dialogues.split('\n')
            new_content = []
            dialogue_index = 0
            
            for line in lines:
                if '|' in line and len(line.split('|')) > 4 and dialogue_index < len(trendy_lines):
                    parts = line.split('|')
                    parts[4] = " " + trendy_lines[dialogue_index].strip() + " "
                    new_content.append('|'.join(parts))
                    dialogue_index += 1
                else:
                    new_content.append(line)
            
            final_content = '\n'.join(new_content)
        else:
            final_content = base_content
        
        processing_time = time.time() - start_time
        st.toast(f"生成完成! 耗时: {processing_time:.1f}秒")
        
        return final_content, []
    except Exception as e:
        return f"⚠️ 生成失败：{str(e)}", []

# ===== 用户界面 =====
st.set_page_config(
    page_title="高级短视频脚本生成器",
    layout="wide",
    page_icon="🎥",
    initial_sidebar_state="expanded"
)

# 顶部区域 - 动态时钟
st.markdown("""
<style>
.clock-container {
    background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
    border-radius: 15px;
    padding: 15px 0;
    margin-bottom: 25px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.clock-title {
    text-align: center;
    color: white;
    font-size: 18px;
    margin-bottom: 5px;
}
</style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="clock-container"><div class="clock-title">北京时间</div></div>', unsafe_allow_html=True)
    create_live_clock()

# 主标题
st.title("🎬 AI短视频脚本生成器")
st.caption("专业脚本创作平台 | 智能分镜设计 | 流行台词生成")

# 主表单区
with st.form("script_form", border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input("视频主题*", placeholder="例：北京胡同美食探索/迪士尼亲子游vlog", 
                             help="越具体越好，如'三里屯网红店打卡'而非'美食探店'")
        audience = st.selectbox("目标受众*", TARGET_AUDIENCES, index=0)
        scene_count = st.slider("分镜数量", 6, 12, 8, help="建议6-12个分镜效果最佳")
        
    with col2:
        style = st.selectbox("视频风格*", VIDEO_STYLES, index=0)
        platform = st.selectbox("发布平台*", ["抖音", "快手", "B站", "视频号", "小红书"])
        category = st.selectbox("视频分类*", VIDEO_CATEGORIES, index=0)
    
    submitted = st.form_submit_button("✨ 生成专业脚本", type="primary", use_container_width=True)
    
    if submitted:
        if not topic.strip():
            st.warning("请填写视频主题")
        else:
            with st.spinner('AI创作中...正在生成流行台词和分镜'):
                result, _ = generate_script(topic, audience, style, platform, category, scene_count)
                
                # 结果展示
                if "|" in result:
                    st.success("🎉 脚本生成成功!")
                    
                    # 显示流行短语标签
                    st.subheader("🔥 使用的流行短语")
                    selected_phrases = random.sample(TRENDY_PHRASES, min(5, len(TRENDY_PHRASES)))
                    st.write(" | ".join([f"`{phrase}`" for phrase in selected_phrases]))
                    
                    # 表格处理
                    st.divider()
                    st.subheader("📽️ 分镜脚本详情")
                    table_lines = [line for line in result.split('\n') 
                                  if '|' in line and '---' not in line and line.strip()]
                    
                    if table_lines:
                        try:
                            # 创建DataFrame
                            df = pd.DataFrame([line.split('|')[1:-1] for line in table_lines])
                            if len(df.columns) == 6:
                                df.columns = ["镜头", "类型", "画面", "台词", "时长", "运镜"]
                            
                            # 高亮显示流行台词
                            def highlight_trendy(text):
                                for phrase in TRENDY_PHRASES:
                                    if phrase in text:
                                        return f'<span style="background-color:#FFE066;border-radius:3px;">{text}</span>'
                                return text
                            
                            # 显示表格
                            st.dataframe(
                                df.style.map(lambda x: highlight_trendy(x) if isinstance(x, str) else x),
                                hide_index=True,
                                use_container_width=True,
                                height=min(600, 45 * len(df) + 45)
                            )
                            
                            # 下载功能
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="💾 下载脚本(CSV)",
                                data=csv,
                                file_name=f"{topic}_{platform}_脚本.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        except:
                            st.code(result)
                    else:
                        st.write(result)
                else:
                    st.error(result)

# 使用指南
with st.expander("📚 创作指南 & 热门趋势", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🔥 2025年热门趋势：**
        - **流行风格**：多巴胺配色 | 新中式美学 | 赛博朋克
        - **热门台词**：""")
        st.write(" | ".join(TRENDY_PHRASES[:6]))
        st.markdown("""
        - **爆款结构**：
          1. 0-3秒：悬念钩子（问题/冲突）
          2. 3-8秒：价值展示（亮点/效果）
          3. 8-15秒：情感共鸣（痛点/梦想）
          4. 结尾：互动引导（评论/关注）
        """)
    
    with col2:
        st.markdown("""
        **💡 创作技巧：**
        1. **标题公式**：  
           `数字+形容词+关键词+emoji`  
           例：5个超简单构图技巧📸秒变摄影大神
           
        2. **开场技巧**：  
           - 提出问题："你知道...吗？"  
           - 制造冲突："千万别再..."  
           - 展示结果："三天后我惊呆了！"
           
        3. **平台差异**：  
           - 抖音：快节奏+强音乐  
           - B站：深度内容+进度条  
           - 小红书：高颜值+干货标签
        """)

# 底部信息
st.divider()
st.caption("""
© 2025 高级短视频脚本生成器 | 此工具仅供交流参考 | 
技术支持: mrxie17@qq.com | 
版本: 1.0 标准版
""")