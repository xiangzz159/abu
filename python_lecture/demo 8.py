# ！/usr/bin/env python
# _*_ coding:utf-8 _*_

'''

@author: yerik

@contact: xiangzz159@qq.com

@time: 2025/4/29 20:07

@desc:

'''

# 基础库导入

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
from abupy import EMarketTargetType

# 使用沙盒数据，目的是和书中一样的数据环境
abupy.env.enable_example_env_ipython()
abupy.env.g_market_target = EMarketTargetType.E_MARKET_TARGET_CN

def main():
    from abupy import AbuFactorAtrNStop, AbuFactorPreAtrNStop, AbuFactorCloseAtrNStop, AbuFactorBuyBreak
    from abupy import abu, AbuMetricsBase, ABuProgress

    # 设置初始资金数
    read_cash = 1000000

    # 买入因子依然延用向上突破因子
    buy_factors = [{'xd': 60, 'class': AbuFactorBuyBreak},
                   {'xd': 42, 'class': AbuFactorBuyBreak}]

    # 卖出因子继续使用上一节使用的因子
    sell_factors = [
        {'stop_loss_n': 1.0, 'stop_win_n': 3.0,
         'class': AbuFactorAtrNStop},
        {'class': AbuFactorPreAtrNStop, 'pre_atr_n': 1.5},
        {'class': AbuFactorCloseAtrNStop, 'close_atr_n': 1.5}
    ]
    choice_symbols = ['002230', '300104', '300059', '601766', '600085', '600036', '600809', '000002', '002594',
                      '002739']
    # 使用run_loop_back运行策略
    abu_result_tuple, kl_pd_manger = abu.run_loop_back(read_cash,
                                                       buy_factors,
                                                       sell_factors,
                                                       n_folds=6,
                                                       choice_symbols=choice_symbols)
    ABuProgress.clear_output()
    AbuMetricsBase.show_general(*abu_result_tuple, only_show_returns=True)

if __name__ == '__main__':
    main()
