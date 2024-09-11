from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from tenders.models import Tender, Organization, Employee, TenderVersion, Bid, BidVersion, BidReview


class ServerAvailabilityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_ping(self):
        response = self.client.get(reverse('ping'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), 'ok')


class TenderTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        Tender.objects.create(name='Tender 1', description='Description 1', service_type='IT', status='Open')
        Tender.objects.create(name='Tender 2', description='Description 2', service_type='Construction',
                              status='Closed')
        Tender.objects.create(name='Tender 3', description='Description 3', service_type='IT', status='In Progress')

    def test_get_tenders(self):
        response = self.client.get(reverse('tender-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(len(response_data), 3)
        self.assertEqual(response_data[0]['name'], 'Tender 1')
        self.assertEqual(response_data[1]['description'], 'Description 2')

    def test_filter_by_service_type(self):
        response = self.client.get(reverse('tender-list'), {'serviceType': 'IT'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]['service_type'], 'IT')
        self.assertEqual(response_data[1]['service_type'], 'IT')


class TenderCreateTestCase(APITestCase):

    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Organization",
            description="Description of Test Organization",
            type="LLC"
        )

        self.creator = Employee.objects.create(
            username="user1",
            first_name="John",
            last_name="Doe"
        )

        self.url = reverse('tender-create')

        self.valid_payload = {
            "name": "Тендер 1",
            "description": "Описание тендера",
            "serviceType": "Construction",
            "status": "Open",
            "organizationId": str(self.organization.id),
            "creatorUsername": self.creator.username
        }

    def test_create_tender_success(self):
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Tender.objects.count(), 1)
        self.assertEqual(Tender.objects.get().name, "Тендер 1")

    def test_create_tender_invalid_employee(self):
        invalid_payload = self.valid_payload.copy()
        invalid_payload['creatorUsername'] = 'invalid_user'

        response = self.client.post(self.url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Employee not found', response.data['error'])


class MyTendersTestCase(APITestCase):

    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Organization",
            description="Description of Test Organization",
            type="LLC"
        )

        self.employee = Employee.objects.create(
            username="user1",
            first_name="John",
            last_name="Doe"
        )

        self.other_employee = Employee.objects.create(
            username="user2",
            first_name="Jane",
            last_name="Smith"
        )


        self.tender1 = Tender.objects.create(
            name="Тендер 1",
            description="Описание тендера 1",
            service_type="Construction",
            status="Open",
            organization=self.organization,
            creator=self.employee
        )

        self.tender2 = Tender.objects.create(
            name="Тендер 2",
            description="Описание тендера 2",
            service_type="IT",
            status="In Progress",
            organization=self.organization,
            creator=self.employee
        )

        self.tender3 = Tender.objects.create(
            name="Тендер 3",
            description="Описание тендера 3",
            service_type="Logistics",
            status="Closed",
            organization=self.organization,
            creator=self.other_employee
        )

        self.url = reverse('user-tenders-list')

    def test_get_my_tenders(self):
        response = self.client.get(self.url, {'username': 'user1'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], self.tender1.name)
        self.assertEqual(response.data[1]['name'], self.tender2.name)

    def test_get_other_user_tenders(self):
        response = self.client.get(self.url, {'username': 'user2'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.tender3.name)


class TenderEditTestCase(APITestCase):

    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Organization",
            description="Description of Test Organization",
            type="LLC"
        )

        self.employee = Employee.objects.create(
            username="user1",
            first_name="John",
            last_name="Doe"
        )

        # Создаем тендер
        self.tender = Tender.objects.create(
            name="Тендер 1",
            description="Описание тендера 1",
            service_type="Construction",
            status="Open",
            organization=self.organization,
            creator=self.employee
        )

        self.url = reverse('tender-edit', kwargs={'pk': self.tender.id})

        self.valid_payload = {
            "name": "Обновленный Тендер 1",
            "description": "Обновленное описание"
        }

    def test_edit_tender_success(self):
        response = self.client.patch(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tender.refresh_from_db()
        self.assertEqual(self.tender.name, "Обновленный Тендер 1")
        self.assertEqual(self.tender.description, "Обновленное описание")

    def test_edit_tender_partial_update(self):
        partial_payload = {
            "name": "Частично обновленный Тендер"
        }
        response = self.client.patch(self.url, partial_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tender.refresh_from_db()
        self.assertEqual(self.tender.name, "Частично обновленный Тендер")
        self.assertEqual(self.tender.description, "Описание тендера 1")


class TenderRollbackTestCase(APITestCase):
    def setUp(self):
        self.tender = Tender.objects.create(name="Тендер 1", description="Описание тендера")
        self.tender_version_1 = TenderVersion.objects.create(
            tender=self.tender,
            version=1,
            name="Тендер 1 версия 1",
            description="Описание тендера версия 1"
        )
        self.tender_version_2 = TenderVersion.objects.create(
            tender=self.tender,
            version=2,
            name="Тендер 1 версия 2",
            description="Описание тендера версия 2"
        )
        self.url = reverse('tender-rollback', kwargs={'tenderId': self.tender.id, 'version': 2})

    def test_rollback_tender(self):
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Тендер 1 версия 2")
        self.assertEqual(response.data['description'], "Описание тендера версия 2")


class BidCreateTestCase(APITestCase):
    def setUp(self):
        self.tender = Tender.objects.create(name="Тендер 1", description="Описание тендера")
        self.organization = Organization.objects.create(name="Организация 1")
        self.creator = User.objects.create(username="user1")
        self.url = reverse('bid-create')

    def test_create_bid_success(self):
        data = {
            "name": "Предложение 1",
            "description": "Описание предложения",
            "status": "SUBMITTED",
            "tenderId": self.tender.id,
            "organizationId": self.organization.id,
            "creatorUsername": self.creator.username
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], "Предложение 1")


class UserBidsListTestCase(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Organization 1")
        self.user = User.objects.create(username='user1')
        self.other_user = User.objects.create(username='user2')
        self.tender = Tender.objects.create(name="Тендер 1", description="Описание тендера")
        self.bid1 = Bid.objects.create(name="Предложение 1", description="Описание предложения 1", tender=self.tender, organization=self.organization, created_by=self.user)
        self.bid2 = Bid.objects.create(name="Предложение 2", description="Описание предложения 2", tender=self.tender, organization=self.organization, created_by=self.other_user)
        self.url = reverse('user-bids-list') + f'?username={self.user.username}'

    def test_user_bids_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Предложение 1')


class TenderBidsListTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='user1')
        self.organization = Organization.objects.create(name="Org1")
        self.tender = Tender.objects.create(name="Tender 1", description="Description 1",
                                            organization=self.organization)
        self.bid1 = Bid.objects.create(
            name="Предложение 1",
            description="Описание предложения 1",
            tender=self.tender,
            organization=self.organization,
            created_by=self.user
        )
        self.url = reverse('tender-bids-list', kwargs={'tenderId': self.tender.id})

    def test_tender_bids_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_data = response.content.decode('utf-8')

        self.assertIn('Предложение 1', response_data)


class BidRollbackTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='user1')
        self.organization = Organization.objects.create(name="Org1")
        self.tender = Tender.objects.create(name="Tender 1", description="Description 1", organization=self.organization)
        self.bid = Bid.objects.create(
            name="Предложение 1",
            description="Описание предложения 1",
            tender=self.tender,
            organization=self.organization,
            created_by=self.user
        )

        self.bid_version_1 = BidVersion.objects.create(
            bid=self.bid,
            name="Предложение 1 версия 1",
            description="Описание предложения версия 1",
            version=1
        )
        self.bid_version_2 = BidVersion.objects.create(
            bid=self.bid,
            name="Предложение 1 версия 2",
            description="Описание предложения версия 2",
            version=2
        )
        self.url = f'/api/bids/{self.bid.id}/rollback/2/'

    def test_bid_rollback_success(self):
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Предложение 1 версия 2')

    def test_bid_rollback_invalid_version(self):
        invalid_url = f'/api/bids/{self.bid.id}/rollback/999/'
        response = self.client.put(invalid_url)
        self.assertEqual(response.status_code, 404)


class BidReviewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create(username='user2')
        self.organization = Organization.objects.create(name='Org1')
        self.tender = Tender.objects.create(name='Tender1', organization=self.organization)
        self.bid = Bid.objects.create(
            name='Bid1',
            description='Bid Description',
            tender=self.tender,
            organization=self.organization,
            created_by=self.user
        )
        self.review = BidReview.objects.create(
            bid=self.bid,
            author=self.user,
            content='This is a review'
        )

        self.url = f'/api/bids/{self.tender.id}/reviews?authorUsername=user2&organizationId={self.organization.id}'

    def test_get_reviews(self):
        response = self.client.get(reverse('bid-reviews', kwargs={'tenderId': self.tender.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)