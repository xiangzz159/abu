# ！/usr/bin/env python
# _*_ coding:utf-8 _*_

'''

@author: yerik

@contact: xiangzz159@qq.com

@time: 2025/4/29 19:10

@desc:

'''

# 基础库导入
from __future__ import print_function
from __future__ import division

import warnings

warnings.filterwarnings('ignore')
warnings.simplefilter('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets

import os
import sys

# 使用insert 0即只使用github，避免交叉使用了pip安装的abupy，导致的版本不一致问题
sys.path.insert(0, os.path.abspath('../'))
import abupy

# 使用沙盒数据，目的是和书中一样的数据环境
abupy.env.enable_example_env_ipython()
from abupy import AbuFactorAtrNStop, AbuFactorPreAtrNStop, AbuFactorCloseAtrNStop, AbuFactorBuyBreak
from abupy import abu, ABuFileUtil, ABuGridHelper, GridSearch, AbuBlockProgress, ABuProgress


def main():
    stop_win_range = np.arange(2.0, 4.5, 0.5)
    stop_loss_range = np.arange(0.5, 2, 0.5)

    sell_atr_nstop_factor_grid = {
        'class': [AbuFactorAtrNStop],
        'stop_loss_n': stop_loss_range,
        'stop_win_n': stop_win_range
    }
    print('AbuFactorAtrNStop止盈参数stop_win_n设置范围:{}'.format(stop_win_range))
    print('AbuFactorAtrNStop止损参数stop_loss_n设置范围:{}'.format(stop_loss_range))

    close_atr_range = np.arange(1.0, 4.0, 0.5)
    pre_atr_range = np.arange(1.0, 3.5, 0.5)

    sell_atr_pre_factor_grid = {
        'class': [AbuFactorPreAtrNStop],
        'pre_atr_n': pre_atr_range
    }

    sell_atr_close_factor_grid = {
        'class': [AbuFactorCloseAtrNStop],
        'close_atr_n': close_atr_range
    }
    print('暴跌保护止损参数pre_atr_n设置范围:{}'.format(pre_atr_range))
    print('盈利保护止盈参数close_atr_n设置范围:{}'.format(close_atr_range))

    sell_factors_product = ABuGridHelper.gen_factor_grid(
        ABuGridHelper.K_GEN_FACTOR_PARAMS_SELL,
        [sell_atr_nstop_factor_grid, sell_atr_pre_factor_grid, sell_atr_close_factor_grid], need_empty_sell=True)
    print('卖出因子参数共有{}种组合方式'.format(len(sell_factors_product)))
    print('卖出因子组合0: 形式为{}'.format(sell_factors_product[0]))

    buy_bk_factor_grid1 = {
        'class': [AbuFactorBuyBreak],
        'xd': [42]
    }

    buy_bk_factor_grid2 = {
        'class': [AbuFactorBuyBreak],
        'xd': [60]
    }

    buy_factors_product = ABuGridHelper.gen_factor_grid(
        ABuGridHelper.K_GEN_FACTOR_PARAMS_BUY, [buy_bk_factor_grid1, buy_bk_factor_grid2])

    print('买入因子参数共有{}种组合方式'.format(len(buy_factors_product)))
    print('买入因子组合形式为{}'.format(buy_factors_product))
    print('组合因子参数数量{}'.format(len(buy_factors_product) * len(sell_factors_product)))

    read_cash = 1000000
    choice_symbols = ['usNOAH', 'usSFUN', 'usBIDU', 'usAAPL', 'usGOOG',
                      'usTSLA', 'usWUBA', 'usVIPS']
    grid_search = GridSearch(read_cash, choice_symbols,
                             buy_factors_product=buy_factors_product,
                             sell_factors_product=sell_factors_product)

    scores, score_tuple_array = grid_search.fit()

    print('最终评分结果数量{}'.format(len(scores)))

    from abupy import AbuMetricsBase
    best_score_tuple_grid = grid_search.best_score_tuple_grid
    AbuMetricsBase.show_general(best_score_tuple_grid.orders_pd, best_score_tuple_grid.action_pd,
                                best_score_tuple_grid.capital, best_score_tuple_grid.benchmark)

    from abupy import WrsmScorer
    scorer = WrsmScorer(score_tuple_array)
    scorer.fit_score()
    scorer.score_pd.to_csv('./score.csv', index=False)
    print(scorer.score_pd.tail())

    # 实例化WrsmScorer，参数weights，只有第二项为1，其他都是0，
    # 代表只考虑投资回报来评分
    scorer = WrsmScorer(score_tuple_array, weights=[0, 1, 0, 0])
    # 返回排序后的队列
    scorer_returns_max = scorer.fit_score()
    # 因为是倒序排序，所以index最后一个为最优参数
    best_score_tuple_grid = score_tuple_array[scorer_returns_max.index[-1]]
    # 由于篇幅，最优结果只打印文字信息
    AbuMetricsBase.show_general(best_score_tuple_grid.orders_pd,
                                best_score_tuple_grid.action_pd,
                                best_score_tuple_grid.capital,
                                best_score_tuple_grid.benchmark,
                                only_info=True)




if __name__ == '__main__':
    main()
