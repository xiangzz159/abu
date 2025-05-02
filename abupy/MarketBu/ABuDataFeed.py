# coding=utf-8
"""
    内置数据源示例实现模块：

    所有数据接口仅供学习使用，以及最基本使用测试，如需进一步使用，请购买数据
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os

import random
import math
import sqlite3 as sqlite
import json
import akshare as ak

import pandas as pd
import numpy as np

from ..CoreBu.ABuEnv import EMarketTargetType, EMarketSubType
from ..CoreBu import ABuEnv
from ..MarketBu import ABuNetWork
from ..MarketBu.ABuDataBase import StockBaseMarket, SupportMixin, FuturesBaseMarket, TCBaseMarket
from ..MarketBu.ABuDataParser import AkShareParser, TXParser, NTParser, SNUSParser
from ..MarketBu.ABuDataParser import SNFuturesParser, SNFuturesGBParser, BNTCParser
from ..UtilBu import ABuStrUtil, ABuDateUtil, ABuMd5
from ..UtilBu.ABuDTUtil import catch_error
from ..CoreBu.ABuDeprecated import AbuDeprecated
# noinspection PyUnresolvedReferences
from ..CoreBu.ABuFixes import xrange, range, filter

"""网络请求（连接10秒，接收60秒）超时时间"""
K_TIME_OUT = (10, 60)


def random_from_list(array):
    """从参数array中随机取一个元素"""
    # 在array长度短的情况下，测试比np.random.choice效率要高
    return array[random.randrange(0, len(array))]


@AbuDeprecated('only read old symbol db, miss update!!!')
def query_symbol_sub_market(symbol):
    path = TXApi.K_SYMBOLS_DB
    conn = sqlite.connect(path)
    cur = conn.cursor()
    symbol = symbol.lower()
    query = "select {} from {} where {} like \'{}.%\'".format(TXApi.K_DB_TABLE_SN, TXApi.K_DB_TABLE_NAME,
                                                              TXApi.K_DB_TABLE_SN, symbol)
    cur.execute(query)
    results = cur.fetchall()
    conn.close()
    sub_market = ''
    if results is not None and len(results) > 0:
        try:
            if results[0][0].find('.') > 0:
                sub_market = '.' + results[0][0].split('.')[1].upper()
        except:
            logging.info(results)
    return sub_market


@catch_error(return_val=None, log=False)
def query_symbol_from_pinyin(pinyin):
    """通过拼音对symbol进行模糊查询"""
    path = TXApi.K_SYMBOLS_DB
    conn = sqlite.connect(path)
    cur = conn.cursor()
    pinyin = pinyin.lower()
    query = "select stockCode from {} where pinyin=\'{}\'".format(TXApi.K_DB_TABLE_NAME, pinyin)
    cur.execute(query)
    results = cur.fetchall()
    conn.close()
    if len(results) > 0:
        code = results[0][0]
        # 查询到的stcok code eg：sh111111，usabcd.n
        start = 2
        end = len(code)
        if '.' in code:
            # 如果是美股要截取.
            end = code.find('.')
        return code[start:end]


class AkShareApi(StockBaseMarket, SupportMixin):
    def __init__(self, symbol):
        """
        :param symbol: Symbol类型对象
        """
        super(AkShareApi, self).__init__(symbol)
        # 设置数据源解析对象类
        self.data_parser_cls = AkShareParser

    def minute(self, *args, **kwargs):
        pass

    def kline(self, n_folds=2, start=None, end=None, period=None):
        """

        Parameters
        ----------
        n_folds
        start
        end
        period: {'daily', 'weekly', 'monthly'}

        Returns
        -------

        """
        symbol = self._symbol.symbol_code
        period = 'daily' if period is None else period
        stock_df = None
        kl_pd = None
        if self._symbol.market == EMarketTargetType.E_MARKET_TARGET_US:
            stock_df = ak.stock_us_daily(symbol=symbol)
            days = ABuEnv.g_market_trade_year * n_folds + 1
            stock_df = stock_df[-days:]

        elif self._symbol.market == EMarketTargetType.E_MARKET_TARGET_CN:
            stock_df = ak.stock_zh_a_hist(symbol=symbol, period=period, start_date=start, adjust="")
            # stock_df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="20210301", adjust="")
        elif self._symbol.market == EMarketTargetType.E_MARKET_TARGET_HK:
            stock_df = ak.stock_hk_hist(symbol=symbol, period=period, start_date=start, end_date=end)

        if stock_df is not None:
            kl_pd = self.data_parser_cls(self._symbol, stock_df).df

        return StockBaseMarket._fix_kline_pd(kl_pd, n_folds, start, end)


class TXApi(StockBaseMarket, SupportMixin):
    """tx数据源，支持港股，美股，a股"""

    K_NET_BASE = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?p=1&param=%s,day,,,%d," \
                 "qfq&_appName=android&_dev=%s&_devId=%s&_mid=%s&_md5mid=%s&_appver=4.2.2&_ifChId=303&_screenW=%d" \
                 "&_screenH=%d&_osVer=%s&_uin=10000&_wxuin=20000&__random_suffix=%d"

    K_NET_HK_MNY = 'http://proxy.finance.qq.com/ifzqgtimg/stock/corp/hkmoney/sumary?' \
                   'symbol=%s&type=sum&jianjie=1&_appName=android' \
                   '&_dev=%s&_devId=%s&_mid=%s&_md5mid=%s&_appver=5.5.0&_ifChId=277' \
                   '&_screenW=%d&_screenH=%d&_osVer=%s&_uin=10000&_wxuin=20000&_net=WIFI&__random_suffix=%d'

    K_DB_TABLE_NAME = "values_table"
    K_DB_TABLE_SN = "stockCode"
    p_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir))
    K_SYMBOLS_DB = os.path.join(p_dir, 'RomDataBu/symbols_db.db')

    def __init__(self, symbol):
        """
        :param symbol: Symbol类型对象
        """
        super(TXApi, self).__init__(symbol)
        # 设置数据源解析对象类
        self.data_parser_cls = TXParser

    def kline(self, n_folds=2, start=None, end=None, period=None):
        """日k线接口"""
        cuid = ABuStrUtil.create_random_with_num_low(40)
        cuid_md5 = ABuMd5.md5_from_binary(cuid)
        random_suffix = ABuStrUtil.create_random_with_num(5)
        dev_mod = random_from_list(StockBaseMarket.K_DEV_MODE_LIST)
        os_ver = random_from_list(StockBaseMarket.K_OS_VERSION_LIST)
        screen = random_from_list(StockBaseMarket.K_PHONE_SCREEN)

        days = ABuEnv.g_market_trade_year * n_folds + 1
        # start 不为空时计算 获取天数，获取的数据肯定比预期的数据多，因为同一时间内，交易日的天数一定不比实际的天数多
        if start:
            temp_end = ABuDateUtil.current_str_date()
            days = ABuDateUtil.diff(start, temp_end, check_order=False)

        sub_market = None
        if self._symbol.market == EMarketTargetType.E_MARKET_TARGET_US:
            # sub_market = self.query_symbol_sub_market(self._symbol.value)
            market = self._symbol.market.value
            if '.' in self._symbol.value:
                # 如果已经有.了说明是大盘，大盘不需要子市场，eg：us.IXIC
                sub_market = ''
            else:
                # 这里tx的source不支持US_PINK, US_OTC, US_PREIPO
                sub_market_map = {EMarketSubType.US_N.value: 'n',

                                  EMarketSubType.US_PINK.value: 'n',
                                  EMarketSubType.US_OTC.value: 'n',
                                  EMarketSubType.US_PREIPO.value: 'n',
                                  EMarketSubType.US_AMEX.value: 'n',

                                  EMarketSubType.US_OQ.value: 'oq'}
                sub_market = '.{}'.format(sub_market_map[self._symbol.sub_market.value])
            url = TXApi.K_NET_BASE % (
                self._symbol.value + sub_market, days,
                dev_mod, cuid, cuid, cuid_md5, screen[0], screen[1], os_ver, int(random_suffix, 10))
        elif self._symbol.market == EMarketTargetType.E_MARKET_TARGET_HK:
            market = self._symbol.market.value
            url = TXApi.K_NET_BASE % (
                self._symbol.value, days,
                dev_mod, cuid, cuid, cuid_md5, screen[0], screen[1], os_ver, int(random_suffix, 10))
        else:
            market = ''
            url = TXApi.K_NET_BASE % (
                self._symbol.value, days,
                dev_mod, cuid, cuid, cuid_md5, screen[0], screen[1], os_ver, int(random_suffix, 10))

        data = ABuNetWork.get(url, timeout=K_TIME_OUT)
        if data is not None:
            kl_pd = self.data_parser_cls(self._symbol, sub_market, data.json()).df
        else:
            return None

        return StockBaseMarket._fix_kline_pd(kl_pd, n_folds, start, end)

    def hkmoney(self):
        """港股概要信息接口"""
        if self._symbol.market != EMarketTargetType.E_MARKET_TARGET_HK:
            raise TypeError('hkmoney only support hk!!')

        cuid = ABuStrUtil.create_random_with_num_low(40)
        cuid_md5 = ABuMd5.md5_from_binary(cuid)
        random_suffix = ABuStrUtil.create_random_with_num(5)
        dev_mod = random_from_list(StockBaseMarket.K_DEV_MODE_LIST)
        os_ver = random_from_list(StockBaseMarket.K_OS_VERSION_LIST)
        screen = random_from_list(StockBaseMarket.K_PHONE_SCREEN)

        url = TXApi.K_NET_HK_MNY % (self._symbol.value, dev_mod, cuid, cuid, cuid_md5, screen[0], screen[1], os_ver,
                                    int(random_suffix, 10))
        return ABuNetWork.get(url, timeout=K_TIME_OUT)

    def minute(self, n_fold=5, *args, **kwargs):
        """分钟k线接口"""
        raise NotImplementedError('TXApi minute NotImplementedError!')


class NTApi(StockBaseMarket, SupportMixin):
    """nt数据源，支持港股，美股，a股"""

    K_NET_BASE = "http://img1.money.126.net/data/%s/kline/day/history/%d/%s.json"

    def __init__(self, symbol):
        """
        :param symbol: Symbol类型对象
        """
        super(NTApi, self).__init__(symbol)
        # 设置数据源解析对象类
        self.data_parser_cls = NTParser

    def kline(self, n_folds=2, start=None, end=None, period=None):
        """日k线接口"""
        kl_df = None
        if start is None or end is None:
            end_year = int(ABuDateUtil.current_str_date()[:4])
            start_year = end_year - n_folds + 1
        else:
            start_year = int(start[:4])
            end_year = int(end[:4])
        req_year = list(range(start_year, end_year + 1))

        if self._symbol.market == EMarketTargetType.E_MARKET_TARGET_US:
            market = self._symbol.market.value
            symbol = self._symbol.symbol_code.upper()
            if self._symbol.is_us_index():
                # ntes 需要做映射匹配大盘symbol
                index_dict = {'.DJI': 'DOWJONES', '.IXIC': 'NASDAQ', '.INX': 'SP500'}
                symbol = index_dict[symbol]
        elif self._symbol.market == EMarketTargetType.E_MARKET_TARGET_HK:
            market = self._symbol.market.value
            symbol = self._symbol.symbol_code.upper()
        elif self._symbol.market == EMarketTargetType.E_MARKET_TARGET_CN:
            market = self._symbol.market.value
            symbol = self._symbol.symbol_code
            if self._symbol.is_sz_stock():
                symbol = '1{}'.format(symbol)
            else:
                symbol = '0{}'.format(symbol)
        else:
            raise TypeError('NTApi dt support {}'.format(self._symbol.market))

        for year in req_year:
            url = NTApi.K_NET_BASE % (market, year, symbol)
            data = ABuNetWork.get(url=url, retry=1, timeout=K_TIME_OUT)
            temp_df = None
            if data is not None:
                temp_df = self.data_parser_cls(self._symbol, data.json()).df
            if temp_df is not None:
                kl_df = temp_df if kl_df is None else kl_df.append(temp_df)
        if kl_df is None:
            return None
        return StockBaseMarket._fix_kline_pd(kl_df, n_folds, start, end)

    def minute(self, n_fold=5, *args, **kwargs):
        """分钟k线接口"""
        raise NotImplementedError('NTApi minute NotImplementedError!')


class SNUSApi(StockBaseMarket, SupportMixin):
    """snus数据源，支持美股"""
    K_NET_BASE = "http://stock.finance.sina.com.cn/usstock/api/json_v2.php/US_MinKService.getDailyK?" \
                 "symbol=%s&___qn=3n"

    def __init__(self, symbol):
        """
        :param symbol: Symbol类型对象
        """
        super(SNUSApi, self).__init__(symbol)
        # 设置数据源解析对象类
        self.data_parser_cls = SNUSParser

    def _support_market(self):
        """声明数据源支持美股"""
        return [EMarketTargetType.E_MARKET_TARGET_US]

    def kline(self, n_folds=2, start=None, end=None, period=None):
        """日k线接口"""
        url = SNUSApi.K_NET_BASE % self._symbol.symbol_code
        data = ABuNetWork.get(url=url, timeout=K_TIME_OUT).json()
        kl_df = self.data_parser_cls(self._symbol, data).df
        if kl_df is None:
            return None
        return StockBaseMarket._fix_kline_pd(kl_df, n_folds, start, end)

    def minute(self, n_fold=5, *args, **kwargs):
        """分钟k线接口"""
        raise NotImplementedError('SNUSApi minute NotImplementedError!')


class SNFuturesApi(FuturesBaseMarket, SupportMixin):
    """sn futures数据源，支持国内期货"""

    K_NET_BASE = "http://stock.finance.sina.com.cn/futures/api/json_v2.php/" \
                 "IndexService.getInnerFuturesDailyKLine?symbol=%s"

    def __init__(self, symbol):
        """
        :param symbol: Symbol类型对象
        """
        super(SNFuturesApi, self).__init__(symbol)
        # 设置数据源解析对象类
        self.data_parser_cls = SNFuturesParser

    def _support_market(self):
        """声明数据源支持期货数据"""
        return [EMarketTargetType.E_MARKET_TARGET_FUTURES_CN]

    def kline(self, n_folds=2, start=None, end=None, period=None):
        """日k线接口"""
        url = SNFuturesApi.K_NET_BASE % self._symbol.symbol_code
        data = ABuNetWork.get(url=url, timeout=K_TIME_OUT).json()
        kl_df = self.data_parser_cls(self._symbol, data).df
        if kl_df is None:
            return None
        return FuturesBaseMarket._fix_kline_pd(kl_df, n_folds, start, end)


class SNFuturesGBApi(FuturesBaseMarket, SupportMixin):
    """sn futures数据源，支持国际期货"""

    K_NET_BASE = "http://stock2.finance.sina.com.cn/futures/api/jsonp.php/" \
                 "var %s%s=/GlobalFuturesService.getGlobalFuturesDailyKLine?symbol=%s&_=%s"

    def __init__(self, symbol):
        """
        :param symbol: Symbol类型对象
        """
        super(SNFuturesGBApi, self).__init__(symbol)
        # 设置数据源解析对象类
        self.data_parser_cls = SNFuturesGBParser

    def _support_market(self):
        """声明数据源支持期货数据, 支持国际期货市场"""
        return [EMarketTargetType.E_MARKET_TARGET_FUTURES_GLOBAL]

    def kline(self, n_folds=2, start=None, end=None, period=None):
        """日k线接口"""
        today = ABuDateUtil.current_str_date().replace('-', '_')
        url = SNFuturesGBApi.K_NET_BASE % (self._symbol.symbol_code, today, self._symbol.symbol_code, today)
        data = ABuNetWork.get(url=url, timeout=(10, 60))
        text = data.text
        # 返回的是Javascript字符串解析出dict
        js_dict = ABuNetWork.parse_js(text[text.find('=(') + 2:text.rfind(')')])
        kl_df = self.data_parser_cls(self._symbol, js_dict).df
        if kl_df is None:
            return None
        return FuturesBaseMarket._fix_kline_pd(kl_df, n_folds, start, end)


class BNApi(TCBaseMarket, SupportMixin):
    """binance数据源，支持币类，比特币，莱特币"""

    K_NET_BASE = 'https://api.binance.com/api/v3/klines?symbol=%s&interval=%s&limit=1000'

    def __init__(self, symbol):
        """
        :param symbol: Symbol类型对象
        """
        super(BNApi, self).__init__(symbol)
        # 设置数据源解析对象类
        self.data_parser_cls = BNTCParser

    def _support_market(self):
        """只支持币类市场"""
        return [EMarketTargetType.E_MARKET_TARGET_TC]

    def kline(self, start=None, end=None, n_folds=None, period=None):
        symbol = self._symbol.symbol_code.upper().replace('/', '')
        period = '4H' if period is None else period
        url = BNApi.K_NET_BASE % (symbol, period)
        if start is not None:
            url += '&startTime=' + str(start)
        if end is not None:
            url += '&endTime=' + str(end)

        data = json.loads(ABuNetWork.get(url=url, timeout=K_TIME_OUT).text)
        kl_df = self.data_parser_cls(self._symbol, data).df
        if kl_df is None:
            return None
        return TCBaseMarket._fix_kline_pd(kl_df, 2, start, end)

    def minute(self, *args, **kwargs):
        """分钟k线接口"""
        raise NotImplementedError('BNApi minute NotImplementedError!')
