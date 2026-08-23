"""
news_aggregator - 新闻聚合器

RSS 新闻抓取 + AI 摘要生成

功能:
  - RSS 源抓取
  - AI 智能摘要
  - 分类聚合
  - 每日简报生成
  - 多源新闻去重
"""

import os
import time
import json
import logging
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger(__name__)

# RSS 依赖
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class NewsAggregator:
    """
    新闻聚合器 - RSS 抓取 + AI 摘要
    """
    
    DEFAULT_FEEDS = {
        # ==================== 科技 ====================
        "tech": [
            # 国际科技
            "https://feeds.feedburner.com/TechCrunch",
            "https://www.theverge.com/rss/index.xml",
            "https://hnrss.org/frontpage",
            "https://www.wired.com/feed/rss",
            "https://arstechnica.com/feed/",
            "https://techcrunch.com/feed/",
            "https://www.engadget.com/rss.xml",
            "https://www.cnet.com/rss/news/",
            "https://www.zdnet.com/news/rss.xml",
            "https://www.theguardian.com/uk/technology/rss",
            # 中国科技
            "https://rsshub.app/ithome/1",
            "https://rsshub.app/36kr/newsflashes",
            "https://rsshub.app/sspai/series",
            "https://rsshub.app/geekbang/news",
            "https://rsshub.app/pingcn/1",
            "https://rsshub.app/huxiu/index",
            "https://rsshub.app/ifanr/latest",
            # 日本科技
            "https://rsshub.app/nikkei/news/tech",
            "https://rsshub.app/ascii/1",
            "https://rsshub.app/itmedia/news",
            # 韩国科技
            "https://rsshub.app/zdnetkorea/news",
            "https://rsshub.app/etnews/1",
        ],
        
        # ==================== 经济/财经 ====================
        "business": [
            # 国际财经
            "https://www.bloomberg.com/feed/podcast",
            "https://www.ft.com/?format=rss",
            "https://www.wsj.com/xml/rss/3_7085.xml",
            "https://www.economist.com/feeds/print-sections/77/finance-and-economics.xml",
            "https://www.reuters.com/business/rss",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://www.marketwatch.com/rss/topstories",
            "https://www.barrons.com/feed",
            # 中国财经
            "https://rsshub.app/zaobao/finance",
            "https://rsshub.app/caijing/1",
            "https://rsshub.app/jrj/news",
            "https://rsshub.app/eastmoney/1",
            "https://rsshub.app/yicai/news",
            # 日本财经
            "https://rsshub.app/nikkei/news/business",
            "https://rsshub.app/jp.reuters/business",
            # 韩国财经
            "https://rsshub.app/koreatimes/business",
            "https://rsshub.app/youthdaily/economic",
        ],
        
        # ==================== 国际新闻 ====================
        "world": [
            # 国际综合
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://www.npr.org/rss/rss.php?id=1001",
            "https://feeds.reuters.com/reuters/worldNews",
            "https://apnews.com/world-news.rss",
            "https://www.aljazeera.com/xml/rss.xml",
            "https://www.dw.com/en/rss.xml",
            "https://www.france24.com/en/rss",
            # 中国新闻
            "https://rsshub.app/zaobao/realtime/china",
            "https://rsshub.app/xinhuanet/1",
            "https://rsshub.app/people/1",
            # 美国新闻
            "https://rsshub.app/nytimes/world",
            "https://rsshub.app/washingtonpost/world",
            "https://rsshub.app/usatoday/news",
            # 日本新闻
            "https://rsshub.app/nikkei/news",
            "https://rsshub.app/nhk/news",
            "https://rsshub.app/yomiuri/1",
            # 韩国新闻
            "https://rsshub.app/yonhap/news",
            "https://rsshub.app/hani/1",
            "https://rsshub.app/koreaherald/news",
        ],
        
        # ==================== 中国 ====================
        "china": [
            "https://rsshub.app/zaobao/realtime/china",
            "https://rsshub.app/ithome/1",
            "https://rsshub.app/36kr/newsflashes",
            "https://rsshub.app/sspai/series",
            "https://rsshub.app/geekbang/news",
            "https://rsshub.app/pingcn/1",
            "https://rsshub.app/huxiu/index",
            "https://rsshub.app/ifanr/latest",
            "https://rsshub.app/zaobao/finance",
            "https://rsshub.app/caijing/1",
            "https://rsshub.app/xinhuanet/1",
            "https://rsshub.app/people/1",
        ],
        
        # ==================== 美国 ====================
        "usa": [
            "https://feeds.feedburner.com/TechCrunch",
            "https://www.theverge.com/rss/index.xml",
            "https://www.wired.com/feed/rss",
            "https://www.wsj.com/xml/rss/3_7085.xml",
            "https://www.bloomberg.com/feed/podcast",
            "https://www.npr.org/rss/rss.php?id=1001",
            "https://www.cnet.com/rss/news/",
            "https://www.zdnet.com/news/rss.xml",
            "https://apnews.com/world-news.rss",
            "https://rsshub.app/nytimes/world",
            "https://rsshub.app/washingtonpost/world",
            "https://rsshub.app/usatoday/news",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://www.marketwatch.com/rss/topstories",
        ],
        
        # ==================== 日本 ====================
        "japan": [
            "https://rsshub.app/nikkei/news/tech",
            "https://rsshub.app/nikkei/news/business",
            "https://rsshub.app/nikkei/news",
            "https://rsshub.app/nhk/news",
            "https://rsshub.app/yomiuri/1",
            "https://rsshub.app/ascii/1",
            "https://rsshub.app/itmedia/news",
            "https://rsshub.app/jp.reuters/business",
        ],
        
        # ==================== 韩国 ====================
        "korea": [
            "https://rsshub.app/zdnetkorea/news",
            "https://rsshub.app/etnews/1",
            "https://rsshub.app/koreatimes/business",
            "https://rsshub.app/yonhap/news",
            "https://rsshub.app/hani/1",
            "https://rsshub.app/koreaherald/news",
        ],
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "news_aggregator"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        
        if not FEEDPARSER_AVAILABLE:
            logger.warning("feedparser 未安装，请运行: pip install feedparser")
        
        logger.info("新闻聚合器 初始化完成")
    
    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def _setup_config(self):
        defaults = {
            "output_dir": "./skills/news_aggregator/output",
            "top_n": 10,
            "summary_length": 150,
            "cache_ttl": 1800,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        
        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)
    
    def _validate_inputs(self, **kwargs) -> bool:
        sources = kwargs.get("sources")
        category = kwargs.get("category")
        if not sources and not category:
            raise ValueError("请指定 sources 或 category 参数")
        return True
    
    def _load_feeds(self, category: str = None, sources: str = None) -> List[str]:
        """加载 RSS 源"""
        feeds = []
        
        if category and category in self.DEFAULT_FEEDS:
            return self.DEFAULT_FEEDS[category]
        
        if sources:
            source_list = [s.strip() for s in sources.split(',')]
            for feed_list in self.DEFAULT_FEEDS.values():
                for feed in feed_list:
                    for src in source_list:
                        if src.lower() in feed.lower():
                            feeds.append(feed)
            return feeds
        
        for feed_list in self.DEFAULT_FEEDS.values():
            feeds.extend(feed_list)
        return feeds
    
    def _fetch_feed(self, feed_url: str) -> List[Dict]:
        """抓取单个 RSS 源"""
        try:
            if not FEEDPARSER_AVAILABLE:
                return []
            
            feed = feedparser.parse(feed_url)
            items = []
            
            for entry in feed.entries[:20]:
                summary = entry.get("summary", "")
                if summary:
                    summary = re.sub(r'<[^>]+>', '', summary)
                    summary = summary[:300]
                
                published = entry.get("published") or entry.get("updated", "")
                author = entry.get("author", "")
                
                items.append({
                    "title": entry.get("title", "无标题"),
                    "link": entry.get("link", ""),
                    "summary": summary or "无摘要",
                    "published": published,
                    "author": author or "未知",
                    "source": feed.feed.get("title", feed_url.split("/")[2] if "//" in feed_url else "未知"),
                    "feed_url": feed_url,
                })
            
            return items
            
        except Exception as e:
            logger.warning(f"抓取 {feed_url} 失败: {e}")
            return []
    
    def _fetch_all_feeds(self, feeds: List[str]) -> List[Dict]:
        """抓取所有 RSS 源"""
        all_items = []
        for feed_url in feeds:
            items = self._fetch_feed(feed_url)
            all_items.extend(items)
        return all_items
    
    def _deduplicate(self, items: List[Dict]) -> List[Dict]:
        """去重"""
        seen = set()
        unique = []
        for item in items:
            key = item.get("title", "")[:30].lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
    
    def _generate_ai_summary(self, articles: List[Dict]) -> str:
        """使用 Ollama 生成 AI 摘要"""
        if not articles:
            return "暂无新闻"
        
        try:
            import requests
            
            news_text = ""
            for i, article in enumerate(articles[:10]):
                news_text += f"{i+1}. {article['title']}\n"
                news_text += f"   {article['summary'][:150]}\n"
                news_text += f"   来源: {article['source']}\n\n"
            
            prompt = f"""请根据以下新闻内容，生成一份每日新闻简报摘要。

要求：
1. 按类别整理
2. 每类列出最重要的 2-3 条新闻
3. 每条新闻用一句话概括
4. 格式简洁清晰

新闻列表：
{news_text}

请生成每日新闻简报："""

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "生成摘要失败")
            else:
                return f"AI 服务异常: {response.status_code}"
                
        except Exception as e:
            logger.warning(f"AI 摘要生成失败: {e}")
            return f"AI 摘要生成失败: {str(e)}"
    
    def _generate_report(self, articles: List[Dict], category: str = None) -> str:
        """生成新闻报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("   📰 每日新闻简报")
        lines.append("=" * 60)
        lines.append(f"   生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if category:
            lines.append(f"   分类: {category}")
        lines.append(f"   新闻数: {len(articles)} 条")
        lines.append("=" * 60)
        lines.append("")
        
        if not articles:
            lines.append("暂无新闻")
            return "\n".join(lines)
        
        # AI 摘要（失败时跳过）
        lines.append("【AI 智能摘要】")
        lines.append("-" * 40)
        try:
            summary = self._generate_ai_summary(articles)
            lines.append(summary)
        except Exception as e:
            logger.warning(f"AI 摘要生成失败，跳过: {e}")
            lines.append("（AI 摘要暂时不可用，请检查 Ollama 服务）")
    
        lines.append("")
        lines.append("-" * 60)
        lines.append("")
        
        # 按来源分组
        sources = {}
        for article in articles:
            source = article.get("source", "未知")
            if source not in sources:
                sources[source] = []
            sources[source].append(article)
        
        for source, items in sorted(sources.items()):
            lines.append(f"📌 {source} ({len(items)} 条)")
            lines.append("-" * 40)
            for item in items[:5]:
                lines.append(f"  • {item.get('title', '无标题')}")
                if item.get('summary'):
                    lines.append(f"    {item['summary'][:120]}...")
                if item.get('link'):
                    lines.append(f"    🔗 {item['link']}")
                lines.append("")
            if len(items) > 5:
                lines.append(f"  ... 还有 {len(items) - 5} 条")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("   简报结束")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _save_report(self, content: str, category: str = None) -> Path:
        """保存报告"""
        output_dir = Path(self.config["output_dir"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"news_{category if category else 'all'}_{timestamp}.txt"
        file_path = output_dir / name
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行新闻聚合"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            self._validate_inputs(**kwargs)
            
            sources = kwargs.get("sources", "")
            category = kwargs.get("category", "")
            top_n = kwargs.get("top_n", self.config.get("top_n", 10))
            
            # 加载 RSS 源
            feeds = self._load_feeds(category, sources)
            logger.info(f"加载 {len(feeds)} 个 RSS 源")
            
            if not feeds:
                return {"status": "error", "error": "未找到 RSS 源"}
            
            # 抓取新闻
            logger.info("抓取新闻...")
            all_items = self._fetch_all_feeds(feeds)
            
            if not all_items:
                return {"status": "error", "error": "未抓取到任何新闻"}
            
            logger.info(f"抓取到 {len(all_items)} 条新闻")
            
            # 去重
            unique_items = self._deduplicate(all_items)
            logger.info(f"去重后 {len(unique_items)} 条")
            
            # 限制数量
            top_n = min(top_n, len(unique_items))
            top_items = unique_items[:top_n]
            
            # 生成报告
            report_content = self._generate_report(top_items, category)
            report_file = self._save_report(report_content, category)
            
            logger.info(f"报告已保存: {report_file}")
            
            return {
                "status": "success",
                "result": {
                    "total_fetched": len(all_items),
                    "unique_count": len(unique_items),
                    "display_count": len(top_items),
                    "feeds_count": len(feeds),
                    "articles": top_items,
                    "report": report_content,
                    "report_file": str(report_file),
                    "category": category or "all",
                    "generated_at": datetime.now().isoformat()
                },
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def __repr__(self):
        return f"<NewsAggregator(name={self.name}, version={self.version})>"