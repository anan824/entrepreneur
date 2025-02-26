import akshare as ak
import pandas as pd
from datetime import datetime

def get_growth_enterprise_market():
    """获取创业板股票数据"""
    try:
        # 获取创业板股票实时行情
        stock_df = ak.stock_zh_a_spot_em()
        
        # 筛选创业板股票（代码以300开头）
        growth_stocks = stock_df[stock_df['代码'].str.startswith('300')]
        
        # 重命名列，使其更易理解
        selected_columns = {
            '代码': 'stock_code',
            '名称': 'stock_name',
            '最新价': 'current_price',
            '涨跌幅': 'change_percent',
            '成交量': 'volume',
            '成交额': 'turnover',
            '振幅': 'amplitude',
            '最高': 'high',
            '最低': 'low',
            '今开': 'open',
            '昨收': 'prev_close'
        }
        
        result = growth_stocks[selected_columns.keys()].rename(columns=selected_columns)
        
        # 保存数据到CSV文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'growth_stocks_{timestamp}.csv'
        result.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f'数据已保存到文件: {filename}')
        
        return result
        
    except Exception as e:
        print(f"获取数据时发生错误: {str(e)}")
        return None

if __name__ == "__main__":
    print("正在获取创业板数据...")
    df = get_growth_enterprise_market()
    
    if df is not None:
        print("\n数据统计:")
        print(f"总共获取到 {len(df)} 只创业板股票")
        
        # 显示涨跌幅排名前10的股票
        print("\n涨幅榜 TOP 10:")
        print(df.nlargest(10, 'change_percent')[['stock_code', 'stock_name', 'current_price', 'change_percent']])
        
        # 显示涨跌幅后10的股票
        print("\n跌幅榜 TOP 10:")
        print(df.nsmallest(10, 'change_percent')[['stock_code', 'stock_name', 'current_price', 'change_percent']])