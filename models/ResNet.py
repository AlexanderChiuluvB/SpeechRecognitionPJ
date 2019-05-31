import torch.nn as nn

def conv3x3(in_channel,out_channel,stride=1,groups=1,dilation=1):
    """

    :param in_channel:
    :param out_channel
    :param stride:
    :param groups:
    :param dilation: gap between each kernel
    :return:
    """
    return nn.Conv2d(in_channel,out_channel,stride=stride,groups=groups,
                     dilation=dilation,padding=dilation,bias=False,kernel_size=3)



def conv1x1(in_channel, out_channel, stride=1, groups=1, dilation=1):

    """

    :param in_channel:
    :param out_channel:
    :param stride:
    :param groups:
    :param dilation:
    :return:
    """
    return nn.Conv2d(in_channel, out_channel, stride=stride, groups=groups,
                     dilation=dilation, padding=dilation, bias=False, kernel_size=1)



class BasicBlock(nn.Module):
    expansion = 1

    """
    用于搭建 resNet 18 34 的基本block
    """


    def __init__(self,in_channel,out_channel,stride=1,base_width=64,dilation=1,groups=None):
        super(BasicBlock,self).__init__()
        norm_layer = nn.BatchNorm2d
        self.conv1 = conv3x3(in_channel,out_channel,stride)
        self.bn1 = norm_layer(out_channel)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(out_channel,out_channel)
        self.bn2 = norm_layer(out_channel)
        self.stride = stride

    def forward(self,x):
        """
        残差网络的构建
        :param x:
        :return:
        """

        identity = x
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)

        x = self.conv2(x)
        x = self.bn2(x)

        x+=identity #skip connection
        x = self.relu(x)

        return x


class BottleNeck(nn.Module):
    """
    用于搭建ResNet 50 101 152 的block

    """
    expansion = 4

    def __init__(self, in_channel, out_channel, groups=1,stride=1, base_width=64, dilation=1):
        super(BottleNeck, self).__init__()
        norm_layer = nn.BatchNorm2d
        width = int(out_channel*(base_width/64.))*groups
        self.conv1 = conv1x1(in_channel, width)
        self.bn1 = norm_layer(width)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(width, width)
        self.bn2 = norm_layer(width)
        self.conv3 = conv1x1(width,out_channel*self.expansion)
        self.bn3 = norm_layer(out_channel*self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.stride = stride

    def forward(self, x):
        """
        残差网络的构建
        :param x:
        :return:
        """

        identity = x
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)

        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu(x)

        x = self.conv3(x)
        x = self.bn3(x)

        x += identity  # skip connection
        x = self.relu(x)

        return x




class ResNet(nn.Module):

    def __init__(self,block,layers,num_classes=20,groups=1,width_per_group=64):

        super(ResNet,self).__init__()
        self._norm_layer = nn.BatchNorm2d
        self.in_channel = 64

        self.dilation = 1
        self.groups = groups
        self.base_width = width_per_group

        #64 个 7x7 filter
        self.conv1 = nn.Conv2d(1,self.in_channel,kernel_size=7,stride=2,padding=3,bias=False)
        self.bn1 = nn.BatchNorm2d(self.in_channel)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3,stride=2,padding=1)
        self.layer1 = self._make_layer(block,64,layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1])
        self.layer3 = self._make_layer(block,256, layers[2])
        self.layer4 = self._make_layer(block,512, layers[3])

        self.avgpool = nn.AdaptiveAvgPool2d((1,1))
        #全连接层
        self.fc = nn.Linear(512*block.expansion,num_classes)

        for m in self.modules():
            if isinstance(m,nn.Conv2d):
                nn.init.kaiming_normal_(m.weight,mode='fan_out',nonlinearity='relu')
            elif isinstance(m,(nn.BatchNorm2d,nn.GroupNorm)):
                nn.init.constant_(m.weight,1)
                nn.init.constant_(m.bias,0)


        for m in self.modules():
            if isinstance(m, BottleNeck):
                nn.init.constant_(m.bn3.weight, 0)
            elif isinstance(m, BasicBlock):
                nn.init.constant_(m.bn2.weight, 0)


    def _make_layer(self,block,planes,blocks,stride=1,dilate=None):

        """
        构建模型
        :param block:
        :param planes:
        :param blocks:
        :param stride:
        :param dilate:
        :return:
        """
        norm_layer = self._norm_layer
        prev_dilation = self.dilation

        if stride !=1 or self.in_channel != planes* block.expansion:
            downsample = nn.Sequential(

                conv1x1(self.in_channel,block.expansion*planes,stride),
                norm_layer(planes*block.expansion),
            )

        layers = []
        layers.append(block(self.in_channel, planes, groups=self.groups,
                            base_width=self.base_width, dilation=prev_dilation))

        self.in_channel = planes* block.expansion

        for _ in range(1,blocks):
            """
            (self, in_channel, out_channel, groups=1,stride=1, base_width=64, dilation=1):
            """
            layers.append(block(self.in_channel,planes,groups=self.groups,base_width=self.base_width,
                                dilation=self.dilation))

        return nn.Sequential(*layers)


    def forward(self,x):

        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.reshape(x.size(0), -1)
        x = self.fc(x)

        return x



def resnet(layers,in_channel,out_channel,**kwargs):
    """


    :param layers:
    :param in_channel:
    :param out_channel:
    :return:
    """


    model = ResNet(in_channel,out_channel,**kwargs)

    return model

def resnet18(**kwargs):

    """
    4 个basic block

    :param kwargs:
    :return:
    """
    return resnet('resnet18',BasicBlock,[2,2,2,2])

def resnet34(**kwargs):

    """
    4 个basic block

    :param kwargs:
    :return:
    """
    return resnet('resnet34',BasicBlock,[3,4,6,3])

