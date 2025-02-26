from flask import Flask, jsonify
from flask_cors import CORS
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import schedule
import threading
import time

app = Flask(__name__)
# 简化 CORS 配置
CORS(app, supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

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
            '成交额': 'turnover'
        }
        
        transformed_data = {}
        for old_key, new_key in field_mapping.items():
            if old_key in stock_data:
                value = stock_data[old_key]
                if new_key == 'change_percent':
                    try:
                        # 直接获取涨跌幅数值，不需要strip
                        value = float(value)
                    except:
                        value = 0
                elif new_key in ['current_price']:
                    try:
                        value = float(value)
                    except:
                        value = 0
                elif new_key in ['volume', 'turnover']:
                    try:
                        value = float(value)
                    except:
                        value = 0
                
                transformed_data[new_key] = value
        
        return transformed_data

    def update_data(self):
        try:
            print("开始更新股票数据...")
            stock_df = ak.stock_zh_a_spot_em()
            stock_records = stock_df.to_dict('records')
            transformed_records = [self.transform_stock_data(record) for record in stock_records]
            
            growth_stocks = [
                stock for stock in transformed_records 
                if stock['stock_code'].startswith(('300', '301'))
            ]
            
            limit_up_stocks = [
                stock for stock in growth_stocks 
                if stock['change_percent'] >= 9.5
            ]
            
            growth_stocks.sort(key=lambda x: x['change_percent'], reverse=True)
            
            self.data_cache = {
                'all_stocks': growth_stocks,
                'limit_up': limit_up_stocks,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.last_update = datetime.now()
            
        except Exception as e:
            print(f"更新数据时发生错误: {str(e)}")
            raise

stock_data = StockData()

@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "API server is running"})

@app.route('/api/stocks/limit-up')  # 修改路由路径
def get_limit_up():
    if stock_data.last_update is None or \
       datetime.now() - stock_data.last_update > timedelta(minutes=5):
        stock_data.update_data()
    return jsonify(stock_data.data_cache.get('limit_up', []))

@app.route('/api/stocks/all')  # 修改路由路径
def get_all_stocks():
    try:
        if stock_data.last_update is None or \
           datetime.now() - stock_data.last_update > timedelta(minutes=5):
            print("数据需要更新...")
            stock_data.update_data()
        
        result = stock_data.data_cache.get('all_stocks', [])
        print(f"返回 {len(result)} 条数据")
        return jsonify(result)
    except Exception as e:
        print(f"处理请求时发生错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/news/<code>')  # 修改路由路径
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