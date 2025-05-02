# ！/usr/bin/env python
# _*_ coding:utf-8 _*_

'''

@author: yerik

@contact: xiangzz159@qq.com

@time: 2025/5/1 15:36

@desc: 接入网络数据元

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

# 禁用沙盒数据
abupy.env.disable_example_env_ipython()

from abupy import ABuSymbolPd
from abupy import EMarketDataFetchMode


def main():
    abupy.env.g_data_fetch_mode = EMarketDataFetchMode.E_DATA_FETCH_FORCE_NET
    # kl_df = ABuSymbolPd.make_kl_df('603777')
    # kl_df = ABuSymbolPd.make_kl_df('usTSLA')
    kl_df = ABuSymbolPd.make_kl_df('hk00700')
    if kl_df is None:
        print("kl_df is None")
    else:
        print(kl_df.tail())



if __name__ == '__main__':
    main()
