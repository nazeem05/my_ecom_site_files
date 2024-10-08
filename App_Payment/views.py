from django.shortcuts import render, HttpResponseRedirect, redirect
from django.urls import reverse
from django.contrib import messages
#Models and Forms
from App_Order.models import Order
from App_Payment.forms import BillingAddress
from App_Payment.forms import BillingForm

from django.contrib.auth.decorators import login_required
#for payment
from sslcommerz_python.payment import SSLCSession
from decimal import Decimal
import socket

# Create your views here.

@login_required
def checkout(request):
    saved_address = BillingAddress.objects.get_or_create(user=request.user)
    saved_address = saved_address[0]
    form = BillingForm(instance=saved_address)
    if request.method == "POST":
        form = BillingForm(request.POST, instance=saved_address)
        if form.is_valid():
            form.save()
            form = BillingForm(instance=saved_address)
            messages.success(request, f"Shipping Address Saved.")
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    order_items = order_qs[0].orderitems.all()
    order_total = order_qs[0].get_totals()
    return render(request, 'App_Payment/checkout.html', context={"form":form, "order_items":order_items, "order_total":order_total, "saved_address":saved_address})


@login_required
def payment(request):
    saved_address = BillingAddress.objects.get_or_create(user=request.user)
    saved_address = saved_address[0]
    if not saved_address.is_fully_filled():
        messages.info(request, f"Please complete shipping address!")
        return redirect("App_Payment:checkout")

    if not request.user.profile.is_fully_filled():
        messages.info(request, f"Please complete profile details!")
        return redirect("App_Login:profile")
    my_store_id = 'xyz62584ab45b176'
    my_store_pass = 'xyz62584ab45b176@ssl'
    mypayment = SSLCSession(sslc_is_sandbox=True, sslc_store_id = my_store_id, sslc_store_pass = my_store_pass)

    status_url = request.build_absolute_uri(reverse("App_Payment:complete"))

    mypayment.set_urls(success_url = status_url, fail_url = status_url, cancel_url = status_url, ipn_url = status_url)

    order_qs = Order.objects.filter(user=request.user, ordered=False)
    order_items = order_qs[0].orderitems.all()
    order_items_count = order_qs[0].orderitems.count()
    order_total = order_qs[0].get_totals()

    mypayment.set_product_integration(total_amount = Decimal(order_total), currency='BDT', product_category='Mixed', product_name = order_items, num_of_item = order_items_count, shipping_method='Courier', product_profile='None')

    current_user = request.user

    mypayment.set_customer_info(name=current_user.profile.full_name, email=current_user.email, address1=current_user.profile.address_1, address2=current_user.profile.address_1, city=current_user.profile.city, postcode=current_user.profile.zipcode, country=current_user.profile.country, phone=current_user.profile.phone)

    mypayment.set_shipping_info(shipping_to=current_user.profile.full_name, address = saved_address.address, city = saved_address.city, postcode = saved_address.zipcode, country = saved_address.country)

    # If you want to post some additional values
    #mypayment.set_additional_values(value_a='cusotmer@email.com', value_b='portalcustomerid', value_c='1234', value_d='uuid')
   
    response_data = mypayment.init_payment()

    print(response_data)

    return redirect(response_data['GatewayPageURL'])


@login_required
def complete(request):
    render(request, "App_Payment/complete.html", context={})