import numpy as np
import random
import copy
import time

n = 8
actiondict = {}
characters = "abcdefghijk"
for i in range(n):
    actiondict[characters[i]] = i

def init_state():
    state = np.zeros((n,n))
    state[n//2, n//2] = 1
    state[n//2, n//2-1] = -1
    state[n//2-1, n//2] = -1
    state[n//2-1, n//2-1] = 1
    return state

def legalaction(state):
    legal_action_list = []
    for i in range(n):
        for j in range(n):
            if state[i,j]!=0:
                continue
            flag_legal = False
            for di,dj in [(-1,-1),(-1,0),(-1,1), (0,-1),(0,1), (1,-1),(1,0),(1,1)]:
                if i+di<0 or i+di>=n or j+dj<0 or j+dj>=n:
                    continue
                x = i+di
                y = j+dj
                if state[x, y] == -1:
                    while x>=0 and x<n and y>=0 and y<n:
                        if state[x,y] == 1:
                            flag_legal = True
                            break
                        elif state[x,y] == 0:
                            break
                        elif state[x,y] == -1:
                            x += di
                            y += dj
                if flag_legal:
                    break
            if flag_legal:
                legal_action_list.append((i,j))
    return legal_action_list
                    
def print_state(state, action_npc=(n,n)):
    legal_action_list = legalaction(state)
    print()
    print("   |", end="")
    for j in range(n):
        print("  "+str(j), end="")
    print()
    print("---+"+ "---"*n)
    for i in range(n):
        print(" "+characters[i]+" |", end="")
        for j in range(n):
            if i==action_npc[0] and j==action_npc[1]:
                print(" #X", end="")
            elif (i,j) in legal_action_list:
                print("  _", end="")
            elif state[i,j] == 1:
                print("  O", end="")
            elif state[i,j] == 0:
                if i==1 or i==n-2 or j==1 or j==n-2:
                    print("  .", end="")
                else:
                    print("   ", end="")
            elif state[i,j] == -1:
                print("  X", end="")
        print()

def update(state, action):
    if action == "pass":
        return state
    state[action]=1
    i,j = action
    for di,dj in [(-1,-1),(-1,0),(-1,1), (0,-1),(0,1), (1,-1),(1,0),(1,1)]:
        x = i+di
        y = j+dj
        turn_candidates = []
        turn_flag = False
        while x>=0 and x<n and y>=0 and y<n:
            if state[x,y] == 1:
                turn_flag = True
                break
            elif state[x,y] == 0:
                break
            elif state[x,y] == -1:
                turn_candidates.append((x,y))
                x += di
                y += dj
        if turn_flag:
            for ii,jj in turn_candidates:
                state[ii,jj] = 1
    return state
    
def judge_state(state, pass_player1, pass_player2, player):
    if pass_player1 >= 2:
        return -1, 0
    if pass_player2 >= 2:
        return 1, 0
    count_zero = np.sum(state == 0)
    if count_zero > 0:
        return 0, player
    count_player1 = np.sum(state == 1)
    count_player2 = np.sum(state == -1)
    if count_player1 >  count_player2: return 1,  0
    if count_player1 == count_player2: return 0,  0
    if count_player1 <  count_player2: return -1, 0

def npc_random(state, pass_p1, pass_p2):
    legal_action_list = legalaction(state)
    if random.random()<0.01 or len(legal_action_list)==0:
        return "pass"
    tmp = random.randrange(len(legal_action_list))
    action_npc = legal_action_list[tmp]
    return action_npc
    
def npc_shallow_playout(state, pass_p1, pass_p2):
    n_playout = 100
    action_list = legalaction(state)
    action_list.append("pass")
    nn = len(action_list)
    results = [0 for _ in range(nn)]
    for i in range(nn):
        for _ in range(n_playout):
            newstate = update(copy.deepcopy(state), action_list[i])
            if action_list[i]=="pass":
                results[i] += -playout(-newstate, pass_p2, pass_p1+1)
            else:
                results[i] += -playout(-newstate, pass_p2, pass_p1)
    #print("shallow_playout", results)
    return action_list[np.argmax(results)]

class Node(object):
    def __init__(self, state, pass_p1, pass_p2, topnode, layer):
        self.state = state
        self.pass_p1 = pass_p1
        self.pass_p2 = pass_p2
        self.topnode = topnode
        self.layer = layer
        self.trial = 0
        self.value = 0

def npc_expand(state, pass_p1, pass_p2):
    n_layer = 2
    n_playout = 5
    action_list = legalaction(state)
    action_list.append("pass")
    nn = len(action_list)
    results = [0 for _ in range(nn)]
    leaf_list = []
    for i in range(nn):
        newstate = -update(copy.deepcopy(state), action_list[i])
        p1 = pass_p2
        p2 = pass_p1+1 if action_list[i] == "pass" else pass_p1
        node = Node(newstate, p1, p2, i, 1)
        leaf_list.append(node)
    done = False
    while not done:
        done = True
        np.random.shuffle(leaf_list)
        for i in range(len(leaf_list)):
            node = leaf_list[i]
            if node.layer >= n_layer and node.trial >= n_playout:
                continue
            res = playout(copy.deepcopy(node.state), node.pass_p1, node.pass_p2)
            sign = 1 if node.layer%2==0 else -1
            results[node.topnode] += sign*res
            node.trial += 1
            node.value += res
            done = False
            if node.layer < n_layer and node.trial >= n_playout:
                tmp_action_list = legalaction(node.state)
                tmp_action_list.append("pass")
                nn = len(tmp_action_list)
                for j in range(nn):
                    newstate = -update(copy.deepcopy(node.state), tmp_action_list[j])
                    p1 = node.pass_p2
                    p2 = node.pass_p1+1 if tmp_action_list[j] == "pass" else node.pass_p1
                    node = Node(newstate, p1, p2, node.topnode, node.layer+1)
                    leaf_list.append(node)
                leaf_list.pop(i)
            break
    return action_list[np.argmax(results)]
    
def npc_minmax(state, pass_p1, pass_p2):
    n_layer = 2
    n_playout = 10
    action_list = legalaction(state)
    action_list.append("pass")
    nn = len(action_list)
    results = [0 for _ in range(nn)]
    for i in range(nn):
        newstate = -update(copy.deepcopy(state), action_list[i])
        p1 = pass_p2
        p2 = pass_p1+1 if action_list[i] == "pass" else pass_p1
        node = Node(newstate, p1, p2, i, 1)
        for _ in range(n_layer):
            tmp_action_list = legalaction(node.state)
            tmp_action_list.append("pass")
            nnn = len(tmp_action_list)
            tmp_results = [0 for _ in range(nnn)]
            tmp_nodes = []
            for j in range(nnn):
                newstate = -update(copy.deepcopy(node.state), tmp_action_list[j])
                p1 = node.pass_p2
                p2 = node.pass_p1+1 if tmp_action_list[j]=="pass" else node.pass_p1
                layer = node.layer+1
                sign = 1 if layer%2==0 else -1
                tmp_node = Node(newstate, p1, p2, i, layer)
                for _ in range(n_playout):
                    res = playout(copy.deepcopy(newstate), p1, p2)
                    #tmp_results[j] += sign * res
                    #tmp_node.value += sign * res
                    tmp_results[j] += res
                    tmp_node.value += res
                tmp_nodes.append(tmp_node)
            #if node.layer%2==0:
            #    idx = np.argmax(tmp_results)
            #else:
            #    idx = np.argmin(tmp_results)
            #idx = np.argmax(tmp_results)
            idx = np.argmin(tmp_results)
            node = tmp_nodes[idx]
            judge = judge_state(node.state, node.pass_p1, node.pass_p2, 1)
            if judge[1]==0:
                break
        sign = 1 if node.layer%2==0 else -1
        results[i] = sign * node.value 
    return action_list[np.argmax(results)]
    
class TreeNode(object):
    def __init__(self, state, pass_p1, pass_p2, topnode, layer):
        self.state = state
        self.pass_p1 = pass_p1
        self.pass_p2 = pass_p2
        self.topnode = topnode
        self.layer = layer
        self.trial = 0
        self.value = 0
        self.parent = None
        self.kids = []

    
def npc_ucb1(state, pass_p1, pass_p2):
    def ucb1(node, sign):
        if node.trial == 0:
            return np.inf
        if node.parent == None:
            brothers = root_list
        else:
            brothers = node.parent.kids
        t = 0
        for i in range(len(brothers)):
            t += brothers[i].trial
        if sign==1:
            return node.value/node.trial + np.sqrt(2*np.log(t)/node.trial)
        else:
            return 1-node.value/node.trial + np.sqrt(2*np.log(t)/node.trial)

    n_playout_total = 1200
    n_playout_each = 50
    action_list = legalaction(state)
    action_list.append("pass")
    nn = len(action_list)
    root_list = []
    for i in range(nn):
        newstate = -update(copy.deepcopy(state), action_list[i])
        p1 = pass_p2
        p2 = pass_p1+1 if action_list[i] == "pass" else pass_p1
        node = TreeNode(newstate, p1, p2, i, 1)
        root_list.append(node)
    for i in range(n_playout_total):
        nodes = root_list
        while True:
            layer = nodes[0].layer -1
            sign = 1 if layer%2==0 else -1
            vals = [ucb1(node, sign) for node in nodes]
            node = nodes[np.argmax(vals)]
            if len(node.kids)==0:
                break
            nodes = node.kids
        res = playout(copy.deepcopy(node.state), node.pass_p1, node.pass_p2)
        sign = 1 if node.layer%2==0 else -1
        res = sign*res
        res = (res+1)/2
        node.trial += 1
        node.value += res
        judge = judge_state(node.state, node.pass_p1, node.pass_p2, sign)
        if node.trial==n_playout_each and judge[1]!=0:
            tmp_action_list = legalaction(node.state)
            tmp_action_list.append("pass")
            nnn = len(tmp_action_list)
            for j in range(nnn):
                newstate = -update(copy.deepcopy(node.state), tmp_action_list[j])
                p1 = node.pass_p2
                p2 = node.pass_p1+1 if tmp_action_list[j] == "pass" else node.pass_p1
                kid = TreeNode(newstate, p1, p2, node.topnode, node.layer+1)
                kid.parent = node
                node.kids.append(kid)
        while node.parent is not None:
            node = node.parent
            node.trial += 1
            node.value += res
    trials = np.array([0 for _ in range(nn)])
    values = np.array([0 for _ in range(nn)])
    for i in range(nn):
        node = root_list[i]
        trials[i] = node.trial
        values[i] = node.value
    return action_list[np.argmax(trials)]
    

def playout(state, pass_p1, pass_p2):
    judge = judge_state(state, pass_p1, pass_p2, 1)
    if judge[1] == 0:
        return judge[0]
    legal_action_list = legalaction(state)
    if random.random()<0.0 or len(legal_action_list)==0:
        return -playout(-state, pass_p2, pass_p1+1)
    else:
        tmp = random.randrange(len(legal_action_list))
        action = legal_action_list[tmp]
        state = update(state, action)
        return -playout(-state, pass_p2, pass_p1)

def update_you(state, pass_you, pass_npc):
    legal_action_list = legalaction(state)
    print("You:", np.sum(state==1), " pass:", pass_you)
    print("NPC:", np.sum(state==-1), " pass:", pass_npc)
    while True:
        inputaction = input("Your action? >> ")
        if inputaction == "quit" or inputaction=="q":
            exit() 
        if inputaction == "pass" or len(legal_action_list)==0:
            pass_you += 1
            break
        elif inputaction == "auto":
            action = npc_random(state, pass_you, pass_npc)
            if action == "pass":
                print("(Autopilot) You passed.")
                pass_you += 1
            else:
                print("(Autopilot) You picked", characters[action[0]]+str(action[1])+".")
                state = update(state, action)
            break
        else:
            try:
                action = (actiondict[inputaction[0]], int(inputaction[1]))
            except:
                print("For example,", characters[legal_action_list[0][0]]+str(legal_action_list[0][1])+", pass, or quit.")
                continue
            if action not in legal_action_list:
                print("For example,", characters[legal_action_list[0][0]]+str(legal_action_list[0][1])+", pass, or quit.")
                continue
            state = update(state, action)
            break
    return state, pass_you, pass_npc
    
def playgame(npc):
    pass_you = 0
    pass_npc = 0
    state = init_state()
    action_npc = (n,n)
    while True:
        print_state(state, action_npc)
        state, pass_you, pass_npc = update_you(state, pass_you, pass_npc)
        judge = judge_state(state, pass_you, pass_npc, 1)
        if judge[1]==0:
            break
    
        action_npc = npc(-state, pass_npc, pass_you)
        if action_npc == "pass":
            pass_npc += 1
        else:
            state = -update(-state, action_npc)
    
        judge = judge_state(state, pass_you, pass_npc, -1)
        if judge[1]==0:
            break
    
    if judge[0]==0: 
        print("Draw!    You:", np.sum(state==1), "NPC:", np.sum(state==-1))
    elif judge[0]==1:
        print("You Win!    You:", np.sum(state==1), "NPC:", np.sum(state==-1))
    elif judge[0]==-1:
        print("You Lose!    You:", np.sum(state==1), "NPC:", np.sum(state==-1))

def autoplay(npc1,npc2):
    pass_p1 = 0
    pass_p2 = 0
    state = init_state()
    while True:
        action_p1 = npc1(state, pass_p1, pass_p2)
        if action_p1 == "pass":
            pass_p1 += 1
        else:
            state = update(state, action_p1)
        judge = judge_state(state, pass_p1, pass_p2, 1)
        if judge[1]==0:
            break

        action_p2 = npc2(-state, pass_p2, pass_p1)
        if action_p2 == "pass":
            pass_p2 += 1
        else:
            state = -update(-state, action_p2)
        judge = judge_state(state, pass_p1, pass_p2, -1)
        if judge[1]==0:
            break
        #print_state(state, action_p2)
    
    if judge[0]==0: 
        print("Draw!       P1:", np.sum(state==1),"(pass:", pass_p1, "), P2:", np.sum(state==-1), "(pass:", pass_p2, ")")
    elif judge[0]==1:
        print("P1 Wins!    P1:", np.sum(state==1),"(pass:", pass_p1, "), P2:", np.sum(state==-1), "(pass:", pass_p2, ")")
    elif judge[0]==-1:
        print("P2 Wins!    P1:", np.sum(state==1),"(pass:", pass_p1, "), P2:", np.sum(state==-1), "(pass:", pass_p2, ")")
    

#playgame(npc_random)
#playgame(npc_shallow_playout)
#playgame(npc_minmax)
playgame(npc_ucb1)
#autoplay(npc_ucb1, npc_random)
#autoplay(npc_ucb1, npc_shallow_playout)
#autoplay(npc_ucb1, npc_minmax)


