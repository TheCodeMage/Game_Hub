
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Game, Genre, Platform, Review, SystemRequirement


User = get_user_model()


class StorefrontViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="frontendtester",
            password="TestPassword123!",
        )

        cls.genre = Genre.objects.create(name="Horror")
        cls.platform = Platform.objects.create(name="Windows")

        cls.published_game = Game.objects.create(
            title="Nightfall",
            price=Decimal("20.00"),
            currency="USD",
            discount_percent=25,
            is_published=True,
            is_featured=True,
            release_date="2026-01-15",
        )
        cls.published_game.genres.add(cls.genre)
        cls.published_game.platforms.add(cls.platform)

        cls.unpublished_game = Game.objects.create(
            title="Secret Project",
            price=Decimal("10.00"),
            is_published=False,
        )

        SystemRequirement.objects.create(
            game=cls.published_game,
            platform=cls.platform,
            requirement_type="minimum",
            processor="Intel Core i5",
            memory="8 GB RAM",
            storage="20 GB",
        )

        Review.objects.create(
            user=cls.user,
            game=cls.published_game,
            rating=5,
            comment="Excellent game.",
            is_published=True,
        )

    def test_home_page_returns_success(self):
        response = self.client.get(reverse("store:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/home.html")
        self.assertContains(response, "Nightfall")
        self.assertNotContains(response, "Secret Project")

    def test_catalog_page_returns_success(self):
        response = self.client.get(reverse("store:catalog"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/catalog.html")
        self.assertContains(response, "Nightfall")
        self.assertNotContains(response, "Secret Project")

    def test_catalog_search(self):
        response = self.client.get(
            reverse("store:catalog"),
            {"q": "Nightfall"},
        )

        self.assertContains(response, "Nightfall")
        self.assertNotContains(response, "Secret Project")

    def test_catalog_genre_filter(self):
        response = self.client.get(
            reverse("store:catalog"),
            {"genre": self.genre.slug},
        )

        self.assertContains(response, "Nightfall")

    def test_catalog_platform_filter(self):
        response = self.client.get(
            reverse("store:catalog"),
            {"platform": self.platform.code},
        )

        self.assertContains(response, "Nightfall")

    def test_catalog_price_filter(self):
        response = self.client.get(
            reverse("store:catalog"),
            {"min_price": "15", "max_price": "25"},
        )

        self.assertContains(response, "Nightfall")

    def test_catalog_sorting(self):
        response = self.client.get(
            reverse("store:catalog"),
            {"sort": "price_asc"},
        )

        self.assertEqual(response.status_code, 200)

    def test_catalog_invalid_price_range(self):
        response = self.client.get(
            reverse("store:catalog"),
            {"min_price": "100", "max_price": "10"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a valid price range.")

    def test_game_detail_page(self):
        response = self.client.get(
            reverse(
                "store:game_detail",
                kwargs={"slug": self.published_game.slug},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nightfall")
        self.assertContains(response, "Intel Core i5")
        self.assertContains(response, "Excellent game.")

    def test_unpublished_game_is_not_public(self):
        response = self.client.get(
            reverse(
                "store:game_detail",
                kwargs={"slug": self.unpublished_game.slug},
            )
        )

        self.assertEqual(response.status_code, 404)
