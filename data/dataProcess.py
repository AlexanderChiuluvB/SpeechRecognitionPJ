import os
from torch.utils import data
import scipy.io.wavfile as wav
import numpy as np
import torch
from utils import utils
from utils import dataPreProcess
from utils.utils import mfcc
import random
import librosa

class SpeechData(data.Dataset):

    def __init__(self,dataList):
        self.data = []
        for data in dataList:
            self.data +=data

    def __getitem__(self, index):

        (dataPath,label) = self.data[index]
        feature = Featurize(dataPath)

        return feature,torch.tensor(label)

    def __len__(self):
        """
        返回数据集中所有数据个数
        """
        return len(self.data)

def Featurize(path):
    """

    :param path:
    :return:
    """



    paddedLength = 55000
    y, sr = librosa.load(path)

    try:
        y = dataPreProcess.padding(y,paddedLength)
    except:
        pass

    feat = dataPreProcess.stft(y, hop_length=512, n_fft=2048)
    #得到功率谱
    feat = np.abs(feat) ** 2
    #做梅尔滤波,并且取对数，然后提取能量谱
    feat = dataPreProcess.melspectrogram(Spec=feat, sigRate=sr, n_mels=128)
    #均一化
    feat = (feat - np.mean(feat)) / (np.sqrt(np.sum(feat ** 2)+0.0000001))
    feat = feat.reshape(1, feat.shape[0], -1)
    feat = torch.from_numpy(feat).type(torch.float)

    return feat


def getFolder(fold_n=10):
    """

    return: a list with elements as a list
    """

    rootDir ='../speechPJ/speech_data'
    studentsID = os.listdir(rootDir)
    speechData = []
    for d in studentsID:
        if d=='16307130343':
            #数据损坏
            continue
        audioFileList = os.listdir(rootDir+'/'+d)
        for f in audioFileList:
            pathName = os.path.join(rootDir,d,f)
            if not pathName.endswith('.wav'):
                continue
            label = int(pathName[-9:-7])
            speechData.append((pathName,label))

    random.shuffle(speechData)
    totalLen = len(speechData)
    eachFolderSize = totalLen//fold_n
    folder =[speechData[i:i+eachFolderSize] for i in range(0,totalLen,eachFolderSize)]

    return folder

def loadDataset(folder,partition,batch_size,fold_n=10):
    """

    :param partition:
    :param batch_size:
    :param train:
    :param fold_n: 10 默认十折交叉验证
    :return:
    """
    from itertools import chain

    trainFolder = folder[:partition]+folder[partition+1:]
    #trainFolder = list(chain(*trainFolder))
    trainLoader = torch.utils.data.DataLoader(SpeechData(trainFolder),shuffle=True,batch_size=batch_size,pin_memory=True,num_workers=32)
    validFolder = folder[partition:partition+1]
    #validFolder = list(chain(*validFolder))
    validLoader = torch.utils.data.DataLoader(SpeechData(validFolder),shuffle=True,batch_size=batch_size,pin_memory=True,num_workers=32)


    return trainLoader,validLoader


if __name__ =='__main__':
    feat = Featurize('../upload/audio.wav')
