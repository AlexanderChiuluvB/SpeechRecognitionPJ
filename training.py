import shutil
from tensorboardX import SummaryWriter
import torch
from utils.utils import *
from data.dataProcess import *
from models.VGG import *


import shutil
from tensorboardX import SummaryWriter


class AverageMeter(object):
    """Computes and stores the average and current value"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def save_checkpointer(checkpointer,is_best,file_name='log/checkpoint.pth'):
    torch.save(checkpointer, file_name)
    if is_best:
        shutil.copyfile(file_name,'model_best.pth')



import time
writer = SummaryWriter('log')
def train(model,epochs,batch_size,lr=4e-5,weight_decay=0.000001,print_freq=100):

    batch_time = AverageMeter()
    data_time = AverageMeter()
    losses = AverageMeter()
    top1 = AverageMeter()
    top5 = AverageMeter()

    optimizer = torch.optim.Adam(model.parameters(), lr)
    criterion = torch.nn.CrossEntropyLoss().cuda()

    #switch to train mode
    model.train()
    print("训练开始")
    folder = getFolder()
    best_acc = 0

    for epoch in range(epochs):

        train_dataLoader,valid_dataLoader = loadDataset(folder=folder,partition=epoch%len(folder),batch_size=batch_size)

        end = time.time()
        for i,(data,label) in enumerate(train_dataLoader):
            data_time.update(time.time() - end)


            data = torch.autograd.Variable(data)
            label = torch.autograd.Variable(label)

            predictY = model(data)
            loss = criterion(predictY,label)

            prec1,prec5 = accuracy(predictY.data,label,topk=(1,5))
            #xwriter.add_scalar("loss/{}epoch".format(e),loss.item()/data.size(0),i)
            #losses.append(loss.item()/data.size(0))
            #print(data.size(0))
            losses.update(loss.item(),data.size(0))
            top1.update(prec1.item(),data.size(0))
            top5.update(prec5.item(),data.size(0))

            #compute gradient and do SGD step
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            batch_time.update(time.time() - end)
            end = time.time()
            niter = epoch*len(train_dataLoader)+i
            writer.add_scalar('训练/Loss', losses.val, niter)
            writer.add_scalar('训练/Prec@1', top1.val, niter)
            writer.add_scalar('训练/Prec@5', top5.val, niter)

        acc = validate(epoch,valid_dataLoader, model, criterion)
        is_best = acc>best_acc
        best_acc = max(acc,best_acc)
        checkpointer = {
        'epoch':epoch+1,
        'acc':acc,
        'state_dict': model.state_dict(),
        'optimizer': optimizer.state_dict()
        }
        save_checkpointer(checkpointer,is_best)


def accuracy(output, target, topk=(1,)):
    """Computes the precision@k for the specified values of k"""
    maxk = max(topk)
    batch_size = target.size(0)

    _, pred = output.topk(maxk, 1, True, True)
    pred = pred.t()
    correct = pred.eq(target.view(1, -1).expand_as(pred))

    res = []
    for k in topk:
        correct_k = correct[:k].view(-1).float().sum(0)
        res.append(correct_k.mul_(100.0 / batch_size))
    return res


def validate(epoch,val_loader, model, criterion,print_freq=100):
    batch_time = AverageMeter()
    losses = AverageMeter()
    top1 = AverageMeter()
    top5 = AverageMeter()

    # switch to evaluate mode
    model.eval()

    end = time.time()
    for i, (input, target) in enumerate(val_loader):

        input_var = torch.autograd.Variable(input, volatile=True)
        target_var = torch.autograd.Variable(target, volatile=True)

        # compute output
        output = model(input_var)
        loss = criterion(output, target_var)

        # measure accuracy and record loss
        prec1, prec5 = accuracy(output.data, target, topk=(1, 5))
        losses.update(loss.item(), input.size(0))
        top1.update(prec1.item(), input.size(0))
        top5.update(prec5.item(), input.size(0))

        # measure elapsed time
        batch_time.update(time.time() - end)
        end = time.time()

        niter = epoch*len(val_loader)+i
        writer.add_scalar('Test/Loss', losses.val, niter)
        writer.add_scalar('Test/Prec@1', top1.val, niter)
        writer.add_scalar('Test/Prec@5', top5.val, niter)
    print(' * Prec@1 {top1.avg:.3f} Prec@5 {top5.avg:.3f}'
.format(top1=top1, top5=top5))

    return top1.avg

def infer(model,data_path):

    feature = Featurize(data_path)
    feature = feature[None,:,:,:]
    model.eval()
    feature_var = torch.autograd.Variable(feature, volatile=True)
    output = model(feature_var)
    argmax = torch.argmax(output,dim=1).item()

    return argmax


if __name__ =='__main__':
    model = vgg11_bn()
    model.train()
    train(model,epochs=10,batch_size=128)

