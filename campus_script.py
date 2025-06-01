# -*- coding: utf-8 -*-
import streamlit as st
import requests
import os
from datetime import datetime

# ===== 配置区（你只需要改这里！）=====
MOONSHOT_API_KEY = os.environ.get("sk-sqrfIzSxn92laOhBxS9HSMZ6Y4itPpZ70Z49v1pWnIl7RgQb")  # 自动从环境变量读取

# ===== 核心功能 =====
def generate_script(topic, audience, style, platform):
    prompt = f"""你是一位短视频专家，请为{audience}生成{platform}平台脚本：
主题：{topic}
风格：{style}
要求：
1. 包含5个分镜 [镜头类型|画面描述|台词|时长]
2. 开头3秒有反转悬念
3. 第10秒引导互动
4. 结尾@好友"""
    
    try:
        response = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={"Authorization": f"Bearer {MOONSHOT_API_KEY}"},
            json={
                "model": "moonshot-v1-8k",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"生成失败：{str(e)}"

# ===== 用户界面 =====
st.set_page_config(page_title="校园短视频助手", layout="wide")
st.title("🎥 AI短视频脚本生成器（测试）")

with st.form("my_form"):
    topic = st.text_input("视频主题", placeholder="例：军训生活/宿舍美食/特色小吃")
    col1, col2 = st.columns(2)
    with col1:
        audience = st.selectbox("目标受众", ["高一新生", "高二学生", "社团成员", "摄影师",'二次元'])
    with col2:
        style = st.selectbox("视频风格", ["幽默搞笑", "知识干货", "情感治愈", "热血励志"])
    platform = st.radio("发布平台", ["抖音", "快手", "B站"], horizontal=True)
    
    if st.form_submit_button("✨ 生成脚本"):
        with st.spinner('AI正在创作中...'):
            result = generate_script(topic, audience, style, platform)
            st.success("生成成功！")
            st.write(result)

# 移动端适配
st.write('<meta name="viewport" content="width=device-width">', unsafe_allow_html=True)