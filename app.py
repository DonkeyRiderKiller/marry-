import streamlit as st
import random

# 设置网页配置
st.set_page_config(page_title="🎄 圣诞互送礼物 🎁", page_icon="🎅")

# 参与者名单
PARTICIPANTS = ['gs', 'GS', 'hht', 'jm', 'mtt', 'qx', 'bitee']

def generate_matches():
    """生成配对逻辑，逻辑与之前相同"""
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
        for i, giver in enumerate(remaining_group):
            if giver == receivers[i]:
                valid = False
                break
        if valid:
            for i, giver in enumerate(remaining_group):
                matches[giver] = receivers[i]
            break
    return matches

# --- 页面逻辑 ---

st.title("🎄 圣诞节互送礼物抽奖 🎁")
st.write("请在下方选择你的名字，查看你要送礼物的对象。")

# 初始化 Session State (保证刷新页面结果不会变，且所有人共享一个结果逻辑需要数据库，
# 但简易版我们可以让结果在加载时固定，或者仅在内存中生成一次)
# 注意：Streamlit 默认是无状态的。为了简单起见，这里我们做成
# "每个人点进来看到的是独立的界面，但我们需要保证结果一致性"。
# 真正的多端同步需要数据库。
# **为了简化，我们采用一种“伪随机但确定”的方法，或者更简单的：**
# **由你作为管理员，直接生成一份名单，大家输入暗号查看，或者使用简单的随机种子**

# 方案：为了让大家不需要数据库也能玩，我们使用“当天日期+固定逻辑”或者
# 让每个人自己抽，但既然你要求 qx和bitee 锁定，其他人随机。
# 如果每个人看到的随机结果不一样，那就乱套了（A抽到B，B也抽到A，或者C也抽到B）。

# ---> 修正方案：为了确保这是一个多人协作的网页，最简单的方法其实是
# 每个人点进来都触发一次随机是不行的。
# 这里我提供一个“输入密码查看结果”的模式，或者利用 Streamlit 的缓存机制。

# 既然是简单脚本，最稳妥的方式是：
# 你（管理员）运行脚本生成好结果，写死在代码里，然后部署上去。
# 这样所有人看到的结果就是固定的，且唯一的。

# === 请先在本地运行一次下面的小脚本生成结果，然后填入下方 ===
# 例如你本地运行算出：{'gs': 'mtt', 'GS': 'hht', ...}
# 把这个字典填入下面：

# 假设这是你提前生成好的（除了qx和bitee，其他我也随机填了几个，请你务必修改！）
# 你可以用我上一条回复的代码在本地跑一次，把 print(self.matches) 的结果复制过来。
FIXED_MATCHES = {
    'qx': 'bitee',
    'bitee': 'qx',
    # 以下请修改为你本地生成好的结果，确保不重复不自抽
    'gs': 'mtt', 
    'GS': 'jm', 
    'hht': 'GS', 
    'jm': 'gs', 
    'mtt': 'hht' 
}
# =======================================================

name = st.selectbox("我是...", ["请选择"] + PARTICIPANTS)

if name != "请选择":
    if st.button("🎁 点击抽取礼物对象"):
        receiver = FIXED_MATCHES.get(name)
        st.success(f"亲爱的 {name}，你要送礼物的对象是：")
        st.header(f"✨ {receiver} ✨")
        st.info("🤫 请截屏保存并保密！")
    else:
        st.write("点击按钮查看结果")

st.markdown("---")
st.caption("Designed for Christmas Gift Exchange")