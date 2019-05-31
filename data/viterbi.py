
import numpy as np

#红色为0 白色为1
#统计学习方法 186页

#转移矩阵 三个状态相互转移的概率
A = np.asarray([[0.5, 0.2, 0.3], [0.3, 0.5, 0.2], [0.2, 0.3, 0.5]]) # 转移矩阵

#输出概率
#B[0][i]为第0个状态输出为i的概率 eg0.5是第一个状态输出为红色的概率
B = np.asarray([[0.5, 0.5],
                [0.4, 0.6],
                [0.7, 0.3]])

#初始分布矩阵
Pi = np.asarray([0.2, 0.4, 0.4]).transpose()

O = np.asarray([0,1,0]) #红白红 时间序列观察到的结果


def viterbi(A,B,O,Pi):
    """

    通常概率取对数，乘法转换为加法

    :param A: 转移矩阵
    :param B: 输出矩阵
    :param O: 观测序列
    :param Pi:  初始状态概率分布
    :return:
    """

    T = O.shape[0]
    N = A.shape[0]  # 状态数


    # Pi:1x3  B[:,O[0]] 3x1
    prob_list = Pi * B[:,O[0]]
    path = list()

    for state in range(N):
        #path is a list that saves all the best path staring from different state

        path.append([state])

    for t in range(1,T):
        for cur_state in range(N):
            cur_list = list()
            for last_state in range(N):
                prob_trans = A[last_state,cur_state]
                prob_out = B[cur_state,O[t]]
                #上一个状态的概率*转移概率*输出概率
                cur_list.append(prob_list[last_state]*prob_trans*prob_out)
            prob_list[cur_state] = np.max(cur_list)# 更新状态路径概率
            #状态路径概率最大对应的状态
            max_index = np.argmax(cur_list)
            temp = path[max_index][:]
            temp.append(cur_state)
            path[cur_state] = temp

    print(prob_list)
    print(path)
    max_index = np.argmax(prob_list)
    #最优状态序列
    max_path = path[max_index]
    print(max_path)

    return max_path





viterbi(A,B,O,Pi)