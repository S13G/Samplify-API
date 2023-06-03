import nltk
import praw
from decouple import config
from newsapi import NewsApiClient
from nltk.sentiment import SentimentIntensityAnalyzer
from rest_framework import generics, status
from rest_framework.response import Response
from sklearn.feature_extraction.text import CountVectorizer

from trends.serializers import MarketTrendsSerializer, RedditDataSerializer

nltk.download('vader_lexicon')


# Create your views here.
class AnalyzeMarketTrendsView(generics.GenericAPIView):
    serializer_class = MarketTrendsSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data.get('query', '')
        language = serializer.validated_data.get('language', 'en')

        all_insights = []
        sort_criteria = {
            'publishedAt': 'published date',
            'popularity': 'popularity',
            'relevancy': 'relevancy'
        }

        for sort_by, criteria in sort_criteria.items():
            response = self.get_news_articles(query, sort_by, language)
            articles = response['articles']
            print(f"Total Results based on {criteria}: {len(articles)}")
            insights = self.analyze_articles(articles)

            # Word Frequencies and Vectorization
            text_data = [article['title'] + ' ' + article['description'] for article in articles]

            vectorizer = CountVectorizer()
            vectorized_data = vectorizer.fit_transform(text_data)
            feature_names = vectorizer.get_feature_names_out()

            word_frequencies = vectorized_data.sum(axis=0)
            top_words = [(string, word_frequencies[0, idx]) for string, idx in vectorizer.vocabulary_.items()]
            top_words.sort(key=lambda x: x[1], reverse=True)
            top_words_data = [(string, frequency) for string, frequency in top_words[:10]]

            insights[-1].update({
                "Word Frequencies": dict(
                        sorted(zip(feature_names, word_frequencies.A1), key=lambda x: x[1], reverse=True)),
                "Top Words": top_words_data if top_words_data else None
            })

            # Remove empty "Top Words" and "Word Frequencies" keys
            for article in insights:
                if "Top Words" in article and not article["Top Words"]:
                    del article["Top Words"]
                if "Word Frequencies" in article and not article["Word Frequencies"]:
                    del article["Word Frequencies"]

            insights_dict = {
                "Sort Criteria": criteria,
                "Articles": insights
            }

            all_insights.append(insights_dict)

        response_data = {
            "message": "Data retrieved",
            "data": all_insights,
            "status": "success",
            "statement": f"Total Results based on {len(all_insights)} sorting criteria.",
            "total_results": len(articles),
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def get_news_articles(self, query, sort_by, language):
        newsapi = NewsApiClient(api_key=config('NEWSAPI_KEY'))
        return newsapi.get_everything(q=query, sort_by=sort_by, language=language)

    def analyze_articles(self, articles):
        insights = []
        if articles:
            for article in articles:
                insight = self.analyze_article(article)
                insights.append(insight)
        else:
            return Response({"msg": "No articles found for specific query", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        return insights

    def analyze_article(self, article):
        sia = SentimentIntensityAnalyzer()
        title_sentiment_score = sia.polarity_scores(article['title'])
        description = article['description']
        if description is not None:
            description_sentiment_score = sia.polarity_scores(description)
        else:
            description_sentiment_score = None

        insight = {
            "Title": article['title'],
            "Description": article['description'],
            "URL": article['url'],
            "Title Sentiment Score": title_sentiment_score,
            "Description Sentiment Score": description_sentiment_score,
        }
        if "Word Frequencies" in article:
            insight.update({"Word Frequencies": {}})
        if "Top Words" in article:
            insight.update({"Top Words": {}})
        return insight


class AnalyzeRedditDataView(generics.GenericAPIView):
    serializer_class = RedditDataSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        keyword = serializer.validated_data.get('keyword', '')
        limit = serializer.validated_data.get('limit', 5)

        return self.analyze_reddit_data(keyword, limit)

    def analyze_reddit_data(self, keyword, limit):
        reddit = praw.Reddit(
                client_id=config('REDDIT_CLIENT_ID'),
                client_secret=config('REDDIT_CLIENT_SECRET'),
                user_agent=config('REDDIT_USER_AGENT')
        )

        nltk.download('vader_lexicon')
        sia = SentimentIntensityAnalyzer()

        query = f'{keyword} site:reddit.com'
        results = reddit.subreddit('all').search(query, time_filter='all', sort='top', limit=limit)

        insights = []
        titles = []
        descriptions = []

        for submission in results:
            title = submission.title
            score = submission.score
            description = submission.selftext
            url = submission.url

            title_sentiment = sia.polarity_scores(title)
            title_sentiment_score = title_sentiment['compound']

            description_sentiment = sia.polarity_scores(description)
            description_sentiment_score = description_sentiment['compound']

            upvotes = submission.ups
            comments = submission.num_comments
            engagement_rate = comments / upvotes if upvotes > 0 else 0

            insight = {
                'Title': title,
                'Score': score,
                'Description': description,
                'URL': url,
                'Title Sentiment Score': title_sentiment_score,
                'Description Sentiment Score': description_sentiment_score,
                'Upvotes': upvotes,
                'Comments': comments,
                'Engagement Rate': round(engagement_rate, 4)
            }

            titles.append(title)
            descriptions.append(description)
            insights.append(insight)

        text_data = titles + descriptions

        vectorizer = CountVectorizer()
        vectorized_data = vectorizer.fit_transform(text_data)
        feature_names = vectorizer.get_feature_names_out()

        word_frequencies = vectorized_data.sum(axis=0)
        top_words = [(string, word_frequencies[0, idx]) for string, idx in vectorizer.vocabulary_.items()]
        top_words.sort(key=lambda x: x[1], reverse=True)
        top_words_data = [(string, frequency) for string, frequency in top_words[:10]]

        insights_dict = {
            "Sort Criteria": "Top",
            "Articles": insights,
            "Word Frequencies": dict(sorted(zip(feature_names, word_frequencies.A1), key=lambda x: x[1], reverse=True)),
            "Top Words": top_words_data
        }

        response_data = {
            "message": "All data retrieved",
            "data": insights_dict,
            "status": "success"
        }

        return Response(response_data, status=status.HTTP_200_OK)
