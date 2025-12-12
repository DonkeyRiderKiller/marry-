import streamlit as st
import random
import pandas as pd
from datetime import datetime
import gspread # 引入 gspread 库

# --- 1. 配置和固定种子 ---
# ... (保持不变) ...

# Google Sheets 配置
SHEET_TITLE = "Gift_Exchange_Log"
WORKSHEET_NAME = "Sheet1"

# ... (generate_matches 函数保持不变) ...
# ... (FIXED_MATCHES 保持不变) ...

# --- 3. Google Sheets 操作函数 ---

# 辅助函数：连接 Google Sheets
@st.cache_resource(ttl=600) # 缓存客户端连接，避免重复认证
def get_sheet_client():
    """使用 Streamlit Secrets 中的服务账号凭证连接 Google Sheets。"""
    
    try:
        # 1. 从 secrets 中获取凭证字典
        # 确保你的 Streamlit Secrets 配置中包含 [gsheets] section
        creds = st.secrets["gsheets"]
        
        # 2. 使用 gspread 库进行授权和连接
        client = gspread.service_account_from_dict(creds)
        
        # 3. 打开你的表格和工作表
        sheet = client.open(SHEET_TITLE).worksheet(WORKSHEET_NAME) 
        
        return sheet
        
    except Exception as e:
        st.error(f"连接 Google Sheets 认证失败。请检查 Streamlit Secrets [gsheets] 配置和表格共享权限。错误: {e}")
        # 返回 None 或抛出错误，以便调用函数能够捕获
        raise ConnectionError(f"GSheets 连接错误: {e}")

def get_drawn_log():
    """从 GSheets 读取所有已抽取的记录，获取已抽和已收名单。"""
    try:
        sheet = get_sheet_client()
        # 获取所有记录 (以字典列表的形式)
        all_records = sheet.get_all_records() 
        
        # 转换为 Pandas DataFrame
        data = pd.DataFrame(all_records)
        
        # 检查 DataFrame 是否为空
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
        # 写入新的一行数据 (注意：列表中的元素顺序要与 Sheets 表头 GIVER, RECEIVER, DRAW_TIME 匹配)
        sheet.append_row([giver, receiver, datetime.now().isoformat()])
        st.toast("✅ 结果已成功写入共享日志！", icon='🎉')
        return True
    except ConnectionError:
        # 捕获 get_sheet_client 抛出的连接错误
        return False
    except Exception as e:
        st.error(f"结果写入共享日志失败：{e}")
        return False

# --- 4. UI 和流程控制 ---
# ... (保持不变) ...