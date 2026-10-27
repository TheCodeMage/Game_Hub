
from django.contrib import admin

from .models import (
    APIImportLog,
    Cart,
    CartItem,
    Game,
    GameScreenshot,
    Genre,
    Order,
    OrderItem,
    Platform,
    Review,
    SystemRequirement,
    Wishlist,
)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "price",
        "currency",
        "discount_percent",
        "is_published",
        "is_featured",
    )
    list_filter = ("is_published", "is_featured", "genres", "platforms")
    search_fields = ("title", "developer", "publisher", "external_id")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("genres", "platforms")
    list_per_page = 25


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name",)
    prepopulated_fields = {"code": ("name",)}


@admin.register(GameScreenshot)
class GameScreenshotAdmin(admin.ModelAdmin):
    list_display = ("game", "caption", "sort_order")
    search_fields = ("game__title", "caption")


@admin.register(SystemRequirement)
class SystemRequirementAdmin(admin.ModelAdmin):
    list_display = ("game", "platform", "requirement_type")
    list_filter = ("platform", "requirement_type")
    search_fields = ("game__title",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("game", "user", "rating", "is_published", "created_at")
    list_filter = ("rating", "is_published")
    search_fields = ("game__title", "user__username", "comment")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "game", "created_at")
    search_fields = ("user__username", "game__title")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("title_snapshot", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "total_amount",
        "currency",
        "is_demo",
        "created_at",
    )
    list_filter = ("status", "is_demo", "currency")
    search_fields = ("order_number", "user__username")
    readonly_fields = ("order_number", "completed_at")
    inlines = [OrderItemInline]


@admin.register(APIImportLog)
class APIImportLogAdmin(admin.ModelAdmin):
    list_display = ("source", "external_id", "game", "status", "created_at")
    list_filter = ("source", "status")
    search_fields = ("source", "external_id", "message")
    readonly_fields = ("raw_payload", "created_at", "updated_at")
