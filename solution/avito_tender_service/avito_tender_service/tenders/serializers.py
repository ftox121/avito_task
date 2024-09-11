from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Tender, Bid, BidReview, BidVersion


class TenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tender
        fields = ['id', 'name', 'description', 'service_type', 'status', 'organization', 'creator']


class PingView(APIView):
    def get(self, request):
        return Response('ok', status=status.HTTP_200_OK)


class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = ['id', 'name', 'description', 'status', 'tender', 'organization', 'created_by', 'created_at', 'updated_at']


class BidVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidVersion
        fields = ['id', 'bid', 'name', 'description', 'version']


class BidReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidReview
        fields = ['id', 'author', 'content', 'created_at']

