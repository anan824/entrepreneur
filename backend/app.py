from flask import Flask, jsonify, request
from flask_cors import CORS
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import schedule
import threading
import time

app = Flask(__name__)
CORS(app, supports_credentials=True)

class StockData:
    def __init__(self):
        self.data_cache = {}
        self.last_update = None
        
    def transform_stock_data(self, stock_data):
        # 字段映射关系
        field_mapping = {
            '代码': 'stock_code',
            '名称': 'stock_name',
            '最新价': 'current_price',
            '涨跌幅': 'change_percent',
            '成交量': 'volume',
            '成交额': 'turnover',
            '5日涨跌幅': 'five_day_change'
        }
        
        transformed_data = {}
        for old_key, new_key in field_mapping.items():
            try:
                value = stock_data.get(old_key)
                
                # 处理空值或无效值
                if pd.isna(value) or value == '' or value is None:
                    if new_key in ['change_percent', 'current_price', 'volume', 'turnover']:
                        transformed_data[new_key] = 0.0
                    else:
                        transformed_data[new_key] = ''
                    continue
                    
                # 处理字符串类型的数值
                if isinstance(value, str):
                    value = value.replace('%', '').strip()
                    if value == '':
                        value = '0'
                
                # 转换数值类型
                if new_key in ['change_percent', 'current_price', 'volume', 'turnover']:
                    try:
                        transformed_data[new_key] = float(value)
                    except (ValueError, TypeError):
                        transformed_data[new_key] = 0.0
                else:
                    transformed_data[new_key] = str(value)
                    
            except Exception as e:
                print(f"Error transforming {old_key} to {new_key}: {str(e)}")
                # 设置默认值
                if new_key in ['change_percent', 'current_price', 'volume', 'turnover']:
                    transformed_data[new_key] = 0.0
                else:
                    transformed_data[new_key] = ''
        
        # 确保5日涨跌幅字段存在
        if '5日涨跌幅' in stock_data:
            try:
                value = stock_data['5日涨跌幅']
                if isinstance(value, str):
                    value = value.replace('%', '').strip()
                transformed_data['five_day_change'] = float(value) if value else 0.0
            except (ValueError, TypeError):
                transformed_data['five_day_change'] = 0.0
        else:
            transformed_data['five_day_change'] = 0.0
        
        # 最后检查确保所有数值字段都是有效的浮点数
        for key in ['change_percent', 'current_price', 'volume', 'turnover']:
            if key not in transformed_data or not isinstance(transformed_data[key], (int, float)) or pd.isna(transformed_data[key]):
                transformed_data[key] = 0.0
        
        return transformed_data

    def update_data(self):
        try:
            print("开始更新股票数据...")
            stock_df = ak.stock_zh_a_spot_em()
            
            # 确保数据框不为空
            if stock_df.empty:
                print("警告：获取到的数据为空")
                return
            
            # 转换前打印原始数据示例
            print("原始数据示例：")
            print(stock_df.head())
            
            stock_records = stock_df.to_dict('records')
            transformed_records = []
            
            # 逐条转换数据并进行验证
            for record in stock_records:
                transformed = self.transform_stock_data(record)
                # 验证转换后的数据
                if all(key in transformed for key in ['stock_code', 'stock_name', 'current_price', 'change_percent', 'volume', 'turnover']):
                    transformed_records.append(transformed)
                else:
                    print(f"警告：数据记录格式不完整: {transformed}")
            
            # 筛选创业板股票
            growth_stocks = [
                stock for stock in transformed_records 
                if stock['stock_code'].startswith(('300', '301'))
            ]
            
            # 验证处理后的数据
            print(f"处理后的数据示例：")
            if growth_stocks:
                print(growth_stocks[0])
            
            self.data_cache = {
                'all_stocks': growth_stocks,
                'limit_up': [stock for stock in growth_stocks if stock['change_percent'] >= 9.5],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.last_update = datetime.now()
            
        except Exception as e:
            print(f"更新数据时发生错误: {str(e)}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            raise

stock_data = StockData()

@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "API server is running"})

@app.route('/api/stocks/limit-up')
def get_limit_up():
    if stock_data.last_update is None or \
       datetime.now() - stock_data.last_update > timedelta(minutes=5):
        stock_data.update_data()
    result = stock_data.data_cache.get('limit_up', [])
    print("涨停股票数据：")
    print(f"涨停股票数量: {len(result)}")
    if result:
        print("第一只涨停股票:", result[0])
    return jsonify(result)

@app.route('/api/stocks/all')
def get_all_stocks():
    try:
        if stock_data.last_update is None or \
           datetime.now() - stock_data.last_update > timedelta(minutes=5):
            print("数据需要更新...")
            stock_data.update_data()
        
        result = stock_data.data_cache.get('all_stocks', [])
        
        # 获取查询参数
        search_text = request.args.get('search', '').lower()
        five_day_filter = request.args.get('five_day_filter')
        
        # 应用过滤条件
        if search_text or five_day_filter:
            filtered_result = []
            for stock in result:
                # 文本搜索
                text_match = True
                if search_text:
                    text_match = any(
                        search_text in str(value).lower() 
                        for value in stock.values()
                    )
                
                # 5日涨幅过滤
                five_day_match = True
                if five_day_filter:
                    five_day_change = stock.get('five_day_change', 0)
                    if five_day_filter == 'up10':
                        five_day_match = five_day_change >= 10
                    elif five_day_filter == 'up5':
                        five_day_match = 5 <= five_day_change < 10
                    elif five_day_filter == 'down5':
                        five_day_match = five_day_change <= -5
                
                if text_match and five_day_match:
                    filtered_result.append(stock)
            
            result = filtered_result
        
        print("API返回数据示例：")
        if result:
            print(f"总数据条数: {len(result)}")
            print("第一条数据:", result[0])
        return jsonify(result)
    except Exception as e:
        print(f"处理请求时发生错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/news/<code>')
def get_stock_news(code):
    if stock_data.last_update is None or \
       datetime.now() - stock_data.last_update > timedelta(minutes=5):
        stock_data.update_data()
    return jsonify(stock_data.data_cache.get('news', {}).get(code, []))

@app.route('/api/stocks/ma5-trend')
def get_ma5_trend():
    if stock_data.last_update is None or \
       datetime.now() - stock_data.last_update > timedelta(minutes=5):
        stock_data.update_data()
    return jsonify(stock_data.data_cache.get('ma5_trend', []))

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    # 设置定时更新任务
    schedule.every(5).minutes.do(stock_data.update_data)
    # 启动定时任务线程
    threading.Thread(target=run_schedule, daemon=True).start()
    # 启动初始数据更新
    stock_data.update_data()
    # 启动Flask服务，改用8000端口
    app.run(debug=True, port=8000)