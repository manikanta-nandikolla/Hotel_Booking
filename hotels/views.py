from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
import razorpay
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .forms import BookingForm
from .utils import is_hotel_admin

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_SECRET_KEY))


# Home Page
def home(request):
    hotels = Hotel.objects.all()[:3]  # Show only 3 hotels on the home page
    return render(request, 'home.html', {'hotels': hotels})


# List all hotels
@login_required(login_url='login')
def hotel_list(request):
    hotels = Hotel.objects.all()
    return render(request, 'hotels/hotel_list.html', {'hotels': hotels})


# Show hotel details with available rooms
@login_required(login_url='login')
def hotel_detail(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    rooms = Room.objects.filter(hotel=hotel, is_available=True)
    return render(request, 'hotels/hotel_detail.html', {'hotel': hotel, 'rooms': rooms})


# Book a Room
@login_required(login_url='login')
def book_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.room = room

            # Check room availability
            existing_bookings = Booking.objects.filter(
                room=room,
                check_in__lt=booking.check_out,
                check_out__gt=booking.check_in
            )

            if existing_bookings.exists():
                messages.error(request, "Room is not available for the selected dates.")
                return redirect('book_room', room_id=room.id)

            booking.save()
            return redirect(reverse('initiate_payment', args=[booking.id]))

    else:
        form = BookingForm()

    return render(request, 'hotels/book_room.html', {'form': form, 'room': room})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('room', 'room__hotel')
    return render(request, 'hotels/my_bookings.html', {'bookings': bookings})


@login_required
def initiate_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.total_price or booking.total_price <= 0:
        messages.error(request, "Invalid booking amount. Please try again.")
        return redirect('my_bookings')

    amount = int(booking.total_price * 100)  # Convert to paise

    razorpay_order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1"
    })

    payment = Payment.objects.create(
        user=request.user,
        booking=booking,
        razorpay_order_id=razorpay_order['id'],
        amount=booking.total_price
    )

    return render(request, "hotels/initiate_payment.html", {
        "razorpay_key": settings.RAZORPAY_API_KEY,
        "razorpay_order_id": razorpay_order['id'],
        "amount": booking.total_price,
        "booking": booking
    })


@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        data = request.POST
        payment_id = data.get("razorpay_payment_id")
        order_id = data.get("razorpay_order_id")
        signature = data.get("razorpay_signature")

        try:
            payment = Payment.objects.get(razorpay_order_id=order_id)
            payment.razorpay_payment_id = payment_id
            payment.razorpay_signature = signature
            payment.paid = True
            payment.save()

            return render(request, "hotels/payment_success.html", {"payment": payment})

        except Payment.DoesNotExist:
            return JsonResponse({"error": "Payment not found!"}, status=400)

    return redirect("home")


@login_required
def hotel_admin_dashboard(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)

    if not is_hotel_admin(request.user, hotel) and not request.user.is_superuser:
        return HttpResponseForbidden("You are not authorized to access this page.")

    return render(request, 'hotels/hotel_admin_dashboard.html', {'hotel': hotel})

