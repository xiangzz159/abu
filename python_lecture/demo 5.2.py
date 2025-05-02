# ！/usr/bin/env python
# _*_ coding:utf-8 _*_

'''

@author: yerik

@contact: xiangzz159@qq.com

@time: 2025/4/29 18:51

@desc:

'''


from __future__ import division
from __future__ import print_function

import warnings

warnings.filterwarnings('ignore')
warnings.simplefilter('ignore')

import os
import sys
# 使用insert 0即只使用github，避免交叉使用了pip安装的abupy，导致的版本不一致问题
sys.path.insert(0, os.path.abspath('../'))
import abupy

# 使用沙盒数据，目的是和书中一样的数据环境
abupy.env.enable_example_env_ipython()

from abupy import AbuBenchmark, AbuCapital, AbuPickRegressAngMinMax, ABuRegUtil, ABuPickStockExecute, AbuKLManager

stock_pickers = [{'class': AbuPickRegressAngMinMax,
                  'threshold_ang_min': 0.0, 'threshold_ang_max': 10.0,
                  'reversed': False}]

# 从这几个股票里进行选股，只是为了演示方便
# 一般的选股都会是数量比较多的情况比如全市场股票
choice_symbols = ['usNOAH', 'usSFUN', 'usBIDU', 'usAAPL', 'usGOOG',
                  'usTSLA', 'usWUBA', 'usVIPS']

benchmark = AbuBenchmark()
capital = AbuCapital(1000000, benchmark)
kl_pd_manger = AbuKLManager(benchmark, capital)
choice_symbols = ABuPickStockExecute.do_pick_stock_work(choice_symbols, benchmark,
                                       capital, stock_pickers)
# 打印最后的选股结果
print(choice_symbols)

kl_pd_sfun = kl_pd_manger.get_pick_stock_kl_pd('usSFUN')
print('sfun 选股周期内角度={:.3f}'.format(ABuRegUtil.calc_regress_deg(kl_pd_sfun.close)))

kl_pd_baidu = kl_pd_manger.get_pick_stock_kl_pd('usBIDU')
print('bidu 选股周期内角度={:.3f}'.format(ABuRegUtil.calc_regress_deg(kl_pd_baidu.close)))
