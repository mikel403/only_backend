import csv
import importlib
import io
import shutil
import tempfile
import zoneinfo
from datetime import datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
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


    def test_ai_descriptions_are_limited_per_user(self):
        nodule = models.Nodule.objects.create(name="public")
        self.client.force_authenticate(self.user)
        # Precomputed probabilities avoid loading the real model
        with mock.patch("nodule.views.isInDatabase", return_value=True), \
                mock.patch("nodule.views.probs_database", return_value={}) as probs:
            for _ in range(10):
                self.assertEqual(self.client.post(f"/api/nodules/{nodule.id}/AIDescription").status_code, 200)
            self.assertEqual(self.client.post(f"/api/nodules/{nodule.id}/AIDescription").status_code, 429)
            self.assertEqual(probs.call_count, 10)

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



class ExpertDescriptionCountTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="student", password="x")
        cls.expert = User.objects.create_user(username="expert", password="x")
        cls.second = User.objects.create_user(username="second", password="x")
        for expert in (cls.expert, cls.second):
            models.Physicist.objects.create(user=expert)
        cls.nodule = models.Nodule.objects.create(name="public")
        # The expert described the nodule three times; the last time without margin
        for shape, margin in (("oval", "circumscribed"), ("oval", "spiculated"), ("round", None)):
            models.Description.objects.create(user=cls.expert, nodule=cls.nodule, shape=shape, margin=margin)
        models.Description.objects.create(user=cls.second, nodule=cls.nodule, shape="oval")

    def setUp(self):
        self.client.force_authenticate(self.user)

    def test_ground_truth_counts_every_description_of_the_expert(self):
        response = self.client.post(f"/api/nodules/{self.nodule.id}/expert/physician_ground_truth")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["shape"]["total"], 3)
        self.assertAlmostEqual(response.data["shape"]["oval"] * 3, 2)
        self.assertAlmostEqual(response.data["shape"]["round"] * 3, 1)
        self.assertEqual(response.data["margin"]["total"], 2)

    def test_expert_panel_still_counts_one_vote_per_expert(self):
        response = self.client.post(f"/api/nodules/{self.nodule.id}/expert-panel")
        self.assertEqual(response.status_code, 200)
        # Last description of each expert: round (expert) and oval (second)
        self.assertEqual(response.data["shape"]["total"], 2)
        self.assertAlmostEqual(response.data["shape"]["round"], 0.5)
        self.assertAlmostEqual(response.data["shape"]["oval"], 0.5)


class OrientationMigrationTests(APITestCase):
    def test_rollback_keeps_not_assessed_orientations(self):
        from django.apps import apps
        migration = importlib.import_module("nodule.migrations.0015_remove_no_orientation")
        nodule = models.Nodule.objects.create(name="public")
        description = models.Description.objects.create(ai=models.AI.objects.create(name="AI"), nodule=nodule, orientation=None)
        migration.backwards(apps, None)
        description.refresh_from_db()
        self.assertIsNone(description.orientation)


class DescriptionAdminTests(TestCase):
    url = "/admin/nodule/description/"

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_superuser(username="admin", password="x")
        cls.staff = User.objects.create_user(username="student", password="x")
        cls.expert = User.objects.create_user(username="expert", password="x")
        models.Physicist.objects.create(user=cls.expert)
        cls.ai = models.AI.objects.create(name="AI_test")
        cls.nodule = models.Nodule.objects.create(name="public")
        madrid = zoneinfo.ZoneInfo("Europe/Madrid")
        cls.old = models.Description.objects.create(user=cls.expert, nodule=cls.nodule, shape="oval", birads="3")
        cls.new = models.Description.objects.create(user=cls.staff, nodule=cls.nodule, shape="round", birads="4A")
        cls.by_ai = models.Description.objects.create(ai=cls.ai, nodule=cls.nodule, shape="oval", birads="3")
        # time is auto_now_add, so the dates are set after creating the rows
        models.Description.objects.filter(id=cls.old.id).update(time=datetime(2026, 3, 2, 10, 0, tzinfo=madrid))
        models.Description.objects.filter(id=cls.new.id).update(time=datetime(2026, 3, 20, 23, 30, tzinfo=madrid))
        models.Description.objects.filter(id=cls.by_ai.id).update(time=datetime(2026, 4, 1, 9, 0, tzinfo=madrid))

    def setUp(self):
        self.client.force_login(self.admin)

    def listed_ids(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return sorted(d.id for d in response.context["cl"].result_list)

    def test_only_staff_can_open_it(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_descriptions_are_read_only(self):
        self.assertEqual(self.client.get(self.url + "add/").status_code, 403)
        response = self.client.post(f"{self.url}{self.old.id}/change/", {"shape": "round"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post(f"{self.url}{self.old.id}/delete/", {"post": "yes"}).status_code, 403)
        response = self.client.get(self.url)
        self.assertNotIn("delete_selected", response.context["action_form"].fields["action"].choices.__str__())
        self.assertEqual(models.Description.objects.get(id=self.old.id).shape, "oval")

    def test_date_range_filter_uses_madrid_dates(self):
        # 20 March 23:30 in Madrid is already 21 March in some other zones, but here it belongs to the 20th
        ids = self.listed_ids(time__range__gte="2026-03-01", time__range__lte="2026-03-20")
        self.assertEqual(ids, sorted([self.old.id, self.new.id]))
        self.assertEqual(self.listed_ids(time__range__gte="2026-03-21"), [self.by_ai.id])

    def test_author_type_filter(self):
        self.assertEqual(self.listed_ids(author_type="radiologist"), [self.old.id])
        self.assertEqual(self.listed_ids(author_type="user"), [self.new.id])
        self.assertEqual(self.listed_ids(author_type="ai"), [self.by_ai.id])

    def test_export_csv(self):
        response = self.client.post(self.url, {
            "action": "export_csv",
            "_selected_action": [self.old.id, self.by_ai.id],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
        self.assertEqual(rows[0][:4], ["description_id", "time", "author", "author_type"])
        self.assertEqual(rows[1][:4], [str(self.old.id), "2026-03-02 10:00:00", "expert", "radiologist"])
        self.assertEqual(rows[2][2:4], ["AI_test", "ai"])
        self.assertEqual(len(rows), 3)


class UserAdminTests(TestCase):
    url = "/admin/auth/user/"

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_superuser(username="admin", password="x")
        cls.expert = User.objects.create_user(username="expert", password="x")
        models.Physicist.objects.create(user=cls.expert, experience=10)
        cls.student = User.objects.create_user(username="student", password="x")
        cls.test_user = User.objects.create_user(username="TestUser", password="x")
        models.TestUser.objects.create(user=cls.test_user)
        public = models.Nodule.objects.create(name="public")
        own = [models.Nodule.objects.create(name=f"own{i}", new="expert") for i in range(2)]
        # Three descriptions of two different nodules
        for nodule in (public, public, own[0]):
            models.Description.objects.create(user=cls.expert, nodule=nodule, birads="3")
        madrid = zoneinfo.ZoneInfo("Europe/Madrid")
        times = [datetime(2026, 1, 5, tzinfo=madrid), datetime(2026, 2, 5, tzinfo=madrid), datetime(2026, 3, 5, tzinfo=madrid)]
        for description, time in zip(models.Description.objects.order_by("id"), times):
            models.Description.objects.filter(id=description.id).update(time=time)
        cls.times = times

    def setUp(self):
        self.client.force_login(self.admin)

    def rows(self, url, **params):
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        # Rows are users in the user list and Physicist objects in the radiologist list
        return {(row.user if isinstance(row, models.Physicist) else row).username: row for row in response.context["cl"].result_list}

    def test_activity_columns(self):
        rows = self.rows(self.url)
        expert, student = rows["expert"], rows["student"]
        self.assertEqual(expert.num_descriptions, 3)
        self.assertEqual(expert.num_nodules_described, 2)
        self.assertEqual(expert.first_description, self.times[0])
        self.assertEqual(expert.last_description, self.times[2])
        self.assertEqual(expert.num_uploaded, 2)
        self.assertEqual((student.num_descriptions, student.num_uploaded), (0, 0))

    def test_links_open_the_filtered_lists(self):
        content = self.client.get(self.url).content.decode()
        self.assertIn(f"/admin/nodule/description/?user__id__exact={self.expert.id}", content)
        self.assertIn("/admin/nodule/nodule/?new__exact=expert", content)
        self.assertEqual(self.client.get(f"/admin/nodule/description/?user__id__exact={self.expert.id}").status_code, 200)
        response = self.client.get("/admin/nodule/nodule/?new__exact=expert")
        self.assertEqual(len(response.context["cl"].result_list), 2)

    def test_role_filter(self):
        self.assertEqual(set(self.rows(self.url, role="radiologist")), {"expert"})
        self.assertEqual(set(self.rows(self.url, role="test")), {"TestUser"})
        self.assertEqual(set(self.rows(self.url, role="user")), {"admin", "student"})

    def test_make_radiologist_skips_test_users(self):
        self.client.post(self.url, {
            "action": "make_radiologist",
            "_selected_action": [self.student.id, self.test_user.id, self.expert.id],
        })
        self.assertTrue(models.Physicist.objects.filter(user=self.student).exists())
        self.assertFalse(models.Physicist.objects.filter(user=self.test_user).exists())
        self.assertEqual(models.Physicist.objects.get(user=self.expert).experience, 10)

    def test_radiologist_list_shows_activity(self):
        rows = self.rows("/admin/nodule/physicist/")
        self.assertEqual(set(rows), {"expert"})
        self.assertEqual(rows["expert"].num_descriptions, 3)
        self.assertEqual(rows["expert"].num_uploaded, 2)
        self.assertEqual(self.client.get(f"/admin/nodule/physicist/{self.expert.id}/change/").status_code, 200)
