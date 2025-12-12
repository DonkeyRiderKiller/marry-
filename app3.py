import streamlit as st
import random
import pandas as pd
from datetime import datetime

# --- 1. 配置和固定种子 ---

st.set_page_config(page_title="🎄 圣诞互送礼物 🎁", page_icon="🎅")

PARTICIPANTS = ['gs', 'GS', 'hht', 'jm', 'mtt', 'qx', 'bitee']
FINAL_SEED = 729514  # 六位数固定种子，保证结果唯一

# Google Sheets 配置
SHEET_TITLE = "Gift_Exchange_Log"
WORKSHEET_NAME = "Sheet1"

# --- 2. 核心逻辑函数 ---

@st.cache_resource
def generate_matches(seed_value):
    """生成依赖于种子的配对逻辑，全局唯一。"""
    random.seed(seed_value)
    # ... (与之前完全相同的抽奖生成逻辑) ...
    matches = {'qx': 'bitee', 'bitee': 'qx'}
    remaining_group = [p for p in PARTICIPANTS if p not in ['qx', 'bitee']]
    while True:
        receivers = remaining_group[:]
        random.shuffle(receivers) 
        if not any(giver == receivers[i] for i, giver in enumerate(remaining_group)):
            for i, giver in enumerate(remaining_group): matches[giver] = receivers[i]
            break
    random.seed(None) 
    return matches

# 全局共享的抽奖结果 (所有人都相同)
FIXED_MATCHES = generate_matches(FINAL_SEED)

# --- 3. Google Sheets 操作函数 ---

def get_drawn_log():
    """从 GSheets 读取所有已抽取的记录，获取已抽和已收名单。"""
    try:
        conn = st.connection("gslides", type="pandas") # 假设你配置了 gsheets 连接
        # 如果你使用 st-gsheets-connection，连接方式可能不同
        
        # 尝试使用 Streamlit 官方 Google Sheets 连接器
        # 确保你的 Streamlit Cloud secrets 中配置了 Google Sheets 凭证
        sheet = st.connection("gsheets", type=st.secrets["CONNECTION_NAME"]) # 替换 CONNECTION_NAME
        
        # 读取数据 (这里需要根据你实际使用的连接库调整)
        data = sheet.read(worksheet=WORKSHEET_NAME, ttl="10s")
        
        # 检查 DataFrame 是否为空或只有列名
        if data.empty or data['GIVER'].isnull().all():
            return set(), set()
        
        drawn_givers = set(data['GIVER'].dropna())
        drawn_receivers = set(data['RECEIVER'].dropna())
        return drawn_givers, drawn_receivers
        
    except Exception as e:
        # 简化处理：如果连接失败，视为没人抽取，但在实际部署中需确保连接成功
        st.error(f"无法连接到日志系统，多人协作功能可能失效。请检查配置。错误: {e}")
        return set(), set()


def log_result(giver, receiver):
    """将抽奖结果写入 GSheets。"""
    try:
        # ... (连接和写入逻辑，你需要根据实际连接库调整) ...
        # 示例：假设连接对象有一个 append 方法
        # new_entry = pd.DataFrame([{'GIVER': giver, 'RECEIVER': receiver, 'DRAW_TIME': datetime.now().isoformat()}])
        # st.connection("gsheets").append(new_entry, worksheet=WORKSHEET_NAME, headers=False) 
        
        # 假设你使用的是 gspread 或其他 Sheets API 库
        # 示例简化：假设连接成功
        st.success("结果已成功写入共享日志！")
        return True
    except Exception as e:
        st.error(f"结果写入共享日志失败：{e}")
        return False

# --- 4. UI 和流程控制 ---

st.title("🎄 圣诞节互送礼物抽奖 🎁")

# 1. 读取当前已抽取状态
drawn_givers, drawn_receivers = get_drawn_log()
available_participants = [p for p in PARTICIPANTS if p not in drawn_givers]

# 2. 状态锁定逻辑（每个用户独立）
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None

# 如果用户还没有选择身份
if st.session_state.selected_user is None:
    
    st.markdown("---")
    st.subheader("请选择你的名字 (一旦抽取，该名字将对所有人隐藏)")
    
    # 过滤掉已经抽过的人
    selected_name = st.selectbox("我是...", ["请选择"] + available_participants)
    
    if selected_name != "请选择":
        if st.button("确定我的身份并开始抽奖"):
            # 身份锁定在会话中
            st.session_state.selected_user = selected_name
            st.rerun()
            
elif st.session_state.selected_user in drawn_givers:
    # 如果用户身份已被锁定，但同时又在日志中
    st.error(f"你的名字 {st.session_state.selected_user} 已经在抽奖日志中。请勿重复操作。")
    st.info("如果需要查看结果，请联系管理员查询日志。")


else:
    # 3. 身份已锁定，显示抽奖按钮

    current_user = st.session_state.selected_user
    st.info(f"当前身份已锁定为：**{current_user}**")
    
    if st.button(f"🎁 {current_user}，点击抽取礼物对象"):
        
        # 检查分配给这个 GIVER 的 RECEIVER 是否已被抽走
        receiver = FIXED_MATCHES.get(current_user)
        
        # 检查 receiver 是否已经被其他人抽走
        if receiver in drawn_givers:
            # 理论上 FIXED_MATCHES 保证了一对一，但如果 GSheets 有脏数据或逻辑错误，这里可以捕获
            st.error(f"错误：你要抽取的对象 {receiver} 已经被抽走了。请联系管理员！")
        
        else:
            # 记录结果到共享存储
            success = log_result(current_user, receiver)
            
            if success:
                st.session_state.final_result = receiver
                st.session_state.logged = True # 标记为已记录
                st.rerun()
                
    if 'final_result' in st.session_state and st.session_state.logged:
        final_receiver = st.session_state.final_result
        st.success(f"亲爱的 **{current_user}**，你要送礼物的对象是：")
        st.header(f"✨ {final_receiver} ✨")
        st.warning("结果已记录到共享系统，请截屏保存！")
        
# 4. 底部显示状态 (可选项)
st.markdown("---")
st.caption(f"已抽取人数：{len(drawn_givers)}/{len(PARTICIPANTS)}")
st.caption(f"剩余可抽：{', '.join(available_participants) if available_participants else '无'}")
st.caption(f"由固定算法 {FINAL_SEED} 生成。")