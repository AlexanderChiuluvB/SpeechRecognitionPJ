"""


可以看到，几乎每个文件夹下都有__init__.py，一个目录如果包含了__init__.py 文件，
那么它就变成了一个包（package）。__init__.py可以为空，也可以定义包的属性和方法，
但其必须存在，其它程序才能从这个目录中导入相应的模块或函数。例如在data/文件夹下有__init__.py，
则在main.py 中就可以from data.dataset import DogCat。而如果在__init__.py中
写入from .dataset import DogCat，则在main.py中就可以直接写为：from data import DogCat，
或者import data; dataset = data.DogCat，相比于from data.dataset import DogCat更加便捷

"""

from .AlexNet import AlexNet
#from .ResNet34 import ResNet34

