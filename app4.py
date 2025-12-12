import streamlit as st
import random
import pandas as pd
from datetime import datetime
import gspread # 用于连接 Google Sheets

# --- 1. 配置和六位数固定种子 ---

st.set_page_config(page_title="🎄 圣诞互送礼物 🎁", page_icon="🎅")

# 参与者名单
PARTICIPANTS = ['gs', 'GS', 'hht', 'jm', 'mtt', 'qx', 'bitee']

# 固定的六位数随机种子，保证所有用户看到的结果是一样的
FINAL_SEED = 729514  

# Google Sheets 配置
# 请确保你的 Google Sheet 名称与此一致
SHEET_TITLE = "Gift_Exchange_Log"
WORKSHEET_NAME = "Sheet1" 

# --- 2. 核心逻辑函数：生成固定结果 ---

@st.cache_resource
def generate_matches(seed_value):
    """
    生成依赖于种子的配对逻辑，确保结果唯一。
    """
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
            
    random.seed(None) 
    return matches

# 全局共享的抽奖结果 (所有人都相同)
FIXED_MATCHES = generate_matches(FINAL_SEED)


# --- 3. Google Sheets 操作函数 ---

# 定义自定义异常
class ConnectionError(Exception):
    pass

# 辅助函数：连接 Google Sheets
@st.cache_resource(ttl=600) 
def get_sheet_client():
    """使用 Streamlit Secrets 中的服务账号凭证连接 Google Sheets。"""
    
    try:
        # 1. 从 secrets 中获取凭证字典
        creds = st.secrets["gsheets"]
        
        # 2. ❗ 核心：手动重构 private_key ❗
        private_key_clean = creds.pop("private_key_clean") # 移除干净的key
        
        # 重新构建完整的 private_key 字符串，添加换行符
        creds['private_key'] = '-----BEGIN PRIVATE KEY-----\n' + \
                               private_key_clean.replace(' ', '\n') + \
                               '\n-----END PRIVATE KEY-----\n'
        
        # 3. 使用 gspread 库进行授权和连接
        client = gspread.service_account_from_dict(creds)
        
        # 4. 打开你的表格和工作表
        sheet = client.open(SHEET_TITLE).worksheet(WORKSHEET_NAME) 
        
        return sheet
        
    except Exception as e:
        # 记录错误信息到 Streamlit 界面
        st.error(f"连接 Google Sheets 认证失败。请检查 Streamlit Secrets [gsheets] 配置和表格共享权限。原始错误: {e}")
        # 抛出自定义连接错误，以便后续函数可以捕获并优雅处理
        raise ConnectionError(f"GSheets 连接错误: {e}")
def get_drawn_log():
    """从 GSheets 读取所有已抽取的记录，获取已抽和已收名单。"""
    try:
        sheet = get_sheet_client()
        # 获取所有记录 (以字典列表的形式)
        all_records = sheet.get_all_records() 
        
        # 转换为 Pandas DataFrame
        data = pd.DataFrame(all_records)
        
        # 检查 DataFrame 是否为空，并且 GIVER 列有数据 (防止只有表头)
        if data.empty or data['GIVER'].isnull().all():
            return set(), set()
        
        # 确保列名正确
        drawn_givers = set(data['GIVER'].dropna())
        drawn_receivers = set(data['RECEIVER'].dropna())
        return drawn_givers, drawn_receivers
        
    except ConnectionError:
        # 捕获 get_sheet_client 抛出的连接错误
        return set(), set()
    except Exception as e:
        st.error(f"读取日志数据失败：{e}")
        return set(), set()


def log_result(giver, receiver):
    """将抽奖结果写入 GSheets。"""
    try:
        sheet = get_sheet_client()
        # 写入新的一行数据 (列表中的元素顺序要与 Sheets 表头 GIVER, RECEIVER, DRAW_TIME 匹配)
        sheet.append_row([giver, receiver, datetime.now().isoformat()])
        st.toast("✅ 结果已成功写入共享日志！", icon='🎉')
        return True
    except ConnectionError:
        return False
    except Exception as e:
        st.error(f"结果写入共享日志失败：{e}")
        return False


# --- 4. UI 和流程控制 ---

st.title("🎄 圣诞节互送礼物抽奖 🎁")

# 1. 读取当前已抽取状态
drawn_givers, drawn_receivers = get_drawn_log()
# 可供选择的名字 = 所有人 - 已抽过的人
available_participants = [p for p in PARTICIPANTS if p not in drawn_givers]

# 2. 状态锁定逻辑（每个用户独立）
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None
if 'final_result' not in st.session_state:
    st.session_state.final_result = None

# --- UI 展示 ---

# 如果用户还没有选择身份
if st.session_state.selected_user is None:
    
    st.markdown("---")
    st.subheader("请选择你的名字 (一旦抽取，该名字将对所有人隐藏)")
    
    selected_name = st.selectbox("我是...", ["请选择"] + available_participants)
    
    if selected_name != "请选择":
        if st.button("确定我的身份并开始抽奖"):
            # 身份锁定在会话中
            st.session_state.selected_user = selected_name
            st.rerun() 
            
# 身份已锁定或已抽取
else:
    current_user = st.session_state.selected_user
    st.info(f"当前身份已锁定为：**{current_user}**")
    
    # 检查是否已在全局日志中
    if current_user in drawn_givers:
        # 如果当前用户已在日志中，但会话中没有结果（可能刷新导致）
        if st.session_state.final_result is None:
            # 尝试从 FIXED_MATCHES 找回结果（因为是固定算法）
            st.session_state.final_result = FIXED_MATCHES.get(current_user)
            
        st.success(f"亲爱的 **{current_user}**，你的结果已在日志中。你要送礼物的对象是：")
        st.header(f"✨ {st.session_state.final_result} ✨")
        st.warning("结果已记录到共享系统，请截屏保存！")
        
    # 如果身份已锁定，但尚未抽取
    elif st.session_state.final_result is None:
        
        if st.button(f"🎁 {current_user}，点击抽取礼物对象"):
            
            receiver = FIXED_MATCHES.get(current_user)
            
            # 核心互斥检查：确保接收者没有被其他人抽走
            if current_user not in available_participants:
                 # 这条检查主要是为了防止极端情况下的时序问题
                 st.error("此名字已被其他人抽取，请刷新页面！")
                 st.session_state.selected_user = None # 解锁身份
                 st.rerun()
                 
            else:
                # 记录结果到共享存储
                success = log_result(current_user, receiver)
                
                if success:
                    st.session_state.final_result = receiver
                    st.rerun() # 刷新页面显示结果
                    
    # 如果已锁定身份且已在会话中抽取
    elif st.session_state.final_result is not None:
        final_receiver = st.session_state.final_result
        st.success(f"亲爱的 **{current_user}**，你要送礼物的对象是：")
        st.header(f"✨ {final_receiver} ✨")
        st.warning("结果已记录到共享系统，请截屏保存！")
        
# 5. 底部显示状态
st.markdown("---")
st.caption(f"已抽取人数：{len(drawn_givers)}/{len(PARTICIPANTS)}")
st.caption(f"剩余可抽：{', '.join(available_participants) if available_participants else '无'}")
st.caption(f"程序版本号: {FINAL_SEED}")

