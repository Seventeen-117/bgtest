import os
import pandas as pd

def generate_test_files():
    # 获取项目根目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caseparams_dir = os.path.join(base_dir, 'caseparams')
    testcase_dir = os.path.join(base_dir, 'testcase')

    if not os.path.exists(caseparams_dir):
        raise FileNotFoundError(f"The directory {caseparams_dir} does not exist.")

    for file in os.listdir(caseparams_dir):
        if file.endswith('.xlsx'):
            test_name = file.split('.')[0]
            test_file_content = f"""
import pytest
from common.get_caseparams import read_test_data
from common.request import send_request
from common.assertion import assert_response
from common.config import read_config

config = read_config('conf/interface.ini')
test_data = read_test_data('caseparams/{file}')

@pytest.mark.parametrize("data", test_data)
def test_{test_name}(data):
    url = config['API']['url']
    method = config['API']['method']
    response = send_request(method, url, data)
    assert_response(response['result'], data['expected'])
"""
            with open(os.path.join(testcase_dir, f'test_{test_name}.py'), 'w') as f:
                f.write(test_file_content)

if __name__ == "__main__":
    generate_test_files()