import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import resolve
from PIL import Image
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

    def test_private_urls_are_relative_to_the_api(self):
        # The frontend adds its base url, which includes the /djangoapp prefix in production
        response = self.client.get("/api/nodules-descriptions/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data)
        for nodule in response.data:
            self.assertEqual(nodule["private_image_url"], f"/api/nodules/{nodule['id']}/image/")
            self.assertEqual(resolve(nodule["private_full_image_url"]).url_name, "nodule-full-image")


#Uploaded files go to a temporary folder instead of the real media folder
@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class NoduleUploadConsentTests(APITestCase):
    url = "/api/nodules/"

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.radiologist = User.objects.create_user(username="radiologist", password="x")
        models.Physicist.objects.create(user=cls.radiologist)
        cls.user = User.objects.create_user(username="student", password="x")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(models.Nodule._meta.get_field("image").storage.location, ignore_errors=True)
        super().tearDownClass()

    def upload(self, user, **flags):
        buffer = io.BytesIO()
        Image.new("RGB", (4, 4)).save(buffer, format="PNG")
        image = SimpleUploadedFile("nodule.png", buffer.getvalue(), content_type="image/png")
        data = {"name": "nodule", "image": image, "public": "false", "research": "false", "declaration": "false"}
        data.update({key: str(value).lower() for key, value in flags.items()})
        self.client.force_authenticate(user)
        return self.client.post(self.url, data, format="multipart")

    def test_sharing_without_declaration_is_rejected(self):
        for flag in ("public", "research"):
            with self.subTest(flag=flag):
                response = self.upload(self.radiologist, **{flag: True})
                self.assertEqual(response.status_code, 400)
                self.assertIn("declaration", response.data)
        self.assertFalse(models.Nodule.objects.exists())

    def test_sharing_with_declaration_is_saved(self):
        response = self.upload(self.radiologist, research=True, declaration=True)
        self.assertEqual(response.status_code, 201)
        nodule = models.Nodule.objects.get(id=response.data["id"])
        self.assertTrue(nodule.research)
        self.assertTrue(nodule.declaration)

    def test_only_radiologists_can_share(self):
        response = self.upload(self.user, public=True, declaration=True)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(models.Nodule.objects.exists())

    def test_declaration_is_not_stored_without_sharing(self):
        response = self.upload(self.user, declaration=True)
        self.assertEqual(response.status_code, 201)
        self.assertFalse(models.Nodule.objects.get(id=response.data["id"]).declaration)
