import React, { useState, useEffect } from 'react';
import { Table, message } from 'antd';
import axios from 'axios';

const StockTable = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  const formatAmount = (value) => {
    if (value >= 100000000) {
      return `${(value / 100000000).toFixed(2)}亿`;
    }
    return `${(value / 10000).toFixed(2)}万`;
  };

  const columns = [
    {
      title: '代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
    },
    {
      title: '名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 100,
    },
    {
      title: '最新价',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 90,
      render: (value) => value.toFixed(2),
    },
    {
      title: '涨跌幅',
      dataIndex: 'change_percent',
      key: 'change_percent',
      width: 90,
      render: (value) => (
        <span style={{ color: value > 0 ? '#f5222d' : value < 0 ? '#52c41a' : 'inherit' }}>
          {value > 0 ? '+' : ''}{value.toFixed(2)}%
        </span>
      ),
      sorter: (a, b) => a.change_percent - b.change_percent,
    },
    {
      title: '涨速',
      dataIndex: 'speed',
      key: 'speed',
      width: 80,
      render: (value = 0) => (
        <span style={{ color: value > 0 ? '#f5222d' : value < 0 ? '#52c41a' : 'inherit' }}>
          {value > 0 ? '+' : ''}{value.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '5分钟涨跌',
      dataIndex: 'five_min_change',
      key: 'five_min_change',
      width: 100,
      render: (value = 0) => (
        <span style={{ color: value > 0 ? '#f5222d' : value < 0 ? '#52c41a' : 'inherit' }}>
          {value > 0 ? '+' : ''}{value.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '成交量',
      dataIndex: 'volume',
      key: 'volume',
      render: (value) => formatAmount(value),
    },
    {
      title: '成交额',
      dataIndex: 'turnover',
      key: 'turnover',
      render: (value) => formatAmount(value),
    },
  ];

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await axios.get('http://localhost:8000/api/stocks/all');
        setData(response.data);
      } catch (error) {
        console.error('获取数据失败:', error);
        message.error('连接服务器失败，请确保后端服务已启动');
      }
      setLoading(false);
    };

    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: '0 24px', margin: '20px 0' }}>
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="stock_code"
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showQuickJumper: true,
        }}
        bordered
        size="middle"
        scroll={{ x: true }}
      />
    </div>
  );
};

export default StockTable;