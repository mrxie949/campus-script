# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
import os
import time

# ===== API配置 =====
MOONSHOT_API_KEY = "sk-sqrfIzSxn92laOhBxS9HSMZ6Y4itPpZ70Z49v1pWnIl7RgQb"  # 您提供的API密钥
MOONSHOT_API_URL = "https://api.moonshot.cn/v1/chat/completions"

# ===== AI生成核心（增强错误处理）=====
def generate_script(topic, audience, style, platform):
    prompt = f"""你是一位精通{platform}平台的短视频专家，请为{audience}生成脚本：
    
【主题】{topic}
【风格】{style}
【要求】
1. 按表格输出6个分镜 [镜头序号|类型|画面|台词|时长|运镜]
2. 开头3秒使用"疑问句+特写镜头"制造悬念
3. 第10秒添加互动话术
4. 结尾引导关注和@好友

【示例格式】
| 镜头 | 类型 | 画面 | 台词 | 时长 | 运镜 |
|------|------|------|------|------|------|
| 1 | 特写 | 手机显示凌晨3点 | "考研人的夜有多长？" | 2s | 推镜头 |"""
    
    try:
        start_time = time.time()
        response = requests.post(
            MOONSHOT_API_URL,
            headers={"Authorization": f"Bearer {MOONSHOT_API_KEY}"},
            json={
                "model": "moonshot-v1-8k",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1500  # 减少token数量以防超额
            },
            timeout=10  # 设置超时限制
        )
        
        # 检查响应状态
        if response.status_code != 200:
            return f"⚠️ API响应异常: {response.status_code}", []
        
        data = response.json()
        
        # 检查响应结构
        if "choices" not in data:
            return f"⚠️ API返回格式异常: {data.get('error', {}).get('message', '未知错误')}", []
        
        processing_time = time.time() - start_time
        st.toast(f"生成完成! 耗时: {processing_time:.1f}秒")
        
        return data["choices"][0]["message"]["content"], []
    except requests.exceptions.Timeout:
        return "⚠️ 请求超时，请稍后重试", []
    except Exception as e:
        return f"⚠️ 生成失败：{str(e)}", []

# ===== 用户界面（简化版）=====
st.set_page_config(
    page_title="短视频脚本生成器",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 顶部区域
st.title("🎥 AI短视频脚本生成器")
st.caption("输入主题，一键生成专业分镜脚本")

# 主表单区
with st.form("script_form", border=True):
    topic = st.text_input("视频主题", placeholder="例：军训生存指南/宿舍美食DIY", 
                         help="越具体越好，如'图书馆抢座攻略'而非'学习方法'")
    audience = st.selectbox("目标受众", ["新生", "学生社团", "考研党", "毕业生"])
    style = st.selectbox("视频风格", ["幽默搞笑", "知识干货", "情感治愈", "热血励志"])
    platform = st.radio("发布平台", ["抖音", "快手", "B站"], horizontal=True)
    
    submitted = st.form_submit_button("✨ 生成脚本", type="primary", use_container_width=True)
    
    if submitted:
        if not topic.strip():
            st.warning("请填写视频主题")
        else:
            with st.spinner('AI创作中...'):
                result, _ = generate_script(topic, audience, style, platform)
                
                # 结果展示
                if "|" in result:
                    st.success("生成成功!")
                    
                    # 表格处理
                    st.markdown("### 分镜脚本")
                    st.write(result)  # 直接显示原始表格格式
                else:
                    st.error(result)

# 使用指南
with st.expander("📚 使用指南", expanded=True):
    st.markdown("""
    **最佳实践：**
    1. **主题具体化**：`场景+解决方案`（例："宿舍5分钟健身法"）
    2. **风格匹配平台**：
       - 抖音：幽默搞笑 > 知识干货
       - B站：知识干货 > 情感治愈
    """)

# 底部信息
st.divider()
st.caption("© 2023 短视频脚本生成器 | 技术支持: contact@example.com")