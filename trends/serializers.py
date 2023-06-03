from rest_framework import serializers


class MarketTrendsSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=100)
    language = serializers.CharField(max_length=2, default='en')


class RedditDataSerializer(serializers.Serializer):
    keyword = serializers.CharField(max_length=100)
    limit = serializers.IntegerField(default=5)
