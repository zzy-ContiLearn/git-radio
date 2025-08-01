import os
import requests
import pyttsx3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import openai
from bs4 import BeautifulSoup

# 加载环境变量
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


# 初始化语音引擎
def init_tts_engine():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)  # 语速150%
    engine.setProperty('volume', 0.9)  # 音量90%
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  # 选择女声
    return engine


# 获取关注的仓库列表
def get_watched_repos():
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get('https://api.github.com/user/subscriptions', headers=headers)
    return response.json() if response.status_code == 200 else []


# 获取仓库昨日事件
def get_repo_events(owner, repo):
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    url = f'https://api.github.com/repos/{owner}/{repo}/events'
    events = requests.get(url, headers=headers).json()

    return [e for e in events if e['created_at'].startswith(yesterday)]


# 获取GitHub Trending仓库
def get_trending_repos():
    try:
        response = requests.get('https://github.com/trending?since=daily')
        soup = BeautifulSoup(response.text, 'html.parser')

        trending_repos = []
        for article in soup.select('article.Box-row'):
            title = article.select_one('h2.h3').text.strip().replace('\n', '').replace(' ', '')
            description = article.select_one('p').text.strip() if article.select_one('p') else ''
            stars = article.select('a.Link--muted')[0].text.strip()

            trending_repos.append({
                'name': title,
                'description': description,
                'stars': stars
            })
            if len(trending_repos) >= 10:  # 限制10个结果
                break

        return trending_repos
    except Exception as e:
        print(f"Error fetching trending: {e}")
        return []


# 使用GPT摘要信息
def summarize_with_gpt(watched_events, trending_repos):
    openai.api_key = OPENAI_API_KEY

    prompt = "请总结以下GitHub昨日动态：\n"
    prompt += "## 关注仓库动态 ##\n"

    if not watched_events:
        prompt += "无重要事件\n"
    else:
        for event in watched_events:
            repo_name = event['repo']['name']
            event_type = event['type']
            actor = event['actor']['login']
            created_at = event['created_at']

            prompt += f"- 仓库 {repo_name}: {actor} 进行了 {event_type} 操作 (时间: {created_at})\n"

    prompt += "\n## 昨日热门仓库 ##\n"
    for repo in trending_repos:
        prompt += f"- {repo['name']}: {repo['description']} (星标: {repo['stars']})\n"

    prompt += "\n请用简洁的口语化中文总结要点，突出重要事件和热门项目，限150字以内"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"GPT错误: {e}")
        return "无法生成摘要，请检查API设置"


# 主程序
def main():
    # 初始化语音引擎
    tts_engine = init_tts_engine()

    # 获取关注仓库
    print("获取关注仓库...")
    repos = get_watched_repos()
    print(f"找到 {len(repos)} 个关注仓库")

    # 收集昨日事件
    watched_events = []
    for repo in repos[:5]:  # 限制检查5个仓库
        owner, repo_name = repo['full_name'].split('/')
        print(f"检查 {owner}/{repo_name}...")
        events = get_repo_events(owner, repo_name)
        if events:
            watched_events.extend(events)
        time.sleep(1)  # 避免触发速率限制

    # 获取Trending仓库
    print("获取GitHub Trending...")
    trending_repos = get_trending_repos()

    # 生成摘要
    print("生成摘要...")
    summary = summarize_with_gpt(watched_events, trending_repos)
    print("\n摘要内容：")
    print(summary)

    # 语音播报
    print("\n语音播报中...")
    tts_engine.say(summary)
    tts_engine.runAndWait()


if __name__ == "__main__":
    main()