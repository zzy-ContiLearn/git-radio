import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import tempfile
import subprocess
import platform
# 加载环境变量
load_dotenv()

# 通过环境变量控制TTS引擎可用性
MELOTTS_AVAILABLE = os.getenv('MELOTTS_AVAILABLE', 'true').lower() == 'true'
PYTTSX3_AVAILABLE = os.getenv('PYTTSX3_AVAILABLE', 'true').lower() == 'true'

# 根据环境变量配置导入相应的TTS库
if MELOTTS_AVAILABLE:
    try:
        from melo.api import TTS
        print("✅ MeloTTS已启用")
    except ImportError:
        print("⚠️ MeloTTS未安装，但环境变量已启用，将回退到其他TTS")
        MELOTTS_AVAILABLE = False

if PYTTSX3_AVAILABLE:
    try:
        import pyttsx3
        print("✅ pyttsx3已启用")
    except ImportError:
        print("⚠️ pyttsx3未安装，但环境变量已启用")
        PYTTSX3_AVAILABLE = False
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
MODEL_API_KEY = os.getenv('MODEL_API_KEY')
MODEL = os.getenv('MODEL')


# 初始化语音引擎
def init_tts_engine(language='auto'):
    """
    初始化语音引擎 (优先使用MeloTTS，备用pyttsx3)
    :param language: 'zh' for Chinese, 'en' for English, 'auto' for auto-detect
    """
    
    # 优先尝试MeloTTS
    if MELOTTS_AVAILABLE:
        try:
            # Speed is adjustable
            device = 'mps' # or cuda:0 or mps or cpu
            
            # 根据语言选择模型
            if language == 'zh' or language == 'auto':
                try:
                    model = TTS(language='ZH', device=device)
                    speaker_ids = model.hps.data.spk2id
                    print("🎤 使用MeloTTS中文语音")
                    return {'type': 'melotts', 'model': model, 'speaker_ids': speaker_ids, 'language': 'ZH'}        
                except Exception as e:
                    print(f"⚠️ 中文模型加载失败: {e}，尝试英文模型")
            
            # 默认使用英文模型
            model = TTS(language='EN', device=device)
            speaker_ids = model.hps.data.spk2id
            print("🎤 使用MeloTTS英文语音 (美式)")
            return {'type': 'melotts', 'model': model, 'speaker_id': speaker_id, 'language': 'EN'}
            
        except Exception as e:
            print(f"⚠️ MeloTTS初始化失败: {e}，回退到系统TTS")
    
    # 备用方案：使用pyttsx3
    if PYTTSX3_AVAILABLE:
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)  # 语速150%
            engine.setProperty('volume', 0.9)  # 音量90%
            
            # 获取所有可用的语音
            voices = engine.getProperty('voices')
            selected_voice = None
            
            if language == 'zh' or language == 'auto':
                # 寻找中文语音
                for voice in voices:
                    if 'zh' in voice.id.lower() or 'chinese' in voice.name.lower() or 'ting' in voice.name.lower():
                        selected_voice = voice
                        print(f"🎤 使用pyttsx3中文语音: {voice.name}")
                        break
            
            if not selected_voice and (language == 'en' or language == 'auto'):
                # 寻找英语语音
                for voice in voices:
                    if ('en' in voice.id.lower() or 'english' in voice.name.lower() or 
                        'alex' in voice.name.lower() or 'samantha' in voice.name.lower() or
                        'victoria' in voice.name.lower()):
                        selected_voice = voice
                        print(f"🎤 使用pyttsx3英语语音: {voice.name}")
                        break
            
            # 如果没有找到指定语言的语音，使用默认语音
            if not selected_voice:
                if len(voices) > 1:
                    selected_voice = voices[1]
                    print(f"🎤 使用pyttsx3默认语音: {voices[1].name}")
                else:
                    selected_voice = voices[0]
                    print("🎤 使用pyttsx3系统默认语音")
            
            engine.setProperty('voice', selected_voice.id)
            return {'type': 'pyttsx3', 'engine': engine}
            
        except Exception as e:
            print(f"⚠️ pyttsx3初始化失败: {e}")
    
    # 最后的备用方案：使用系统say命令 (仅macOS)
    system = platform.system()
    if system == "Darwin":
        print("🎤 使用macOS系统say命令")
        return {'type': 'system_say'}
    
    raise Exception("❌ 无可用的语音引擎")


# 通用TTS语音播报函数
def speak_with_tts(tts_engine, text, language='auto', speed=1.0):
    """
    使用配置的TTS引擎进行语音播报
    :param tts_engine: TTS引擎字典
    :param text: 要播报的文本
    :param language: 语言
    :param speed: 语速
    """
    try:
        engine_type = tts_engine.get('type', 'melotts')
        
        if engine_type == 'melotts':
            # 使用MeloTTS
            model = tts_engine['model']
            speaker_ids = tts_engine['speaker_ids']
            
            # 处理语言参数，如果是auto则使用引擎的默认语言
            if language == 'auto':
                actual_language = tts_engine.get('language', 'ZH')
            else:
                actual_language = language
            
            # 获取speaker_id，如果找不到则使用第一个可用的
            if actual_language in speaker_ids:
                speaker_id = speaker_ids[actual_language]
            else:
                # 使用第一个可用的speaker
                speaker_id = list(speaker_ids.values())[0]
                print(f"⚠️ 未找到语言 {actual_language} 的speaker，使用默认speaker")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # 生成语音文件
            model.tts_to_file(text, speaker_id, temp_path, speed=speed)
            
            # 播放音频文件
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", temp_path], check=True)
            elif system == "Linux":
                subprocess.run(["aplay", temp_path], check=True)
            elif system == "Windows":
                import winsound
                winsound.PlaySound(temp_path, winsound.SND_FILENAME)
            
            # 清理临时文件
            os.unlink(temp_path)
            
        elif engine_type == 'pyttsx3':
            # 使用pyttsx3
            engine = tts_engine['engine']
            engine.say(text)
            engine.runAndWait()
            
        elif engine_type == 'system_say':
            # 使用系统say命令 (macOS)
            subprocess.run(["say", text], check=True)
            
        else:
            print(f"⚠️ 未知的TTS引擎类型: {engine_type}")
        
    except Exception as e:
        print(f"❌ TTS语音播报失败: {e}")
        raise e


# 获取starred仓库列表
def get_starred_repos() -> List[Dict[str, Any]]:
    """获取用户starred的仓库列表"""
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Git-Radio/1.0'
    }
    try:
        response = requests.get('https://api.github.com/user/starred?per_page=50', headers=headers)
        response.encoding = 'utf-8'  # 确保正确的编码
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            print("❌ GitHub Token无效或已过期，请检查.env文件中的GITHUB_TOKEN")
            return []
        else:
            print(f"获取starred仓库失败: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"获取starred仓库出错: {e}")
        return []


# 获取仓库过去24小时的重要事件
def get_repo_recent_events(owner: str, repo: str) -> List[Dict[str, Any]]:
    """获取仓库过去24小时的重要事件"""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    
    important_events = []
    
    try:
        # 获取events
        events_url = f'https://api.github.com/repos/{owner}/{repo}/events'
        events_response = requests.get(events_url, headers=headers)
        
        if events_response.status_code == 200:
            events = events_response.json()
            for event in events:
                event_time = datetime.fromisoformat(event['created_at'].replace('Z', '+00:00'))
                if event_time >= twenty_four_hours_ago:
                    # 筛选重要事件类型
                    if event['type'] in ['PushEvent', 'PullRequestEvent', 'IssuesEvent', 'ReleaseEvent', 'CreateEvent']:
                        important_events.append(event)
        
        # 获取最新的Pull Requests
        prs_url = f'https://api.github.com/repos/{owner}/{repo}/pulls?state=all&sort=updated&per_page=10'
        prs_response = requests.get(prs_url, headers=headers)
        
        if prs_response.status_code == 200:
            prs = prs_response.json()
            for pr in prs:
                pr_updated = datetime.fromisoformat(pr['updated_at'].replace('Z', '+00:00'))
                if pr_updated >= twenty_four_hours_ago and pr.get('comments', 0) > 5:
                    # 将热门PR作为特殊事件添加
                    important_events.append({
                        'type': 'HotPullRequest',
                        'created_at': pr['updated_at'],
                        'actor': {'login': pr['user']['login']},
                        'repo': {'name': f'{owner}/{repo}'},
                        'payload': {
                            'title': pr['title'],
                            'comments': pr.get('comments', 0),
                            'state': pr['state'],
                            'url': pr['html_url']  # 添加PR的URL
                        }
                    })
        
        return important_events[:10]  # 限制返回数量
        
    except Exception as e:
        print(f"获取 {owner}/{repo} 事件时出错: {e}")
        return []


# 获取GitHub Trending仓库
def get_trending_repos() -> List[Dict[str, Any]]:
    """获取GitHub今日trending仓库"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get('https://github.com/trending?since=daily', headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        trending_repos = []
        for article in soup.select('article.Box-row'):
            try:
                # 获取仓库名称
                title_elem = article.select_one('h2.h3 a')
                if not title_elem:
                    continue
                    
                title = title_elem.get('href').strip('/')
                
                # 获取描述
                desc_elem = article.select_one('p.col-9')
                description = desc_elem.text.strip() if desc_elem else ''
                
                # 获取今日star数
                stars_today_elem = article.select_one('span.d-inline-block.float-sm-right')
                stars_today = stars_today_elem.text.strip() if stars_today_elem else '0'
                
                # 获取总star数
                total_stars_elem = article.select_one('a[href*="/stargazers"]')
                total_stars = total_stars_elem.text.strip() if total_stars_elem else '0'
                
                # 获取编程语言
                lang_elem = article.select_one('span[itemprop="programmingLanguage"]')
                language = lang_elem.text.strip() if lang_elem else 'Unknown'

                trending_repos.append({
                    'name': title,
                    'description': description,
                    'stars_today': stars_today,
                    'total_stars': total_stars,
                    'language': language
                })
                
                if len(trending_repos) >= 10:  # 限制10个结果
                    break
            except Exception as e:
                print(f"解析trending仓库时出错: {e}")
                continue

        return trending_repos
    except Exception as e:
        print(f"获取trending仓库失败: {e}")
        return []

def get_response(client, model, messages) -> str:
    response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=400,
                temperature=0.7
            )
    return response

# 使用GPT摘要信息
def summarize_with_gpt(starred_events: List[Dict[str, Any]], trending_repos: List[Dict[str, Any]]) -> str:
    """使用GPT生成智能摘要"""
    if not MODEL_API_KEY:
        return generate_simple_summary(starred_events, trending_repos)
    
    prompt = "请为我播报今日GitHub动态摘要，用轻松的语调：\n\n"
    
    # 处理starred仓库的重要事件
    if starred_events:
        prompt += "## 你关注的仓库动态 ##\n"
        for event in starred_events[:8]:  # 限制事件数量
            repo_name = event['repo']['name']
            event_type = event['type']
            actor = event['actor']['login']
            
            if event_type == 'HotPullRequest':
                title = event['payload']['title']
                comments = event['payload']['comments']
                pr_url = event['payload'].get('url', '')
                if pr_url:
                    prompt += f"- {repo_name}: 热门PR '{title}' 收到了{comments}条评论\n  URL: {pr_url}\n"
                else:
                    prompt += f"- {repo_name}: 热门PR '{title}' 收到了{comments}条评论\n"
            elif event_type == 'ReleaseEvent':
                prompt += f"- {repo_name}: {actor} 发布了新版本\n"
            elif event_type == 'PullRequestEvent':
                prompt += f"- {repo_name}: {actor} 提交了新的Pull Request\n"
            elif event_type == 'IssuesEvent':
                prompt += f"- {repo_name}: {actor} 创建或更新了Issue\n"
            else:
                prompt += f"- {repo_name}: {actor} 进行了{event_type}操作\n"
    else:
        prompt += "## 你关注的仓库动态 ##\n今日暂无重要更新\n"
    
    # 处理trending仓库
    if trending_repos:
        prompt += "\n## 今日GitHub热门项目 ##\n"
        for repo in trending_repos[:5]:  # 只取前5个
            name = repo['name']
            desc = repo['description'][:50] + '...' if len(repo['description']) > 50 else repo['description']
            stars_today = repo['stars_today']
            language = repo['language']
            prompt += f"- {name} ({language}): {desc} - 今日+{stars_today}⭐\n"
    
    prompt += "\n要求1：读取pr的内容并简单总结\n要求2：总结内容不要带上url\n要求3：总结不要带表情包\n请用自然、口语化的中文总结，就像朋友间的聊天，重点突出有趣的项目和重要更新。对于提供了URL的重要PR，请访问这些URL并总结其中的关键内容和变更。控制在300字以内。"
    
    try:
        from openai import OpenAI
        import os
        # 确保环境变量正确设置
        print(MODEL_API_KEY)
        if not MODEL_API_KEY:
            print("OpenAI API密钥未配置，使用简单摘要")
            return generate_simple_summary(starred_events, trending_repos)
            
        # 设置环境变量以避免编码问题
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        messages=[{"role": "user", "content": prompt}]
        
        if MODEL == "DEEPSEEK":
            client = OpenAI(api_key=MODEL_API_KEY, base_url="https://api.deepseek.com")
            response = get_response(client, "deepseek-chat", messages)    
        elif MODEL == "OPENAI":
            client = OpenAI(api_key=MODEL_API_KEY, )
            response = get_response(client, "gpt-3.5-turbo", messages)
        else:
            print("not supported model type!")

        result = response.choices[0].message.content
        return result.strip() if result else ""
    except Exception as e:
        print(f"GPT摘要生成失败: {e}")
        return generate_simple_summary(starred_events, trending_repos)


# 简单摘要生成（备用方案）
def generate_simple_summary(starred_events: List[Dict[str, Any]], trending_repos: List[Dict[str, Any]]) -> str:
    """生成简单的文本摘要"""
    summary = "今日GitHub动态播报：\n\n"
    
    if starred_events:
        summary += f"你关注的仓库中有{len(starred_events)}个重要更新，"
        hot_prs = [e for e in starred_events if e['type'] == 'HotPullRequest']
        if hot_prs:
            summary += f"其中{len(hot_prs)}个热门PR值得关注。"
    else:
        summary += "你关注的仓库今日较为平静。"
    
    if trending_repos:
        summary += f"\n\nGitHub今日热门项目中，{trending_repos[0]['name']}项目表现突出，"
        summary += f"使用{trending_repos[0]['language']}语言开发。"
        if len(trending_repos) > 1:
            summary += f"另外还有{len(trending_repos)-1}个项目值得关注。"
    print(summary)
    return summary


# 主程序
def main(language='auto'):
    """主程序入口"""
    print("🎵 Git Radio 启动中...")
    
    # 检查必要的环境变量
    if not GITHUB_TOKEN or GITHUB_TOKEN == "您的GitHub个人访问令牌":
        print("❌ 错误: 请在.env文件中设置真实的GITHUB_TOKEN")
        print("💡 获取方法: https://github.com/settings/tokens")
        print("🔧 或者运行演示模式: python3 git_radio.py --demo")
        return
    
    # 初始化语音引擎
    try:
        tts_engine = init_tts_engine(language)
        print("🔊 语音引擎初始化成功")
    except Exception as e:
        print(f"❌ 语音引擎初始化失败: {e}")
        return

    # 获取starred仓库
    print("⭐ 获取你的starred仓库...")
    repos = get_starred_repos()
    print(f"📚 找到 {len(repos)} 个starred仓库")
    
    if not repos:
        print("⚠️  未找到starred仓库，请先在GitHub上star一些项目")
        return

    # 收集过去24小时的重要事件
    print("🔍 分析过去24小时的重要动态...")
    all_events = []
    
    # 只检查最近更新的前10个仓库，避免API限制
    recent_repos = sorted(repos, key=lambda x: x.get('updated_at', ''), reverse=True)[:10]
    
    for i, repo in enumerate(recent_repos):
        owner, repo_name = repo['full_name'].split('/')
        print(f"📊 检查 {owner}/{repo_name} ({i+1}/{len(recent_repos)})")
        
        events = get_repo_recent_events(owner, repo_name)
        
        if events:
            all_events.extend(events)
            print(f"   ✅ 发现 {len(events)} 个重要事件")
        
        # 避免触发GitHub API速率限制
        if i < len(recent_repos) - 1:
            time.sleep(0.5)

    # 获取GitHub Trending仓库
    print("🔥 获取今日GitHub热门项目...")
    trending_repos = get_trending_repos()
    print(f"📈 找到 {len(trending_repos)} 个热门项目")

    # 生成智能摘要
    print("🤖 生成智能摘要...")
    summary = summarize_with_gpt(all_events, trending_repos)
    
    print("\n" + "="*50)
    print("📻 今日Git Radio播报内容:")
    print("="*50)
    print(summary)
    print("="*50)

    # 语音播报
    print("\n🎙️  开始语音播报...")
    try:
        speak_with_tts(tts_engine, summary, language, speed=1.0)
        print("✅ 播报完成！")
    except Exception as e:
        print(f"❌ 语音播报失败: {e}")
    
    print("\n🎵 Git Radio 播报结束，祝你有美好的一天！")


# 演示模式数据
def get_demo_data():
    """获取演示数据"""
    demo_events = [
        {
            'type': 'HotPullRequest',
            'created_at': '2024-01-15T10:30:00Z',
            'actor': {'login': 'developer123'},
            'repo': {'name': 'microsoft/vscode'},
            'payload': {
                'title': 'Add new AI-powered code completion feature',
                'comments': 15,
                'state': 'open',
                'url': 'https://github.com/microsoft/vscode/pull/12345'
            }
        },
        {
            'type': 'ReleaseEvent',
            'created_at': '2024-01-15T09:15:00Z',
            'actor': {'login': 'maintainer'},
            'repo': {'name': 'facebook/react'},
            'payload': {'tag_name': 'v18.3.0'}
        },
        {
            'type': 'PullRequestEvent',
            'created_at': '2024-01-15T08:45:00Z',
            'actor': {'login': 'contributor'},
            'repo': {'name': 'tensorflow/tensorflow'},
            'payload': {'action': 'opened'}
        }
    ]
    
    demo_trending = [
        {
            'name': 'openai/whisper',
            'description': 'Robust Speech Recognition via Large-Scale Weak Supervision',
            'stars_today': '1,234',
            'total_stars': '45,678',
            'language': 'Python'
        },
        {
            'name': 'microsoft/playwright',
            'description': 'Playwright is a framework for Web Testing and Automation',
            'stars_today': '567',
            'total_stars': '23,456',
            'language': 'TypeScript'
        },
        {
            'name': 'vercel/next.js',
            'description': 'The React Framework for the Web',
            'stars_today': '890',
            'total_stars': '78,901',
            'language': 'JavaScript'
        }
    ]
    
    return demo_events, demo_trending


# 演示模式主程序
def demo_mode(language='auto'):
    """演示模式"""
    print("🎵 Git Radio 演示模式启动中...")
    
    # 初始化语音引擎
    try:
        tts_engine = init_tts_engine(language)
        print("🔊 语音引擎初始化成功")
    except Exception as e:
        print(f"❌ 语音引擎初始化失败: {e}")
        return
    
    print("📚 使用演示数据模拟GitHub动态...")
    
    # 获取演示数据
    demo_events, demo_trending = get_demo_data()
    
    print(f"🔍 模拟发现 {len(demo_events)} 个重要事件")
    print(f"🔥 模拟获取 {len(demo_trending)} 个热门项目")
    
    # 生成智能摘要
    print("🤖 生成演示摘要...")
    summary = summarize_with_gpt(demo_events, demo_trending)
    
    print("\n" + "="*50)
    print("📻 Git Radio 演示播报内容:")
    print("="*50)
    print(summary)
    print("="*50)
    
    # 语音播报
    print("\n🎙️  开始语音播报...")
    try:
        speak_with_tts(tts_engine, summary, language, speed=1.0)
        print("✅ 演示播报完成！")
    except Exception as e:
        print(f"❌ 语音播报失败: {e}")
    
    print("\n🎵 Git Radio 演示结束！")
    print("💡 要使用真实数据，请配置GitHub Token后运行: python3 git_radio.py")


if __name__ == "__main__":
    import argparse
    
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='Git Radio - GitHub动态语音播报工具')
    parser.add_argument('--demo', action='store_true', help='运行演示模式')
    parser.add_argument('--lang', choices=['ZH', 'EN', 'auto'], default='auto', 
                       help='语音播报语言: zh(中文), en(英语), auto(自动检测)')
    
    args = parser.parse_args()
    
    # 根据参数运行相应模式
    if args.demo:
        demo_mode(args.lang)
    else:
        main(args.lang)