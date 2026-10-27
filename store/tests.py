
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import (
    APIImportLog,
    Cart,
    CartItem,
    Game,
    Genre,
    Order,
    OrderItem,
    Platform,
    Review,
    SystemRequirement,
    Wishlist,
)


User = get_user_model()


class GameHubModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="gamer1",
            email="gamer1@example.com",
            password="TestPassword123!",
        )

        cls.genre = Genre.objects.create(name="Horror")
        cls.platform = Platform.objects.create(name="Windows")

        cls.game = Game.objects.create(
            title="Nightfall",
            price=Decimal("20.00"),
            currency="USD",
            discount_percent=25,
            is_published=True,
        )

        cls.game.genres.add(cls.genre)
        cls.game.platforms.add(cls.platform)

    def test_game_slug_is_generated(self):
        self.assertEqual(self.game.slug, "nightfall")

    def test_game_discounted_price(self):
        self.assertEqual(
            self.game.discounted_price,
            Decimal("15.00"),
        )

    def test_game_relationships(self):
        self.assertIn(self.genre, self.game.genres.all())
        self.assertIn(self.platform, self.game.platforms.all())

    def test_game_external_identity_must_be_unique(self):
        Game.objects.create(
            title="Imported Game A",
            external_source="rawg",
            external_id="12345",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Game.objects.create(
                    title="Imported Game B",
                    external_source="rawg",
                    external_id="12345",
                )

    def test_negative_game_price_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Game.objects.create(
                    title="Invalid Price Game",
                    price=Decimal("-1.00"),
                )

    def test_discount_cannot_exceed_100(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Game.objects.create(
                    title="Invalid Discount Game",
                    discount_percent=101,
                )

    def test_wishlist_item_can_be_created(self):
        item = Wishlist.objects.create(
            user=self.user,
            game=self.game,
        )

        self.assertEqual(item.game, self.game)
        self.assertEqual(item.user, self.user)

    def test_duplicate_wishlist_is_rejected(self):
        Wishlist.objects.create(
            user=self.user,
            game=self.game,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Wishlist.objects.create(
                    user=self.user,
                    game=self.game,
                )

    def test_duplicate_review_is_rejected(self):
        Review.objects.create(
            user=self.user,
            game=self.game,
            rating=5,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    user=self.user,
                    game=self.game,
                    rating=4,
                )

    def test_review_rating_database_constraint(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    user=self.user,
                    game=self.game,
                    rating=6,
                )

    def test_system_requirement_is_unique_per_game_platform_type(self):
        SystemRequirement.objects.create(
            game=self.game,
            platform=self.platform,
            requirement_type=SystemRequirement.RequirementType.MINIMUM,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SystemRequirement.objects.create(
                    game=self.game,
                    platform=self.platform,
                    requirement_type=SystemRequirement.RequirementType.MINIMUM,
                )

    def test_cart_cannot_contain_duplicate_game_rows(self):
        cart = Cart.objects.create(user=self.user)

        CartItem.objects.create(
            cart=cart,
            game=self.game,
            quantity=1,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CartItem.objects.create(
                    cart=cart,
                    game=self.game,
                    quantity=2,
                )

    def test_order_item_preserves_purchase_price(self):
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal("20.00"),
            currency="USD",
        )

        item = OrderItem.objects.create(
            order=order,
            game=self.game,
            title_snapshot=self.game.title,
            unit_price=Decimal("20.00"),
            quantity=1,
        )

        self.game.price = Decimal("30.00")
        self.game.save()

        item.refresh_from_db()

        self.assertEqual(item.unit_price, Decimal("20.00"))
        self.assertEqual(item.title_snapshot, "Nightfall")
        self.assertEqual(item.line_total, Decimal("20.00"))

    def test_real_payment_order_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Order.objects.create(
                    user=self.user,
                    is_demo=False,
                )

    def test_api_import_log_stores_json(self):
        log = APIImportLog.objects.create(
            source="rawg",
            external_id="9876",
            status=APIImportLog.Status.SUCCESS,
            raw_payload={"name": "Example Game", "id": 9876},
        )

        log.refresh_from_db()

        self.assertEqual(
            log.raw_payload["name"],
            "Example Game",
        )
        self.assertEqual(log.game, None)
