# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os  # 新增环境变量支持

# ===== 配置区 =====
MOONSHOT_API_KEY = os.environ.get("sk-sqrfIzSxn92laOhBxS9HSMZ6Y4itPpZ70Z49v1pWnIl7RgQb")  # 从环境变量读取
MOONSHOT_API_URL = "https://api.moonshot.cn/v1/chat/completions"

def generate_script(topic, audience, style, platform):
    prompt = f"""你是一位精通{platform}平台的短视频专家，请为{audience}生成脚本：
    
    主题：{topic}
    风格：{style}
    要求：
    1. 按表格输出6个分镜 [镜头|类型|画面|台词|时长|运镜]
    2. 开头3秒有悬念钩子
    3. 第10秒引导互动
    4. 结尾@好友

    示例：
    | 镜头 | 类型 | 画面 | 台词 | 时长 | 运镜 |
    |------|------|------|------|------|------|
    | 1 | 特写 | 手机闹钟响 | "凌晨5点的图书馆..." | 3s | 推镜头 |"""
    
    try:
        response = requests.post(
            MOONSHOT_API_URL,
            headers={"Authorization": f"Bearer {MOONSHOT_API_KEY}"},
            json={
                "model": "moonshot-v1-8k",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000
            },
            timeout=10  # 设置超时
        )
        data = response.json()
        if "choices" not in data:
            return f"API错误：{data.get('error', {}).get('message', '未知错误')}"
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"生成失败：{str(e)}"

# ===== 界面设计 =====
st.set_page_config(page_title="校园短视频助手", layout="wide")
st.title("🎬 AI脚本生成器")

with st.form("script_form"):
    topic = st.text_input("视频主题", placeholder="例：食堂美食测评")
    audience = st.selectbox("目标受众", ["新生", "考研党", "社团成员"])
    style = st.selectbox("风格", ["搞笑", "干货", "治愈"])
    platform = st.radio("平台", ["抖音", "快手", "B站"], horizontal=True)
    
    if st.form_submit_button("生成脚本"):
        with st.spinner('创作中...'):
            result = generate_script(topic, audience, style, platform)
            if "|" in result:
                st.success("成功！")
                lines = [line.split("|")[1:-1] for line in result.split("\n") if "|" in line]
                st.table(pd.DataFrame(lines, columns=["镜头", "类型", "画面", "台词", "时长", "运镜"]))
            else:
                st.error(result)