
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render

from .models import Game, Genre, Platform


def home(request):
    published_games = (
        Game.objects.filter(is_published=True)
        .prefetch_related("genres", "platforms")
    )

    featured_games = published_games.filter(
        is_featured=True
    )[:6]

    latest_games = (
        published_games.filter(release_date__isnull=False)
        .order_by("-release_date", "-id")[:8]
    )

    genres = Genre.objects.filter(
        games__is_published=True
    ).distinct()[:8]

    context = {
        "featured_games": featured_games,
        "latest_games": latest_games,
        "genres": genres,
    }

    return render(request, "store/home.html", context)


def catalog(request):
    games = (
        Game.objects.filter(is_published=True)
        .prefetch_related("genres", "platforms")
        .annotate(
            average_rating=Avg(
                "reviews__rating",
                filter=Q(reviews__is_published=True),
            ),
            review_count=Count(
                "reviews",
                filter=Q(reviews__is_published=True),
                distinct=True,
            ),
        )
    )

    search_query = request.GET.get("q", "").strip()
    genre_slug = request.GET.get("genre", "").strip()
    platform_code = request.GET.get("platform", "").strip()
    min_price_value = request.GET.get("min_price", "").strip()
    max_price_value = request.GET.get("max_price", "").strip()
    sort = request.GET.get("sort", "title")

    if search_query:
        games = games.filter(
            Q(title__icontains=search_query)
            | Q(developer__icontains=search_query)
            | Q(publisher__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    if genre_slug:
        games = games.filter(genres__slug=genre_slug)

    if platform_code:
        games = games.filter(platforms__code=platform_code)

    price_error = ""

    try:
        if min_price_value:
            min_price = Decimal(min_price_value)
            if not min_price.is_finite() or min_price < 0:
                raise ValueError
            games = games.filter(price__gte=min_price)

        if max_price_value:
            max_price = Decimal(max_price_value)
            if not max_price.is_finite() or max_price < 0:
                raise ValueError
            games = games.filter(price__lte=max_price)

        if min_price_value and max_price_value:
            if Decimal(min_price_value) > Decimal(max_price_value):
                raise ValueError

    
    except (ValueError, ArithmeticError):
        price_error = "Please enter a valid price range."
        games = games.none()


    sort_options = {
        "title": "title",
        "price_asc": "price",
        "price_desc": "-price",
        "newest": "-release_date",
        "rating": "-average_rating",
    }

    if sort not in sort_options:
        sort = "title"

    games = games.order_by(sort_options[sort], "title")

    paginator = Paginator(games, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    query_params.pop("page", None)

    context = {
        "page_obj": page_obj,
        "games": page_obj.object_list,
        "genres": Genre.objects.filter(
            games__is_published=True
        ).distinct(),
        "platforms": Platform.objects.filter(
            games__is_published=True
        ).distinct(),
        "search_query": search_query,
        "selected_genre": genre_slug,
        "selected_platform": platform_code,
        "min_price": min_price_value,
        "max_price": max_price_value,
        "sort": sort,
        "price_error": price_error,
        "querystring": query_params.urlencode(),
    }

    return render(request, "store/catalog.html", context)


def game_detail(request, slug):
    game = get_object_or_404(
        Game.objects.filter(is_published=True)
        .prefetch_related(
            "genres",
            "platforms",
            "screenshots",
            "system_requirements__platform",
        )
        .annotate(
            average_rating=Avg(
                "reviews__rating",
                filter=Q(reviews__is_published=True),
            ),
            review_count=Count(
                "reviews",
                filter=Q(reviews__is_published=True),
                distinct=True,
            ),
        ),
        slug=slug,
    )

    reviews = (
        game.reviews.filter(is_published=True)
        .select_related("user")
        .order_by("-created_at")[:10]
    )

    context = {
        "game": game,
        "reviews": reviews,
    }

    return render(request, "store/game_detail.html", context)
