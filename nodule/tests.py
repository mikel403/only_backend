import io
import shutil
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from django.urls import resolve
from PIL import Image
from rest_framework.test import APITestCase

from . import models
from .utils.correlation import delta_fleiss_for_user
from .utils.descriptors import descriptors


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

    def test_large_images_are_rejected(self):
        with override_settings(MAX_UPLOAD_IMAGE_SIZE_MB=0):
            response = self.upload(self.user)
        self.assertEqual(response.status_code, 400)
        self.assertIn("image", response.data)
        self.assertFalse(models.Nodule.objects.exists())

    def test_large_images_are_not_sent_to_yolo(self):
        buffer = io.BytesIO()
        Image.new("RGB", (4, 4)).save(buffer, format="PNG")
        image = SimpleUploadedFile("nodule.png", buffer.getvalue(), content_type="image/png")
        self.client.force_authenticate(self.user)
        with override_settings(MAX_UPLOAD_IMAGE_SIZE_MB=0), mock.patch("nodule.views.yoloCrop") as yolo:
            response = self.client.post("/api/AIDetection", {"image": image}, format="multipart")
        self.assertEqual(response.status_code, 400)
        yolo.assert_not_called()


class DescribeNoduleAccessTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="radiologist", password="x")
        cls.public = models.Nodule.objects.create(name="public")
        cls.own = models.Nodule.objects.create(name="own", new="radiologist")
        cls.foreign = models.Nodule.objects.create(name="foreign", new="other")

    def setUp(self):
        self.client.force_authenticate(self.user)

    def describe(self, nodule_id):
        return self.client.post(f"/api/nodules/{nodule_id}/descriptions/", {"birads": "3"}, format="json")

    def test_public_and_own_nodules_can_be_described(self):
        for nodule in (self.public, self.own):
            with self.subTest(nodule=nodule.name):
                self.assertEqual(self.describe(nodule.id).status_code, 201)
        self.assertEqual(models.Description.objects.filter(user=self.user).count(), 2)

    def test_foreign_private_nodule_is_hidden(self):
        self.assertEqual(self.describe(self.foreign.id).status_code, 404)
        self.assertEqual(self.client.get(f"/api/nodules/{self.foreign.id}/descriptions/").status_code, 404)
        self.assertFalse(models.Description.objects.exists())

    def test_missing_or_invalid_nodule_returns_404(self):
        missing = models.Nodule.objects.order_by("-id").first().id + 1
        for nodule_id in (missing, "abc"):
            with self.subTest(nodule_id=nodule_id):
                self.assertEqual(self.describe(nodule_id).status_code, 404)
        self.assertFalse(models.Description.objects.exists())


class DescriptionVisibilityTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="radiologist", password="x")
        cls.expert = User.objects.create_user(username="expert", password="x")
        models.Physicist.objects.create(user=cls.expert)
        cls.student = User.objects.create_user(username="student", password="x")
        cls.ai = models.AI.objects.create(name="AI_test")
        cls.public = models.Nodule.objects.create(name="public")
        cls.foreign = models.Nodule.objects.create(name="foreign", new="expert")
        for nodule in (cls.public, cls.foreign):
            models.Description.objects.create(user=cls.expert, nodule=nodule, shape="oval", birads="3")
            models.Description.objects.create(ai=cls.ai, nodule=nodule, shape="oval", birads="3")
        models.Description.objects.create(user=cls.student, nodule=cls.public, shape="oval", birads="3")

    def setUp(self):
        self.client.force_authenticate(self.user)

    def oval_total(self, username):
        response = self.client.post(f"/api/{username}/statistics")
        self.assertEqual(response.status_code, 200)
        return response.data["statistics"]["shape"]["oval"]["total"]

    def test_detail_hides_foreign_private_nodules(self):
        self.assertEqual(self.client.get(f"/api/expert/nodules/{self.public.id}/descriptions").status_code, 200)
        self.assertEqual(self.client.get(f"/api/expert/nodules/{self.foreign.id}/descriptions").status_code, 404)

    def test_ai_descriptions_only_for_visible_nodules(self):
        response = self.client.get("/api/AI_test/descriptions")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([d["nodule_id"] for d in response.data], [self.public.id])

    def test_statistics_only_count_visible_nodules(self):
        self.assertEqual(self.oval_total("expert"), 1)
        self.assertEqual(self.oval_total("Overall"), 1)

    def test_statistics_only_for_radiologists(self):
        for username in ("student", "nobody"):
            with self.subTest(username=username):
                self.assertEqual(self.client.post(f"/api/{username}/statistics").status_code, 404)

    def test_overall_username_is_reserved(self):
        self.client.force_authenticate(None)
        for username in ("Overall", "overall"):
            with self.subTest(username=username):
                response = self.client.post("/auth/users/", {"username": username, "password": "Uned-2026-train"}, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertIn("username", response.data)
        self.assertFalse(get_user_model().objects.filter(username__iexact="overall").exists())

    def test_expert_panel_and_ground_truth_hide_foreign_private_nodules(self):
        for path in ("expert-panel", "expert/physician_ground_truth"):
            with self.subTest(path=path):
                self.assertEqual(self.client.post(f"/api/nodules/{self.public.id}/{path}").status_code, 200)
                self.assertEqual(self.client.post(f"/api/nodules/{self.foreign.id}/{path}").status_code, 404)

    def test_ai_description_hides_foreign_private_nodules(self):
        self.assertEqual(self.client.post(f"/api/nodules/{self.foreign.id}/AIDescription").status_code, 404)

    def test_intercorrelation_with_any_user_on_visible_nodules(self):
        # Old descriptions of a nodule that is no longer visible must not be counted
        for nodule in (self.public, self.foreign):
            models.Description.objects.create(user=self.user, nodule=nodule, shape="oval", birads="3")
        for username in ("expert", "student"):
            with self.subTest(username=username):
                response = self.client.post(f"/api/{username}/intercorrelation")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["num_descriptor"]["shape"], 1)


class TestUserReadOnlyTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.test_user = User.objects.create_user(username="TestUser", password="Uned-2026-train")
        models.TestUser.objects.create(user=cls.test_user)
        cls.user = User.objects.create_user(username="student", password="Uned-2026-train")
        cls.nodule = models.Nodule.objects.create(name="public")

    def setUp(self):
        self.client.force_authenticate(self.test_user)

    def test_test_user_can_not_save_anything(self):
        requests = [
            ("post", f"/api/nodules/{self.nodule.id}/descriptions/", {"birads": "3"}),
            ("post", "/api/nodules/", {"name": "nodule"}),
            ("put", "/api/physicists/me/", {"experience": 3}),
            ("put", "/auth/users/me/", {"first_name": "changed"}),
            ("patch", "/auth/users/me/", {"first_name": "changed"}),
            ("delete", "/auth/users/me/", {"current_password": "Uned-2026-train"}),
            ("post", "/auth/users/set_password/", {"current_password": "Uned-2026-train", "new_password": "Other-2026-pass"}),
            ("post", "/reset-password/", {"current_password": "Uned-2026-train", "new_password": "Other-2026-pass", "re_new_password": "Other-2026-pass"}),
        ]
        for method, url, data in requests:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, data, format="json")
                self.assertEqual(response.status_code, 403)
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.first_name, "")
        self.assertTrue(self.test_user.check_password("Uned-2026-train"))
        self.assertFalse(models.Description.objects.exists())
        self.assertEqual(models.Nodule.objects.count(), 1)

    def test_test_user_can_still_read(self):
        self.assertEqual(self.client.get("/api/nodules/").status_code, 200)
        self.assertEqual(self.client.get("/auth/users/me/").status_code, 200)
        self.assertEqual(self.client.post("/api/statistics").status_code, 200)

    def test_other_users_can_still_save(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.patch("/auth/users/me/", {"first_name": "changed"}, format="json").status_code, 200)
        self.assertEqual(self.client.post(f"/api/nodules/{self.nodule.id}/descriptions/", {"birads": "3"}, format="json").status_code, 201)


class AIDetectionThrottleTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="radiologist", password="x")
        cls.other = User.objects.create_user(username="other", password="x")

    def setUp(self):
        # Throttle counters live in the cache, so each test starts from zero
        cache.clear()

    def detect(self, user):
        buffer = io.BytesIO()
        Image.new("RGB", (4, 4)).save(buffer, format="PNG")
        image = SimpleUploadedFile("nodule.png", buffer.getvalue(), content_type="image/png")
        self.client.force_authenticate(user)
        return self.client.post("/api/AIDetection", {"image": image}, format="multipart")

    def test_detections_are_limited_per_user(self):
        with mock.patch("nodule.views.yoloCrop", return_value=[]) as yolo:
            for _ in range(10):
                self.assertEqual(self.detect(self.user).status_code, 200)
            self.assertEqual(self.detect(self.user).status_code, 429)
            self.assertEqual(yolo.call_count, 10)
            # The limit is per user
            self.assertEqual(self.detect(self.other).status_code, 200)


class DeltaFleissTests(SimpleTestCase):
    user = 1

    def rows(self, ratings):
        # ratings: {nodule_id: {user_id: shape}}
        rows, next_id = [], 1
        for nodule_id, by_user in ratings.items():
            for user_id, shape in by_user.items():
                rows.append({"id": next_id, "nodule_id": nodule_id, "user_id": user_id, "shape": shape})
                next_id += 1
        return rows

    def delta(self, ratings):
        return delta_fleiss_for_user(self.rows(ratings), self.user, "shape", descriptors["shape"])

    base = {
        1: {1: "oval", 2: "oval", 3: "oval"},
        2: {1: "round", 2: "oval", 3: "round"},
        # Only one other rater: not comparable without the user
        4: {1: "oval", 2: "oval"},
        # The user gave no shape for this nodule
        5: {1: None, 2: "round", 3: "irregular"},
    }

    def test_only_nodules_rated_by_the_user_with_two_other_raters(self):
        out = self.delta(self.base)
        self.assertEqual(out["overlap_n"], 2)
        self.assertEqual(out["lost_without_you"], 1)
        self.assertIsNotNone(out["delta"])

    def test_nodules_not_rated_by_the_user_do_not_change_delta(self):
        with_others = dict(self.base)
        with_others[3] = {2: "irregular", 3: "round"}
        with_others[6] = {2: "oval", 3: "oval", 4: "round"}
        self.assertEqual(self.delta(with_others), self.delta(self.base))
