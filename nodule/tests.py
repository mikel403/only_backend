from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from . import models


class NodulePhysicistPaginationTests(APITestCase):
    url = "/api/nodules/"

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="radiologist", password="x")
        cls.other = User.objects.create_user(username="other", password="x")
        n = [models.Nodule.objects.create(name=f"nodule{i}") for i in range(6)]
        # Uploaded by another user: never listed for cls.user
        cls.foreign = models.Nodule.objects.create(name="foreign", new="other")
        # Described ids are interleaved with pending ones so the expected order is not the insertion order
        for nodule in (n[1], n[3], n[3], n[4]):
            models.Description.objects.create(user=cls.user, nodule=nodule)
        models.Description.objects.create(user=cls.other, nodule=n[0])
        cls.pending = [n[0].id, n[2].id, n[5].id]
        cls.described = [n[1].id, n[3].id, n[4].id]

    def setUp(self):
        self.client.force_authenticate(self.user)

    def get_ids(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return [nodule["id"] for nodule in response.data]

    def walk_pages(self, limit, **params):
        ids, start = [], 0
        while True:
            page = self.get_ids(_start=start, _limit=limit, **params)
            if not page:
                return ids
            ids += page
            start += limit

    def test_pending_first_then_described_ordered_by_id(self):
        self.assertEqual(self.get_ids(), self.pending + self.described)
        self.assertEqual(self.get_ids(_timesDescribed="all"), self.pending + self.described)

    def test_order_is_stable(self):
        first = self.get_ids(_start=0, _limit=4)
        for _ in range(3):
            self.assertEqual(self.get_ids(_start=0, _limit=4), first)

    def test_pages_have_no_repeated_or_missing_nodules(self):
        for limit in (1, 2, 4):
            with self.subTest(limit=limit):
                ids = self.walk_pages(limit)
                self.assertEqual(ids, self.pending + self.described)
                self.assertNotIn(self.foreign.id, ids)

    def test_only_pending_pages(self):
        self.assertEqual(self.walk_pages(2, _timesDescribed="0"), self.pending)

    def test_only_described_pages(self):
        # Nodule described twice by the user appears only once
        self.assertEqual(self.walk_pages(2, _timesDescribed="1"), [self.described[0], self.described[2]])
        self.assertEqual(self.walk_pages(2, _timesDescribed="2"), [self.described[1]])

    def test_counters_are_kept(self):
        response = self.client.get(self.url, {"_start": 0, "_limit": 2})
        first = response.data[0]
        self.assertEqual(first["numNodules"], 3)
        self.assertEqual(first["numNodulesDescribed"], 3)
        self.assertEqual(first["numNodules2Times"], 1)
        self.assertNotIn("orderPriority", first)
