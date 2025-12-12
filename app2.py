import streamlit as st
import random
import hashlib

# --- 1. 配置和固定种子 ---

st.set_page_config(page_title="🎄 圣诞互送礼物 🎁", page_icon="🎅")

# 参与者名单
PARTICIPANTS = ['gs', 'GS', 'hht', 'jm', 'mtt', 'qx', 'bitee']

# 固定的“随机”种子。使用一个看起来随机的固定数字，确保结果在任何地方都是一样的。
# 这个数字是预先随机生成的，一旦部署就固定，管理员不需要知道它的含义。
FINAL_SEED = 18837295147  # <--- 这是固定的，用于保证结果唯一性

# --- 2. 核心逻辑函数 ---

@st.cache_resource
def generate_matches(seed_value):
    """
    生成依赖于种子的配对逻辑，确保结果唯一。
    使用 st.cache_resource 确保这个函数只在程序启动时运行一次，避免重复计算。
    """
    
    # 核心：根据种子设置随机数生成器
    random.seed(seed_value)
    
    matches = {}
    # 1. 强制 qx 和 bitee 互抽
    matches['qx'] = 'bitee'
    matches['bitee'] = 'qx'
    
    # 2. 其余人逻辑
    remaining_group = [p for p in PARTICIPANTS if p not in ['qx', 'bitee']]
    
    while True:
        receivers = remaining_group[:]
        random.shuffle(receivers) 
        
        valid = True
        # 检查是否自抽
        if any(giver == receivers[i] for i, giver in enumerate(remaining_group)):
            valid = False
        
        if valid:
            for i, giver in enumerate(remaining_group):
                matches[giver] = receivers[i]
            break
    
    # 3. 结果生成后，关闭种子设置
    random.seed(None) 
    return matches

# -----------------------------------------------------------

# 全局共享的抽奖结果 (所有人看到的结果都相同)
FIXED_MATCHES = generate_matches(FINAL_SEED)

# --- 3. UI 逻辑 ---

st.title("🎄 圣诞节互送礼物抽奖 🎁")
st.write("请在下方选择你的名字，并抽取你要送礼物的对象。")

# Session State 用于锁定用户身份和结果
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None
if 'drawn_result' not in st.session_state:
    st.session_state.drawn_result = None

# --- 用户选择和锁定逻辑 ---

# 如果用户还没有选择身份
if st.session_state.selected_user is None:
    
    # 下拉框供用户选择
    selected_name = st.selectbox("请选择你的名字 (一旦选择，无法更改):", 
                                 ["请选择"] + PARTICIPANTS)

    if selected_name != "请选择":
        if st.button("确定我的身份"):
            # 锁定身份
            st.session_state.selected_user = selected_name
            st.rerun()
            
else:
    # --- 身份已锁定，显示抽奖界面 ---
    
    current_user = st.session_state.selected_user
    st.info(f"当前身份已锁定为：**{current_user}**")
    
    # 如果还没有抽取结果
    if st.session_state.drawn_result is None:
        
        if st.button(f"🎁 {current_user}，点击抽取礼物对象"):
            
            receiver = FIXED_MATCHES.get(current_user)
            
            # 锁定抽奖结果
            st.session_state.drawn_result = receiver
            st.rerun() # 刷新页面显示结果
            
    else:
        # --- 结果已抽取，显示最终结果 ---
        
        final_receiver = st.session_state.drawn_result
        st.success(f"亲爱的 **{current_user}**，你要送礼物的对象是：")
        st.header(f"✨ {final_receiver} ✨")
        st.warning("请截屏保存结果！出于保密考虑，页面刷新后结果依然在此，但不可再抽。")

st.markdown("---")
st.caption(f"由随机算法 {FINAL_SEED} 生成。祝大家圣诞快乐！")