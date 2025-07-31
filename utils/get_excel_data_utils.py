import pandas as pd
import os

def read_excel_data(file_path, sheet_name=0, encoding='utf-8'):
    """
    自动判断文件类型，支持读取Excel（.xls/.xlsx）和CSV（.csv）文件，返回每行数据组成的字典列表。
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    ext = os.path.splitext(file_path)[-1].lower()
    if ext in ['.xls', '.xlsx']:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    elif ext == '.csv':
        df = pd.read_csv(file_path, encoding=encoding)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")
    return df.to_dict(orient='records')

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 可测试csv或excel
    data_path = os.path.join(base_dir, 'caseparams', 'test_http_data.csv')
    datas = read_excel_data(data_path)
    print(datas)