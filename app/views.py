from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Count

from app.models import Movie, Seat, Ticket


def list_movies(request):
    return render(request, 'app/movies.html', {
        'movies': Movie.objects.all()
    })


def list_seats(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    # فقط صندلی‌هایی که برای این فیلم رزرو نشده‌اند
    reserved_seats = Ticket.objects.filter(movie=movie).values_list('seat_id', flat=True)
    seats = Seat.objects.exclude(id__in=reserved_seats)
    return render(request, 'app/seats.html', {
        'movie': movie,
        'seats': seats
    })


def reserve_seat(request, movie_id, seat_id):
    if not request.user.is_authenticated:
        return redirect(f'/login/?next=/movie/{movie_id}/seats/')
    movie = get_object_or_404(Movie, id=movie_id)
    seat = get_object_or_404(Seat, id=seat_id)
    # چک کن قبلاً رزرو نشده باشد
    already_reserved = Ticket.objects.filter(movie=movie, seat=seat).exists()
    if already_reserved:
        # اگر رزرو شده بود، پیام بده
        return render(request, 'app/seats.html', {
            'movie': movie,
            'seats': Seat.objects.exclude(id__in=Ticket.objects.filter(movie=movie).values_list('seat_id', flat=True)),
            'is_reserved': True  # این متغیر را به قالب می‌فرستیم
        })
    # اگر رزرو نشده بود، رزرو کن
    Ticket.objects.create(movie=movie, seat=seat, user=request.user)
    # بعد از رزرو، پیام موفقیت بفرست
    return render(request, 'app/seats.html', {
        'movie': movie,
        'seats': Seat.objects.exclude(id__in=Ticket.objects.filter(movie=movie).values_list('seat_id', flat=True)),
        'is_reserved': False  # یعنی رزرو موفق بود
    })


def stats(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    data = Ticket.objects.values('seat__number').annotate(total=Count('id')).order_by('seat__number')
    return JsonResponse({'stats': list(data)})


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})
