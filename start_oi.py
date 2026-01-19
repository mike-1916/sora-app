import streamlit as st
import requests
import time

# --- 页面配置 ---
st.set_page_config(page_title="Sora-2 移动版", page_icon="🎬", layout="centered")

# 隐藏多余菜单
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Sora-2 视频生成")

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("API Key", type="password")
    base_url = st.selectbox(
        "选择线路", 
        ("https://grsai.dakka.com.cn", "https://grsaiapi.com"),
        index=0
    )

# --- 主界面 ---
prompt = st.text_area("在此输入提示词...", height=150)
col1, col2 = st.columns(2)
with col1:
    aspect_ratio = st.selectbox("画幅", ("16:9", "9:16", "1:1"), index=0)
with col2:
    duration = st.selectbox("时长", (5, 10), index=1)

if st.button("🚀 开始生成", use_container_width=True):
    if not api_key:
        st.error("请先在左侧输入 API Key")
        st.stop()
    
    # 1. 提交任务
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "sora-2",
        "prompt": prompt,
        "aspectRatio": aspect_ratio,
        "duration": duration,
        "size": "small",
        "shutProgress": False
    }
    
    try:
        st.info("正在提交...")
        res = requests.post(f"{base_url}/v1/video/sora-video", headers=headers, json=payload)
        
        if res.status_code != 200:
            st.error(f"提交失败: {res.text}")
            st.stop()
            
        task_id = res.json().get("data", {}).get("id") or res.json().get("id")
        if not task_id:
            st.error(f"没有收到任务ID: {res.text}")
            st.stop()
            
        st.success(f"任务已提交! ID: {task_id}")
        
        # 2. 轮询结果
        bar = st.progress(0)
        status_text = st.empty()
        
        while True:
            time.sleep(3)
            check = requests.post(f"{base_url}/v1/draw/result", headers=headers, json={"id": task_id})
            if check.status_code == 200:
                data = check.json()
                status = data.get("status") or data.get("data", {}).get("status")
                
                # 尝试获取进度
                prog = data.get("data", {}).get("progress", 0)
                bar.progress(int(prog) if prog else 0)
                status_text.text(f"状态: {status}")
                
                if status == "succeeded":
                    # 尝试从不同层级获取 URL
                    results = data.get("data", {}).get("results", [])
                    url = results[0].get("url") if results else None
                    if url:
                        st.balloons()
                        st.video(url)
                    else:
                        st.error("未找到视频地址")
                    break
                elif status == "failed":
                    st.error("生成失败")
                    break
    except Exception as e:
        st.error(f"发生错误: {e}")
