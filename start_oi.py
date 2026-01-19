import streamlit as st
import requests
import time
import base64
from datetime import datetime

# --- 1. 基础配置 ---
st.set_page_config(page_title="Sora-2 Pro", page_icon="🎬", layout="centered")

# 初始化历史记录
if "history" not in st.session_state:
    st.session_state.history = []

# --- 2. 获取 API Key (从 Secrets 读取) ---
try:
    # 这里会自动读取你在后台配置的 API_KEY
    api_key = st.secrets["API_KEY"]
except Exception:
    st.error("⚠️ 未检测到 API Key！")
    st.info("请去 Streamlit 后台 -> Settings -> Secrets 中添加：\nAPI_KEY = \"sk-xxxx...\"")
    st.stop()

# CSS 美化
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {margin-top: -50px;}
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Sora-2 视频生成器")

# --- 3. 侧边栏设置 (现在很清爽了) ---
with st.sidebar:
    st.header("⚙️ 系统设置")
    
    # 显示 Key 的状态 (只显示前4位，确认已加载)
    st.success(f"✅ API Key 已加载 ({api_key[:4]}...)")
    
    base_url = st.selectbox(
        "选择线路", 
        ("https://grsai.dakka.com.cn", "https://grsaiapi.com"),
        index=0
    )
    
    st.divider()
    if st.button("🗑️ 清空历史记录"):
        st.session_state.history = []
        st.rerun()

# --- 4. 核心功能区 ---
tab1, tab2 = st.tabs(["✨ 新建任务", "📜 历史记录"])

with tab1:
    # --- 输入区域 ---
    prompt = st.text_area("提示词 (Prompt)", height=120, placeholder="描述你想生成的视频内容...")
    
    # --- 图片上传 ---
    uploaded_file = st.file_uploader("上传参考图片 (可选)", type=['jpg', 'png', 'jpeg'])
    
    image_data = ""
    if uploaded_file is not None:
        st.image(uploaded_file, caption="已加载参考图", width=200)
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode()
        mime_type = uploaded_file.type
        image_data = f"data:{mime_type};base64,{base64_str}"

    # --- 参数设置 ---
    col1, col2 = st.columns(2)
    with col1:
        # 支持 1080p
        resolution = st.selectbox("清晰度", ("1080p", "720p", "small"), index=0)

    with col2:
        # 支持 15秒
        duration = st.selectbox("视频时长 (秒)", (5, 10, 15), index=2)
        
    aspect_ratio = st.selectbox("画幅比例", ("16:9", "9:16", "1:1", "4:3"), index=0)

    # --- 提交按钮 ---
    if st.button("🚀 立即生成", type="primary", use_container_width=True):
        if not prompt:
            st.toast("⚠️ 请输入提示词")
            st.stop()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 构造参数
        payload = {
            "model": "sora-2",
            "prompt": prompt,
            "aspectRatio": aspect_ratio,
            "duration": duration,
            "size": resolution, 
            "shutProgress": False
        }
        
        if image_data:
            payload["url"] = image_data

        status_container = st.container()
        
        try:
            with status_container:
                st.info("正在上传指令...")
                create_url = f"{base_url}/v1/video/sora-video"
                res = requests.post(create_url, headers=headers, json=payload)
                
                if res.status_code != 200:
                    st.error(f"提交失败: {res.text}")
                    st.stop()

                res_json = res.json()
                task_id = res_json.get("data", {}).get("id") or res_json.get("id")
                
                if not task_id:
                    st.error("未能获取任务ID")
                    st.stop()
                    
                st.success(f"任务提交成功! ID: {task_id}")
                
                # --- 轮询等待 ---
                prog_bar = st.progress(0)
                status_text = st.empty()
                
                while True:
                    time.sleep(3)
                    check_res = requests.post(f"{base_url}/v1/draw/result", headers=headers, json={"id": task_id})
                    
                    if check_res.status_code == 200:
                        data = check_res.json()
                        status = data.get("status") or data.get("data", {}).get("status")
                        progress = data.get("data", {}).get("progress", 0) or 0
                        
                        prog_bar.progress(int(progress))
                        status_text.text(f"生成中... {progress}% ({status})")
                        
                        if status == "succeeded":
                            results = data.get("data", {}).get("results", [])
                            video_url = results[0].get("url") if results else None
                            
                            if video_url:
                                st.balloons()
                                st.video(video_url)
                                
                                # 保存到历史记录
                                new_record = {
                                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "prompt": prompt,
                                    "video_url": video_url,
                                    "image_used": True if image_data else False
                                }
                                st.session_state.history.insert(0, new_record)
                            else:
                                st.error("生成显示成功，但未返回视频链接")
                            break
                        elif status == "failed":
                            reason = data.get("data", {}).get("failure_reason", "未知")
                            st.error(f"生成失败: {reason}")
                            break
        except Exception as e:
            st.error(f"发生错误: {e}")

# --- 5. 历史记录页面 ---
with tab2:
    if not st.session_state.history:
        st.info("暂无生成记录")
    else:
        for idx, item in enumerate(st.session_state.history):
            with st.expander(f"📅 {item['time']} - {item['prompt'][:20]}...", expanded=(idx == 0)):
                st.write(f"**提示词:** {item['prompt']}")
                if item['image_used']:
                    st.caption("🖼️ 使用了参考图")
                st.video(item['video_url'])
                st.markdown(f"[📥 点击下载视频]({item['video_url']})")
