# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time  # 新增用于请求限速

# ===== 用户配置区 =====

MOONSHOT_API_KEY = "sk-sqrfIzSxn92laOhBxS9HSMZ6Y4itPpZ70Z49v1pWnIl7RgQb"  # 👈 替换这里
MOONSHOT_API_URL = "https://api.moonshot.cn/v1/chat/completions"

# ===== 修复后的AI生成核心 =====
def generate_script(topic, audience, style, platform):
    prompt = f"""你是一位精通{platform}平台的短视频专家，请为{audience}生成脚本：
    
【主题】{topic}
【风格】{style}
【要求】
1. 按表格输出6个分镜 [镜头序号|类型|画面|台词|时长|运镜]
2. 开头3秒使用"疑问句+特写镜头"制造悬念
3. 第10秒添加互动话术
4. 结尾引导关注和@好友

【输出示例】
| 镜头 | 类型 | 画面 | 台词 | 时长 | 运镜 |
|------|------|------|------|------|------|
| 1 | 特写 | 手机显示凌晨3点 | "考研人的夜有多长？" | 2s | 推镜头 |"""
    
    try:
        # 添加请求限速（Moonshot免费版限频）
        time.sleep(1)  
        
        response = requests.post(
            MOONSHOT_API_URL,
            headers={
                "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "moonshot-v1-8k",  # 确认使用可用模型
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000,
                "top_p": 0.9
            },
            timeout=15  # 设置超时时间
        )
        
        # 增强错误处理
        response.raise_for_status()  # 自动捕获HTTP错误
        result = response.json()
        
        # 检查响应结构
        if not result.get("choices"):
            error_msg = result.get("error", {}).get("message", "API返回格式异常")
            return f"⚠️ 生成失败：{error_msg}\n\n完整响应：{result}"
            
        return result["choices"][0]["message"]["content"]
        
    except requests.exceptions.RequestException as e:
        return f"⚠️ 网络请求失败：{str(e)}"
    except Exception as e:
        return f"⚠️ 系统错误：{str(e)}"

# ===== 用户界面 =====
st.set_page_config(
    page_title="校园短视频助手",
    page_icon="🎬",
    layout="wide"
)

st.title("🎥 AI短视频脚本生成器（修复版）")
st.caption(f"最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

with st.sidebar:
    st.success("✅ 已修复常见API错误")
    st.warning("注意：请勿公开分享API密钥")

with st.form("script_form"):
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("视频主题", placeholder="例：军训生存指南/宿舍美食DIY")
        audience = st.selectbox("目标受众", ["高一新生", "高二学生", "社团成员", "校园情侣"])
    with col2:
        style = st.selectbox("视频风格", ["幽默搞笑", "知识干货", "情感治愈", "热血励志"])
        platform = st.radio("发布平台", ["抖音", "快手", "B站"], horizontal=True)
    
    if st.form_submit_button("✨ 生成脚本", type="primary"):
        with st.spinner('AI正在创作中...'):
            result = generate_script(topic, audience, style, platform)
            
            # 增强结果解析
            if "|" in result:
                st.success("生成成功！")
                try:
                    # 提取表格部分
                    table_lines = [line for line in result.split('\n') 
                                 if '|' in line and '---' not in line and line.strip()]
                    if len(table_lines) > 1:
                        # 创建DataFrame
                        df = pd.DataFrame(
                            [line.split('|')[1:-1] for line in table_lines],
                            columns=["镜头", "类型", "画面", "台词", "时长", "运镜"]
                        )
                        st.dataframe(
                            df.style.set_properties(**{
                                'text-align': 'left',
                                'white-space': 'pre-wrap'
                            }),
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.write(result)  # 非表格格式直接显示
                except Exception as e:
                    st.warning(f"表格解析失败：{str(e)}")
                    st.code(result)  # 显示原始内容
            else:
                st.error(result)  # 显示错误信息

# 移动端适配
st.markdown("""
<style>
@media (max-width: 600px) {
    .stTextInput input, .stSelectbox select {
        font-size: 14px !important;
    }
}
</style>
""", unsafe_allow_html=True)