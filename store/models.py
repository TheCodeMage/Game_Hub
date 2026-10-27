
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    """Reusable created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Genre(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Platform(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    code = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Game(TimeStampedModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)

    developer = models.CharField(max_length=150, blank=True)
    publisher = models.CharField(max_length=150, blank=True)
    release_date = models.DateField(null=True, blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="USD")
    discount_percent = models.PositiveSmallIntegerField(default=0)

    cover_image_url = models.URLField(max_length=500, blank=True)
    trailer_url = models.URLField(max_length=500, blank=True)

    genres = models.ManyToManyField(
        Genre,
        related_name="games",
        blank=True,
    )
    platforms = models.ManyToManyField(
        Platform,
        related_name="games",
        blank=True,
    )

    external_source = models.CharField(max_length=50, blank=True)
    external_id = models.CharField(max_length=100, blank=True)

    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["title"]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="game_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(discount_percent__lte=100),
                name="game_discount_lte_100",
            ),
            models.UniqueConstraint(
                fields=["external_source", "external_id"],
                condition=~Q(external_id=""),
                name="unique_game_external_identity",
            ),
        ]
        indexes = [
            models.Index(
                fields=["is_published", "title"],
                name="game_published_title_idx",
            ),
            models.Index(
                fields=["release_date"],
                name="game_release_date_idx",
            ),
        ]

    @property
    def discounted_price(self):
        discount = self.discount_percent
        return (
            self.price
            * (100 - discount)
            / 100
        ).quantize(self.price.__class__("0.01"))

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "game"
            candidate = base_slug
            suffix = 2

            while Game.objects.filter(slug=candidate).exclude(
                pk=self.pk
            ).exists():
                candidate = f"{base_slug}-{suffix}"
                suffix += 1

            self.slug = candidate

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class GameScreenshot(TimeStampedModel):
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="screenshots",
    )
    image_url = models.URLField(max_length=500)
    caption = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"Screenshot for {self.game.title}"


class SystemRequirement(TimeStampedModel):
    class RequirementType(models.TextChoices):
        MINIMUM = "minimum", "Minimum"
        RECOMMENDED = "recommended", "Recommended"

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="system_requirements",
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.PROTECT,
        related_name="system_requirements",
    )
    requirement_type = models.CharField(
        max_length=12,
        choices=RequirementType.choices,
    )

    os_version = models.CharField(max_length=200, blank=True)
    processor = models.CharField(max_length=200, blank=True)
    memory = models.CharField(max_length=100, blank=True)
    graphics = models.CharField(max_length=200, blank=True)
    directx = models.CharField(max_length=100, blank=True)
    storage = models.CharField(max_length=100, blank=True)
    additional_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["game", "platform", "requirement_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["game", "platform", "requirement_type"],
                name="unique_game_platform_requirement",
            ),
        ]

    def __str__(self):
        return (
            f"{self.game.title} - {self.platform.name} - "
            f"{self.get_requirement_type_display()}"
        )


class Review(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_reviews",
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "game"],
                name="unique_review_per_user_game",
            ),
            models.CheckConstraint(
                condition=Q(rating__gte=1) & Q(rating__lte=5),
                name="review_rating_1_to_5",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.game.title} ({self.rating}/5)"


class Wishlist(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlists",
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "game"],
                name="unique_wishlist_user_game",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.game.title}"


class Cart(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )

    def __str__(self):
        return f"Cart for {self.user}"


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "game"],
                name="unique_cart_game",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=1),
                name="cart_item_quantity_gte_1",
            ),
        ]

    def __str__(self):
        return f"{self.game.title} x {self.quantity}"


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        DEMO_PENDING = "demo_pending", "Demo Pending"
        DEMO_COMPLETED = "demo_completed", "Demo Completed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="game_orders",
    )
    order_number = models.UUIDField(
        default=None,
        unique=True,
        editable=False,
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DEMO_PENDING,
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    currency = models.CharField(max_length=3, default="USD")
    is_demo = models.BooleanField(default=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(total_amount__gte=0),
                name="order_total_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(is_demo=True),
                name="gamehub_orders_must_be_demo",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.order_number is None:
            import uuid
            self.order_number = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.order_number)


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )

    # Preserve purchase-time details even if the Game changes or is deleted.
    title_snapshot = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="order_item_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=1),
                name="order_item_quantity_gte_1",
            ),
        ]

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.title_snapshot} x {self.quantity}"


class APIImportLog(TimeStampedModel):
    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    source = models.CharField(max_length=50)
    external_id = models.CharField(max_length=100, blank=True)
    game = models.ForeignKey(
        Game,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_logs",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SUCCESS,
    )
    message = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["source", "external_id"],
                name="api_source_external_idx",
            ),
        ]

    def __str__(self):
        return f"{self.source}: {self.external_id} ({self.status})"
