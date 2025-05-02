# ！/usr/bin/env python
# _*_ coding:utf-8 _*_

'''

@author: yerik

@contact: xiangzz159@qq.com

@time: 2025/4/27 22:43

@desc:

'''
from __future__ import division
# 基础库导入，注意第一次运行时会比较慢，要做数据的解压等处理操作
from __future__ import print_function

import warnings

warnings.filterwarnings('ignore')
warnings.simplefilter('ignore')

import os
import sys

# 使用insert 0即只使用github，避免交叉使用了pip安装的abupy，导致的版本不一致问题
sys.path.insert(0, os.path.abspath('../'))
import abupy
abupy.env.enable_example_env_ipython()

from abupy import AbuBenchmark
from abupy import AbuCapital, AbuFactorBuyBreak
from abupy import AbuFactorSellBreak

# 使用120天向下突破为卖出信号
sell_factor1 = {'xd': 120, 'class': AbuFactorSellBreak}

# buy_factors 60日向上突破，42日向上突破两个因子
buy_factors = [{'xd': 60, 'class': AbuFactorBuyBreak},
               {'xd': 42, 'class': AbuFactorBuyBreak}]
# 只使用120天向下突破为卖出因子
sell_factors = [sell_factor1]
benchmark = AbuBenchmark()
capital = AbuCapital(1000000, benchmark)

from abupy import ABuPickTimeExecute
orders_pd, action_pd, _ = ABuPickTimeExecute.do_symbols_with_same_factors(['usTSLA'],
                                                                            benchmark,
                                                                            buy_factors,
                                                                            sell_factors,
                                                                            capital, show=True)
