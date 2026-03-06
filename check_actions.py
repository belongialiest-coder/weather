import requests
import json

url = 'https://api.github.com/repos/belongialiest-coder/weather/actions/runs?per_page=3'
try:
    response = requests.get(url, timeout=10)
    data = response.json()

    if 'workflow_runs' in data:
        print("=" * 60)
        print("GitHub Actions 运行状态")
        print("=" * 60)

        for run in data['workflow_runs'][:3]:
            print(f"\n名称: {run['name']}")
            print(f"状态: {run['status']}")
            if run.get('conclusion'):
                print(f"结论: {run['conclusion']}")
            print(f"分支: {run['head_branch']}")
            print(f"提交: {run['head_commit']['message'].split('\n')[0][:60]}")
            print(f"创建时间: {run['created_at']}")
            print(f"链接: {run['html_url']}")
            print("-" * 60)
    else:
        print('获取失败:', data.get('message', 'Unknown error'))
except Exception as e:
    print(f"错误: {e}")
