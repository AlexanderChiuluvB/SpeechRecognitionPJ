import numpy as np
from scipy.fftpack import dct
from python_speech_features import mfcc

def preEmphasis(audioSignal,preEmphCof):
    """

    预加重处理其实是将语音信号通过一个高通滤波器：

    :param audioSignal:
    :param preEmphCof: 0.97
    :return:
    """
    firstSignal = audioSignal[0]
    firstAfterSignal = audioSignal[1:]
    exceptFirstSignal = audioSignal[:-1]

    result = np.append(firstSignal,firstAfterSignal-preEmphCof*exceptFirstSignal)
    return result


def Framing(signal,frameLen,frameSteps):
    """

    :param signal:
    :param frameLen: 帧长度 16000*0.025 = 400
    :param frameSteps: 16000*0.01 = 160
    :return:

    windowLen=0.025
    windowSteps=0.01

    """

    signalLen = len(signal)
    frameLen = int(np.ceil(frameLen))
    frameSteps = int(np.ceil(frameSteps))

    #帧个数
    numframes = int(np.ceil(float(np.abs(1.0*signalLen-frameLen))/frameSteps))

    #对信号做padding后的长度
    paddingLen = int((numframes)*frameSteps+frameLen)

    zeros = np.zeros((paddingLen-signalLen,))

    paddingSingal = np.concatenate((signal,zeros))

    """
    array([[    0,     1,     2, ...,   509,   510,   511],
       [  256,   257,   258, ...,   765,   766,   767],
       [  512,   513,   514, ...,  1021,  1022,  1023],
       ...,
       [50944, 50945, 50946, ..., 51453, 51454, 51455],
       [51200, 51201, 51202, ..., 51709, 51710, 51711],
       [51456, 51457, 51458, ..., 51965, 51966, 51967]], dtype=int32)
    
    每帧长度为512,相邻两帧之间的重叠个数为256
    
    """

    indices = np.tile(np.arange(0,frameLen),(numframes,1))+np.tile(
            np.arange(0, numframes * frameSteps, frameSteps), (frameLen, 1)).T

    indices = np.array(indices,dtype=np.int32)

    frames = paddingSingal[indices]

    #加汉宁窗
    window = periodic_hann(frameLen)

    return frames*window

def periodic_hann(windowLen):


    """
    汉宁窗

    以增加帧左端和右端的连续性

    :param windowLen:
    :return:

    ref: https://github.com/tensorflow/models/blob/master/research/audioset/mel_features.py
    """

    return 0.5 *(1-np.cos(2*np.pi/windowLen*np.arange(windowLen)))



def Power(frames,fftSize):
    """

    频谱取模平方得到功率谱

    :param frames:
    :param fftSize: FFT长度
    :return:
    """
    magnitude = np.absolute(np.fft.rfft(frames,fftSize))
    result = (1/fftSize) *np.square(magnitude)

    return result


def hz2mel(hz):
    """
    把普通频率转化为mel频率

    :param hz:
    :return:
    """
    return 2595*np.log10(1+hz/700.)

def mel2hz(mel):
    """
    把mel频率转化为普通频率
    :param mel:
    :return:
    """
    return 700*(10**(mel/2595.0)-1)

def MelFilter(filterNum,fftSize,sampleRate,lowFreq,highFreq):

    """

    :param filterNum: 滤波器数量
    :param fftSize: FFT大小
    :param sampleRate: 采样频率
    :param lowFreq: 梅尔滤波器的最低边缘
    :param highFreq: 梅尔滤波器的最高边缘，默认为采样率/2
    :return:
    """

    ### 采样频率至少是最高频率的两倍
    highFreq = sampleRate/2

    lowmel = hz2mel(lowFreq)

    highmel = hz2mel(highFreq)

    melpoints = np.linspace(lowmel,highmel,filterNum+2)

    ### 把hz转换为fft bin number

    bin = np.floor((fftSize+1)*mel2hz(melpoints)/sampleRate)

    result = np.zeros([filterNum,fftSize//2+1])

    #下面是做滤波
    for i in range(0,filterNum):
        for j in range(int(bin[i]),int(bin[i+1])):
            result[i,j] = (j-bin[i])/(bin[i+1]-bin[i])

        for j in range(int(bin[i+1]),int(bin[i+2])):
            result[i,j] = (bin[i+2]-j) / (bin[i+2]-bin[i+1])
    return result


def preProcess(audioSignal,sampleRate,windowLen,
                           windowSteps,filterNum,fftSize,lowFreq,
                           highFreq,preEmphCof):
    """
    :param audioSignal:
    :param sampleRate:
    :param windowLen:
    :param windowSteps:
    :param filterNum:
    :param fftSize:
    :param lowFreq:
    :param highFreq:
    :param preEmphCof:
    :param AnalysisWindow:
    :return:
    """
    #最高频率为采样频率的一半
    highFreq = highFreq or sampleRate /2

    #预加重
    signal = preEmphasis(audioSignal,preEmphCof)

    #分帧
    frames = Framing(signal,windowLen*sampleRate,windowSteps*sampleRate)

    #取平方
    power = Power(frames,fftSize)

    #计算每一帧的能量总和
    energy = np.sum(power,1)

    #如果能量为0 则设为浮点数的max
    energy = np.where(energy==0,np.finfo(float).eps,energy)

    #Mel 滤波
    filtered = MelFilter(filterNum,fftSize,sampleRate,lowFreq,highFreq)

    feature = np.dot(power,filtered.T)
    feature = np.where(feature==0,np.finfo(float).eps,feature)

    return feature,energy



def discreteCosineTransform(x):
    """
    离散余弦变换DCT
    得到MFCC
    :param x:
    :return:
    """

    """
    
    以下是自己实现的dct
    但考虑到掉包的话是调用用C写的代码，速度会快很多，
    因此这里提取特征的时候还是掉包把，这样识别速度以及特征处理会快很多
    
    def mydct(feature):
    
    m,n = feature.shape
    
    dctFeature = np.zeros((m,n))
    
    for i in range(m):
        for j in range(n):
            
            if(i==0):
                ci = 1/np.sqrt(m)
            else:
                ci = np.sqrt(2)/np.sqrt(m)
            
            if(j==0):
                cj = 1/np.sqrt(n)
            else:
                cj = np.sqrt(2)/np.sqrt(n)
        
            sumRes = 0
            
            for k in range(m):
                for l in range(n):
                    
                    dct1 = 2* feature[k][l]*np.cos(np.pi*k*(2*l+1)/2*n)
                    sumRes+=dct1
            dctFeature[i][j] = ci*cj*sumRes
            
    return dctFeature
    
    """


    return dct(x,type=2,axis=1,norm='ortho')


def lifter(cepstra,L=22):
    """
    :param cepstra: matrix of mel-cepstra (numFrames* cepstraNum)
    :param L: liftering coefficient
    :return:  (1+ sin(π×N/L)*(L/2))*cepstra matrix
    """
    nframes,ncoeff = np.shape(cepstra)
    N = np.arange(ncoeff)

    lift = 1 +(L/2.)*np.sin(np.pi*N/L)

    return cepstra*lift

def mymfcc(audioSignal,sampleRate=16000):
    """

    :param audioSignal:
    :param sampleRate:
    :return:
    """

    windowLen=0.032 #16000 * 0.032 = 512 帧长度为512
    windowSteps=0.016 #使得两个帧之间的重叠长度为帧长的二分之一
    cepstrumNum=13 #梅尔频率13个特征
    fftSize=1024 #FFT大小
    filterNum=128#滤波器个数
    lowFreq = 0
    highFreq = None
    #AnalysisWindow = lambda x:np.ones((x,))
    #AnalysisWindow = lambda x:np.hanning((x))
    # preemphasis filter with preEmphCof as coefficient
    preEmphCof = 0.97

    """
    normalize signal
    """

    #high,low = abs(max(audioSignal)),abs(min(audioSignal))
    #audioSignal  = audioSignal/max(high,low)

    feature,energy = preProcess(audioSignal,sampleRate,windowLen,
                           windowSteps,filterNum,fftSize,lowFreq,
                           highFreq,preEmphCof)


    #每个滤波器输出的能量取对数
    #feature = np.log(feature)
    #逆变换得到MFCC系数
    #feature = discreteCosineTransform(feature)
    #前13个系数,作为MFCC
    #feature = feature[:,:cepstrumNum]
    #把高频的频率幅度增大
    #feature = lifter(feature)
    # 均一化
    #feature -=np.mean(feature,1,keepdims=True)

    ##replace first cepstral coefficient with log of frame energy
    #feature[:,0] = np.log(energy)


    return feature


