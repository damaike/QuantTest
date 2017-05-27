# -*- coding: utf-8 -*-

import datetime
import math
import os

KEY_TOTAL_INVEST = 'total_invest'
KEY_MARKET_VALUE = 'makret_value'
KEY_TOTAL_PROFIT = 'total_profit'
KEY_PROFIT_RATIO = 'profit_ratio'


DATA_FILE = r"d:\399300.txt"
START_DATE = "2005/1/1"
MAX_PROFIT = 1

RESULT_FILE = r'd:\result.txt'

MONEY_DAY = 10000
LOG_TO_FILE = False
DEBUG = False

# 读取日线数据文件数据文件
# 格式：日期 价格
# sample: 2015/10/21    3.05
def read_price_data():
    price_data = []
    lines = []

    with open(DATA_FILE) as f:
        lines = f.readlines()
        f.close()

    for line in lines:
        items = line.split()
        if len(items) == 2:
            items[0] = string_2_date(items[0])
            items[1] = float(items[1])
            price_data.append(items)

    return price_data


# 字符串转换为日期
def string_2_date(datestr):
    return datetime.datetime.strptime(datestr, '%Y/%m/%d').date()


# 计算能买多少股
# A股必须以手为单位买入，每手100股
def calc_stock_to_buy(money, price):
    stock_to_buy = int(math.floor(money / (price * 100.0))) * 100
    return stock_to_buy


# 获取价格数据
def price_from_data(price_data):
    return price_data[1]


def calc_profit_ratio(market_value, money_spent):
    if money_spent == 0:
        return 0

    profit_ratio = (market_value - money_spent) / float(money_spent)
    if money_spent < 0:
        profit_ratio *= -1

    return profit_ratio



# 获取从从指定日期开始的日线数据
def read_partial_price_data(start_date):
    price_data = read_price_data()

    for index in range(0, len(price_data)):
        if price_data[index][0] >= start_date:
            return price_data[index:]

    return []

# 打印调试信息
def log_debug(log):
    if DEBUG:
        raw_log(log)


def log_info(log):
    raw_log(log)


def raw_log(log):
    if LOG_TO_FILE:
        with open(RESULT_FILE, 'a') as f:
            f.write((log+"\n").encode('utf8'))
    else:
        print log


# 普通定投
def putong_dingtou(start_date):
    price_data = read_partial_price_data(string_2_date(start_date))

    total_invest = 0
    current_invest = 0
    times = 0
    stocks = 0

    for data in price_data:
        price = price_from_data(data)

        # 盈利超过100%全部卖光
        market_value = price * stocks
        if market_value > (current_invest * 2):
            total_invest += current_invest - market_value
            stocks = 0
            current_invest = 0
            print u"{:} ### 盈利超过100%全部卖光".format(data[0])


        log_debug(u"{:}, 市值：{:,}, 持股：{:,}, 价格：{:}".format(data[0], stocks * price, stocks, price))

        stock_to_buy = calc_stock_to_buy(MONEY_DAY, price)

        stocks += stock_to_buy
        current_invest += stock_to_buy * price

        times += 1

    last_price = price_data[-1][1]
    market_value = stocks * last_price

    log_debug("\n*********************\n")

    total_invest += current_invest

    return {
        KEY_TOTAL_INVEST : total_invest,
        KEY_MARKET_VALUE : market_value,
        KEY_TOTAL_PROFIT : market_value - total_invest,
        KEY_PROFIT_RATIO : calc_profit_ratio(market_value, total_invest) * 100.0
    }


# 价值平均定投
def jiazhi_pingjun(start_date):
    price_data = read_partial_price_data(string_2_date(start_date))

    total_investment = 0
    cycle_investment = 0
    total_times = 0
    times = 0
    stocks = 0
    money_per_time = MONEY_DAY

    for data in price_data:
        log_debug(u"市值,\t预期,\t持股,\t价格,\t总投入,\t总利润,\t利润率")

        price = price_from_data(data)

        market_value = stocks * price

        # 如果利润超过最大预期利润，卖光所有
        current_profit = calc_profit_ratio(market_value, cycle_investment)
        if current_profit > MAX_PROFIT:
            total_investment += cycle_investment - stocks * price
            cycle_investment = 0
            stocks = 0
            total_times += times
            times = 0
            market_value = 0

            log_info(u"{:} ######## 全部卖光".format(data[0]))

        wish_value = times * money_per_time
        delta = market_value - wish_value   # 市值和预期差值
        log_debug(u"{:} 市值：{:,.0f}，预期：{:,.0f}，持股：{:,.0f}, 价格：{:}，总投入：{:,.0f}，总利润：{:,.0f}，利润率：{:,.1f}".format(
            data[0], market_value, wish_value, stocks, price,
            total_investment + cycle_investment, market_value - total_investment + cycle_investment, current_profit * 100
        ))

        stock_to_op = 0
        if delta > 0:  #市值比预期高，卖出
            stock_to_op =int(delta / price)
            cycle_investment -= stock_to_op * price
            stocks -= stock_to_op
            log_debug(u"\txx  卖出 %d 股" % stock_to_op)
        elif delta < 0: # 市值比预期低，买入
            stock_to_op = calc_stock_to_buy(delta * -1, price)
            cycle_investment += stock_to_op * price
            stocks += stock_to_op
            log_debug(u"\t买入 %d 股" % stock_to_op)

        times += 1

    last_price = price_data[-1][1]
    market_value = stocks * last_price

    log_debug("\n+++++++++++++++++++++\n")

    total_investment += cycle_investment

    return {
        KEY_TOTAL_INVEST : total_investment,
        KEY_MARKET_VALUE : market_value,
        KEY_TOTAL_PROFIT : market_value - total_investment,
        KEY_PROFIT_RATIO : calc_profit_ratio(market_value, total_investment) * 100.0
    }



def main():
    if LOG_TO_FILE:
        os.remove(RESULT_FILE)

    d = putong_dingtou(START_DATE)
    log_info(u"普通定投：\n开始日期：{:}\n总投入：{:,.0f}\n当前市值：{:,.0f}\n总利润：{:,.0f}\n利润率：{:.1f}%".format(
        START_DATE, d[KEY_TOTAL_INVEST], d[KEY_MARKET_VALUE], d[KEY_TOTAL_PROFIT], d[KEY_PROFIT_RATIO]))

    print ''

    d = jiazhi_pingjun(START_DATE)

    log_info(u"价值平均：\n开始日期：{:}\n总投入：{:,.0f}\n当前市值：{:,.0f}\n总利润：{:,.0f}\n利润率：{:.1f}%".format(
        START_DATE, d[KEY_TOTAL_INVEST], d[KEY_MARKET_VALUE], d[KEY_TOTAL_PROFIT], d[KEY_PROFIT_RATIO]))


main()
