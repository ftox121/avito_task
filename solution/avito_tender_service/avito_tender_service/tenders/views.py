from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Tender, Bid, Organization, BidReview, TenderVersion, Employee, BidVersion
from .serializers import TenderSerializer, BidSerializer, BidReviewSerializer


class TenderListView(generics.ListAPIView):
    queryset = Tender.objects.all()
    serializer_class = TenderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        service_type = self.request.query_params.get('serviceType', None)
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        return queryset


class TenderCreateView(generics.CreateAPIView):
    queryset = Tender.objects.all()
    serializer_class = TenderSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        organization_id = data.get('organizationId')
        creator_username = data.get('creatorUsername')

        if not organization_id:
            return Response({'error': 'organization is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not creator_username:
            return Response({'error': 'creator is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            creator = Employee.objects.get(username=creator_username)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_400_BAD_REQUEST)

        tender = Tender.objects.create(
            name=data.get('name', ''),
            description=data.get('description', ''),
            service_type=data.get('serviceType', ''),
            status=data.get('status', ''),
            organization=organization,
            creator=creator
        )

        serializer = TenderSerializer(tender)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserTenderListView(generics.ListAPIView):
    serializer_class = TenderSerializer

    def get_queryset(self):
        username = self.request.query_params.get('username')
        if not username:
            raise NotFound("Username parameter is required")

        return Tender.objects.filter(creator__username=username)


class TenderUpdateView(generics.UpdateAPIView):
    queryset = Tender.objects.all()
    serializer_class = TenderSerializer
    lookup_field = 'pk'


class TenderRollbackView(APIView):
    def put(self, request, *args, **kwargs):
        tender_id = kwargs.get('tenderId')
        version = kwargs.get('version')

        try:
            tender_version = TenderVersion.objects.get(tender_id=tender_id, version=version)
            tender = tender_version.tender
            tender.name = tender_version.name
            tender.description = tender_version.description
            tender.save()

            return Response({
                'id': tender.id,
                'name': tender.name,
                'description': tender.description,
                'created_at': tender.created_at,
                'updated_at': tender.updated_at,
            }, status=status.HTTP_200_OK)
        except TenderVersion.DoesNotExist:
            return Response({'error': 'Version not found'}, status=status.HTTP_404_NOT_FOUND)


class BidCreateView(generics.CreateAPIView):
    queryset = Bid.objects.all()
    serializer_class = BidSerializer

    def create(self, request, *args, **kwargs):
        data = request.data

        try:
            tender = Tender.objects.get(id=data.get('tenderId'))
        except Tender.DoesNotExist:
            return Response({'error': 'Tender not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            organization = Organization.objects.get(id=data.get('organizationId'))
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            created_by = User.objects.get(username=data.get('creatorUsername'))
        except User.DoesNotExist:
            return Response({'error': 'Creator not found'}, status=status.HTTP_404_NOT_FOUND)

        bid_data = {
            'name': data.get('name'),
            'description': data.get('description'),
            'status': data.get('status', 'SUBMITTED'),
            'tender': tender.id,
            'organization': organization.id,
            'created_by': created_by.id
        }

        serializer = self.get_serializer(data=bid_data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBidsListView(generics.ListAPIView):
    serializer_class = BidSerializer

    def get_queryset(self):
        username = self.request.query_params.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Bid.objects.none()
            return Bid.objects.filter(created_by=user)
        return Bid.objects.none()


class TenderBidsListView(generics.ListAPIView):
    serializer_class = BidSerializer

    def get_queryset(self):
        tender_id = self.kwargs.get('tenderId')
        return Bid.objects.filter(tender_id=tender_id)


class BidUpdateView(generics.UpdateAPIView):
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        bid = self.get_object()
        if bid.created_by != request.user:
            return Response({'error': 'You do not have permission to edit this bid'}, status=status.HTTP_403_FORBIDDEN)
        return super().patch(request, *args, **kwargs)


class BidRollbackView(APIView):
    def put(self, request, *args, **kwargs):
        bid_id = kwargs.get('bidId')
        version = kwargs.get('version')

        try:
            bid_version = BidVersion.objects.get(bid_id=bid_id, version=version)
            bid = bid_version.bid

            bid.name = bid_version.name
            bid.description = bid_version.description
            bid.save()

            response_data = {
                'id': bid.id,
                'name': bid.name,
                'description': bid.description,
                'status': bid.status,
                'tender': bid.tender.id,
                'organization': bid.organization.id,
                'created_by': bid.created_by.id,
                'created_at': bid.created_at,
                'updated_at': bid.updated_at,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except BidVersion.DoesNotExist:
            return Response({'error': 'Version not found'}, status=status.HTTP_404_NOT_FOUND)


class BidReviewsView(APIView):
    def get(self, request, *args, **kwargs):
        bid_id = kwargs.get('tenderId')
        author_username = request.query_params.get('authorUsername')
        organization_id = request.query_params.get('organizationId')

        reviews = BidReview.objects.filter(
            bid__tender_id=bid_id,
            author__username=author_username,
            bid__organization_id=organization_id
        )

        serializer = BidReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


