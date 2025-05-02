# ！/usr/bin/env python
# _*_ coding:utf-8 _*_

'''

@author: yerik

@contact: xiangzz159@qq.com

@time: 2025/4/29 18:31

@desc:

'''


from __future__ import print_function
from __future__ import division

import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import os
import sys
# 使用insert 0即只使用github，避免交叉使用了pip安装的abupy，导致的版本不一致问题
sys.path.insert(0, os.path.abspath('../'))
import abupy

# 使用沙盒数据，目的是和书中一样的数据环境
abupy.env.enable_example_env_ipython()
from abupy import AbuFactorBuyBreak, AbuFactorSellBreak, AbuPositionBase
from abupy import AbuFactorAtrNStop, AbuFactorPreAtrNStop, AbuFactorCloseAtrNStop
from abupy import ABuPickTimeExecute, AbuBenchmark, AbuCapital, AbuKellyPosition, AbuMetricsBase

# 选定noah和sfun
target_symbols = ['usSFUN', 'usNOAH']

# 针对sfun只使用42d向上突破作为买入因子
buy_factors_sfun = [{'xd': 42, 'class': AbuFactorBuyBreak}]
# 针对sfun只使用60d向下突破作为卖出因子
sell_factors_sfun = [{'xd': 60, 'class': AbuFactorSellBreak}]

# 针对noah只使用21d向上突破作为买入因子
buy_factors_noah = [{'xd': 21, 'class': AbuFactorBuyBreak}]
# 针对noah只使用42d向下突破作为卖出因子
sell_factors_noah = [{'xd': 42, 'class': AbuFactorSellBreak}]

factor_dict = dict()
# 构建SFUN独立的buy_factors，sell_factors的dict
factor_dict['usSFUN'] = {'buy_factors': buy_factors_sfun,
                         'sell_factors': sell_factors_sfun}

# 构建NOAH独立的buy_factors，sell_factors的dict
factor_dict['usNOAH'] = {'buy_factors': buy_factors_noah,
                         'sell_factors': sell_factors_noah}

benchmark = AbuBenchmark()
capital = AbuCapital(1000000, benchmark)
orders_pd, action_pd, all_fit_symbols = ABuPickTimeExecute.do_symbols_with_diff_factors(target_symbols,
                                                                                        benchmark,
                                                                                        factor_dict,
                                                                                        capital)
print(orders_pd[:10].filter(['symbol', 'buy_cnt', 'buy_factor', 'buy_pos']))

metrics = AbuMetricsBase(orders_pd, action_pd, capital, benchmark)
metrics.fit_metrics()
metrics.plot_returns_cmp(only_show_returns=True)
