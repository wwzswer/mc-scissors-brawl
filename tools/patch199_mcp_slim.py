import io

NL = chr(10)
p = 'D:/Documents/deepseek-harness/default-workspace/qq-bridge/src/mcp-mc-brawl.js'
s = io.open(p, encoding='utf-8').read()
n0 = len(s)

def sub(old, new, label):
    global s
    assert old in s, 'anchor missing: ' + label
    s = s.replace(old, new, 1)
    print('  ok ' + label)

# 1) 去掉 mc_room_board（mc_room 已能按房间码读局面），工具少一个
start = s.index("server.tool(" + NL + "  'mc_room_board',")
end = s.index("server.tool(" + NL + "  'mc_log',", start)
s = s[:start] + s[end:]
print('  ok 移除 mc_room_board')

# 2) answer：choice 只收字符串，新增 plan
sub("""  '回答 mc_room_wait 给出的问题：出拳传 move；行动传 choice（序号或选项 id）；结束行动传 choice="pass"。',
  {
    move: z.enum(['rock', 'scissors', 'paper']).optional().describe('猜拳：rock/scissors/paper'),
    choice: z.union([z.string(), z.number()]).optional().describe('行动序号（1、2…）或选项 id，或 "pass"'),
  },""",
    """  '回答 mc_room_wait 的问题。move=出拳；choice=行动序号/id/pass；plan=顺便把整回合行动排好（逗号分隔，最快）。',
  {
    move: z.enum(['rock', 'scissors', 'paper']).optional().describe('出拳：rock/scissors/paper'),
    choice: z.string().optional().describe('行动序号（1、2…）或选项 id，或 "pass"'),
    plan: z.string().optional().describe('整回合计划，逗号分隔，如 "1,3,pass"；和 move 一起传只要一问一答'),
  },""",
    'answer schema')

sub("  async ({ move, choice }) => {", "  async ({ move, choice, plan }) => {", 'answer 解构')

# 3) plan 解析 + 带进 action
sub("""    const action = { kind: 'ans', promptId: ask.promptId };
    if (ask.ask === 'rps') {""",
    """    const planList = (typeof plan === 'string' && plan.trim())
      ? plan.split(/[,\\uFF0C;\\uFF1B\\n、]/).map(x => x.trim()).filter(Boolean)
      : [];
    const action = { kind: 'ans', promptId: ask.promptId };
    if (planList.length) action.plan = planList;
    if (ask.ask === 'rps') {""",
    'ans 带 plan')

# 4) 文案：「接着…或者 mc_room_board」改成 mc_room；rps 提示可带 plan（按行改，避免转义）
lines = s.split(NL)
for i, ln in enumerate(lines):
    if '接着 mc_room_wait 等下一条，或者 mc_room_board 看局面' in ln:
        lines[i] = ln.replace('或者 mc_room_board 看局面', '或者用 mc_room 按房间码看局面')
    if "mc_room_answer move=rock/scissors/paper 回答" in ln:
        lines[i] = ("  if (ask.ask === 'rps') return head + '（用 mc_room_answer move=rock/scissors/paper 回答）' +"
                    + NL + "    '  💡 顺手把这一回合的行动也排好：plan=\"1,3,pass\" —— 一回合只问一次，快很多。';")
s = NL.join(lines)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('mcp: %d -> %d bytes' % (n0, len(s)))
