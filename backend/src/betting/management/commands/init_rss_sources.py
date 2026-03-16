from django.core.management.base import BaseCommand
from src.betting.models import NewsSource


class Command(BaseCommand):
    help = 'Initialize default RSS news sources'

    def handle(self, *args, **options):
        """Создать базовые RSS источники новостей"""
        
        default_sources = [
            {
                'name': 'Fast Company',
                'url': 'https://feeds.feedburner.com/fastcompany/headlines?_=9997',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 1,
                'keywords_filter': 'business, innovation, leadership, design, technology, entrepreneurship',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'Ritholtz',
                'url': 'https://ritholtz.com/feed/',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 2,
                'keywords_filter': 'finance, investing, markets, economy, business, analysis',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'Forbes Real-Time',
                'url': 'https://www.forbes.com/real-time/feed2/',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 3,
                'keywords_filter': 'business, finance, economy, markets, investing, entrepreneurship',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'Financial Times International',
                'url': 'https://www.ft.com/rss/home/international',
                'source_type': 'rss',
                'category': 'general',
                'language': 'en',
                'priority': 4,
                'keywords_filter': 'finance, business, economy, markets, international, politics',
                'exclude_keywords': 'sports, entertainment'
            },
            {
                'name': 'Harvard Business Review',
                'url': 'http://feeds.harvardbusiness.org/harvardbusiness/',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 5,
                'keywords_filter': 'business, management, leadership, strategy, innovation, entrepreneurship',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'HubSpot Marketing Blog',
                'url': 'https://blog.hubspot.com/marketing/rss.xml',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 6,
                'keywords_filter': 'marketing, business, digital, strategy, growth, sales',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'Abnormal Returns',
                'url': 'https://abnormalreturns.com/feed/',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 7,
                'keywords_filter': 'finance, investing, markets, analysis, trading, economy',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'Calculated Risk Blog',
                'url': 'http://www.calculatedriskblog.com/feeds/posts/default',
                'source_type': 'rss',
                'category': 'general',
                'language': 'en',
                'priority': 8,
                'keywords_filter': 'finance, economy, housing, markets, analysis, data',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'I Will Teach You To Be Rich',
                'url': 'https://www.iwillteachyoutoberich.com/feed/',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 9,
                'keywords_filter': 'personal finance, investing, money, business, entrepreneurship',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'Copyblogger',
                'url': 'https://copyblogger.com/feed/',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 10,
                'keywords_filter': 'marketing, content, writing, business, digital, strategy',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'Naked Capitalism',
                'url': 'https://www.nakedcapitalism.com/feed',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 11,
                'keywords_filter': 'finance, economy, politics, analysis, markets, banking',
                'exclude_keywords': 'sports, entertainment'
            },
            {
                'name': 'New York Times Economy',
                'url': 'https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml',
                'source_type': 'rss',
                'category': 'general',
                'language': 'en',
                'priority': 12,
                'keywords_filter': 'economy, business, finance, markets, policy, analysis',
                'exclude_keywords': 'sports, entertainment'
            },
            {
                'name': 'Dow Jones Top Stories',
                'url': 'https://feeds.content.dowjones.io/public/rss/mw_topstories',
                'source_type': 'rss',
                'category': 'technology',
                'language': 'en',
                'priority': 13,
                'keywords_filter': 'technology, business, finance, markets, news, analysis',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'New York Times Business',
                'url': 'https://rss.nytimes.com/services/xml/rss/nyt/Business.xml',
                'source_type': 'rss',
                'category': 'general',
                'language': 'en',
                'priority': 14,
                'keywords_filter': 'business, finance, economy, markets, corporate, analysis',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'Seeking Alpha',
                'url': 'https://seekingalpha.com/feed.xml',
                'source_type': 'rss',
                'category': 'general',
                'language': 'en',
                'priority': 15,
                'keywords_filter': 'finance, investing, markets, stocks, analysis, earnings',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'Seth Godin Blog',
                'url': 'https://seths.blog/feed/atom/',
                'source_type': 'atom',
                'category': 'general',
                'language': 'en',
                'priority': 16,
                'keywords_filter': 'marketing, business, leadership, innovation, strategy, creativity',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'Tim Ferriss Blog',
                'url': 'https://tim.blog/feed/',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 17,
                'keywords_filter': 'productivity, business, lifestyle, health, entrepreneurship, learning',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'WirtschaftsWoche',
                'url': 'https://www.wiwo.de/contentexport/feed/rss/schlagzeilen',
                'source_type': 'feed',
                'category': 'general',
                'language': 'de',
                'priority': 18,
                'keywords_filter': 'business, economy, finance, markets, politics, analysis',
                'exclude_keywords': 'sports, entertainment'
            },
            {
                'name': 'Zero Hedge',
                'url': 'https://feeds.feedburner.com/zerohedge/feed',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 19,
                'keywords_filter': 'finance, markets, economy, politics, analysis, trading',
                'exclude_keywords': 'sports, entertainment'
            },
            {
                'name': 'Entrepreneur Latest',
                'url': 'https://feeds.feedburner.com/entrepreneur/latest',
                'source_type': 'feed',
                'category': 'general',
                'language': 'en',
                'priority': 20,
                'keywords_filter': 'entrepreneurship, business, startup, innovation, leadership, success',
                'exclude_keywords': 'sports, entertainment, politics'
            },
            {
                'name': 'Small Business Trends',
                'url': 'https://feeds.feedburner.com/SmallBusinessTrends?_=1153',
                'source_type': 'rss',
                'category': 'general',
                'language': 'en',
                'priority': 21,
                'keywords_filter': 'small business, entrepreneurship, marketing, technology, trends, strategy',
                'exclude_keywords': 'sports, entertainment, politics'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for source_data in default_sources:
            source, created = NewsSource.objects.get_or_create(
                url=source_data['url'],
                defaults=source_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created RSS source: {source.name}')
                )
            else:
                # Обновляем существующий источник
                for key, value in source_data.items():
                    if key != 'url':
                        setattr(source, key, value)
                source.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated RSS source: {source.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'RSS sources initialization completed. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
